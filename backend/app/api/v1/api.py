from fastapi import APIRouter

from app.api.v1.endpoints import tts, voices, system, auth, users

api_router = APIRouter()

# 用户认证相关接口
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["用户认证"],
)

# TTS语音合成相关接口
api_router.include_router(
    tts.router,
    prefix="/tts",
    tags=["语音合成"],
)

# 音色管理相关接口
api_router.include_router(
    voices.router,
    prefix="/voices",
    tags=["音色管理"],
)

# 用户管理相关接口
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["用户管理"],
)

# 系统管理相关接口
api_router.include_router(
    system.router,
    prefix="/system",
    tags=["系统管理"],
)

# 系统管理接口
@api_router.get("/info", tags=["系统信息"])
async def get_api_info():
    """获取API信息"""
    return {
        "name": "火山引擎TTS API服务",
        "version": "1.0.0",
        "description": "基于火山引擎的高质量语音合成服务，支持131个音色，7个分类",
        "voice_library": {
            "total_voices": 131,
            "categories": 7,
            "emotion_voices": 5,
            "languages": ["中文", "英语", "日语", "西班牙语"],
            "source": "voice_presets_complete.json"
        },
        "endpoints": {
            "tts": {
                "synthesize": "POST /api/v1/tts/synthesize - 同步语音合成",
                "stream": "POST /api/v1/tts/synthesize/stream - 流式语音合成",
                "batch": "POST /api/v1/tts/batch - 批量语音合成",
                "download": "GET /api/v1/tts/download/{filename} - 下载音频文件",
                "status": "GET /api/v1/tts/status/{request_id} - 查询合成状态",
                "test": "GET /api/v1/tts/test-connection - 测试连接"
            },
            "voices": {
                "list": "GET /api/v1/voices/ - 获取音色列表",
                "detail": "GET /api/v1/voices/{voice_id} - 获取音色详情",
                "categories": "GET /api/v1/voices/categories/list - 获取音色分类",
                "emotions": "GET /api/v1/voices/emotions/list - 获取情感列表",
                "languages": "GET /api/v1/voices/languages/list - 获取语言列表",
                "popular": "GET /api/v1/voices/popular/list - 获取热门音色",
                "statistics": "GET /api/v1/voices/statistics - 获取音色库统计信息"
            }
        },
        "features": [
            "131个高质量音色",
            "多情感表达支持",
            "多语言支持(中英日西)",
            "7大音色分类",
            "流式语音合成",
            "批量处理",
            "实时状态查询",
            "完整的API文档"
        ]
    }