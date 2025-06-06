from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import logging
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api.v1.api import api_router


# 设置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 TTS API服务启动中...")
    
    # 启动时的初始化操作
    try:
        # 初始化数据库
        from app.core.database import db_manager
        await db_manager.initialize()
        
        # 初始化缓存服务
        from app.services.cache_service import cache_service
        await cache_service.initialize()
        
        logger.info("✅ 服务初始化完成")
        yield
    finally:
        # 关闭时的清理操作
        from app.services.cache_service import cache_service
        from app.core.database import db_manager
        
        await cache_service.close()
        await db_manager.close()
        logger.info("👋 TTS API服务关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="基于火山引擎的高质量语音合成服务API",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 临时允许所有来源以解决跨域问题
    allow_credentials=False,  # 当使用 "*" 时必须设置为 False
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/audio", StaticFiles(directory=settings.AUDIO_FILES_PATH), name="audio")

# 创建预览文件夹（如果不存在）
previews_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "audio_files", "previews")
os.makedirs(previews_dir, exist_ok=True)

# 挂载静态文件（预览音频）
app.mount("/previews", StaticFiles(directory=previews_dir), name="previews")

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "内部服务器错误",
            "message": str(exc) if settings.DEBUG else "服务暂时不可用，请稍后重试"
        }
    )

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 根路径
@app.get("/")
async def root():
    return {
        "message": "火山引擎TTS API服务",
        "version": settings.VERSION,
        "docs": "/docs",
        "status": "running"
    }

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "service": "tts-api"
    }

# 详细健康检查
@app.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查，包含各个组件状态"""
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "components": {
            "api": "healthy",
            "config": "healthy" if settings.VOLCANO_APP_ID else "warning"
        }
    }
    
    # 检查必要配置
    if not settings.VOLCANO_APP_ID or not settings.VOLCANO_ACCESS_TOKEN:
        status["status"] = "warning"
        status["components"]["volcano_config"] = "missing"
    
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.DEBUG else settings.WORKERS
    )