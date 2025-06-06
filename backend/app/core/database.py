from sqlalchemy import create_engine, MetaData, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from typing import Generator, Optional
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

# 数据库基类
Base = declarative_base()

# 数据库引擎和会话
engine = None
SessionLocal = None


def get_database_url() -> str:
    """获取数据库连接URL"""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # 如果没有配置PostgreSQL，使用SQLite
    sqlite_path = os.path.join(os.getcwd(), "tts_database.db")
    return f"sqlite:///{sqlite_path}"


def create_database_engine():
    """创建数据库引擎"""
    global engine
    
    database_url = get_database_url()
    logger.info(f"数据库连接: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    if database_url.startswith("postgresql"):
        # PostgreSQL配置
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.DEBUG,
            connect_args={
                "options": "-c timezone=UTC"
            }
        )
        logger.info("使用PostgreSQL数据库")
        
    elif database_url.startswith("sqlite"):
        # SQLite配置
        engine = create_engine(
            database_url,
            echo=settings.DEBUG,
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            }
        )
        logger.info("使用SQLite数据库")
        
        # SQLite外键约束支持
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
    
    else:
        raise ValueError(f"不支持的数据库类型: {database_url}")
    
    return engine


def create_session_maker():
    """创建会话工厂"""
    global SessionLocal
    
    if not engine:
        create_database_engine()
    
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入用）"""
    if not SessionLocal:
        create_session_maker()
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """创建所有数据表"""
    try:
        # 导入所有模型
        from app.models.user import User, UserSession, APIKey
        from app.models.tts_history import TTSHistory, UserQuota, SystemStats
        
        # 创建表
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据表创建完成")
        
        # 验证表是否存在
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table_names = metadata.tables.keys()
        
        expected_tables = [
            "users", "user_sessions", "api_keys", 
            "tts_history", "user_quotas", "system_stats"
        ]
        
        for table_name in expected_tables:
            if table_name in table_names:
                logger.info(f"   ✅ 表 {table_name} 已创建")
            else:
                logger.warning(f"   ⚠️ 表 {table_name} 创建失败")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据表创建失败: {str(e)}")
        return False


def check_database_connection() -> bool:
    """检查数据库连接"""
    try:
        if not engine:
            create_database_engine()
        
        with engine.connect() as connection:
            # 执行简单查询
            if engine.dialect.name == "postgresql":
                result = connection.execute(text("SELECT version()"))
            else:
                result = connection.execute(text("SELECT sqlite_version()"))
            
            version = result.fetchone()[0]
            logger.info(f"数据库连接正常，版本: {version}")
            return True
            
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False


async def init_database():
    """初始化数据库"""
    logger.info("🗃️ 初始化数据库...")
    
    try:
        # 创建引擎和会话
        create_database_engine()
        create_session_maker()
        
        # 检查连接
        if not check_database_connection():
            raise Exception("数据库连接失败")
        
        # 创建表
        if not create_tables():
            raise Exception("数据表创建失败")
        
        # 初始化默认数据
        await init_default_data()
        
        logger.info("✅ 数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise


async def init_default_data():
    """初始化默认数据"""
    try:
        from app.models.user import User
        
        db = next(get_db())
        
        # 检查是否已有管理员用户
        admin_user = db.query(User).filter(User.is_superuser == True).first()
        if not admin_user:
            # 创建默认管理员用户
            admin_user = User(
                username="admin",
                email="admin@tts-service.com",
                full_name="系统管理员",
                is_active=True,
                is_verified=True,
                is_superuser=True,
                daily_quota=100000,
                monthly_quota=3000000,
                concurrent_limit=10
            )
            admin_user.set_password("admin123")
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            logger.info(f"✅ 创建默认管理员用户: {admin_user.username}")
        
        # 创建默认演示用户
        demo_user = db.query(User).filter(User.username == "demo").first()
        if not demo_user:
            demo_user = User(
                username="demo",
                email="demo@tts-service.com",
                full_name="演示用户",
                is_active=True,
                is_verified=True,
                is_superuser=False,
                daily_quota=1000,
                monthly_quota=30000,
                concurrent_limit=3
            )
            demo_user.set_password("demo123")
            
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            
            logger.info(f"✅ 创建默认演示用户: {demo_user.username}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"初始化默认数据失败: {str(e)}")


async def close_database():
    """关闭数据库连接"""
    global engine
    
    if engine:
        engine.dispose()
        logger.info("🔌 数据库连接已关闭")


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
    
    async def initialize(self):
        """初始化数据库"""
        await init_database()
        self.engine = engine
        self.session_factory = SessionLocal
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        if not self.session_factory:
            raise RuntimeError("数据库未初始化")
        return self.session_factory()
    
    def check_health(self) -> dict:
        """检查数据库健康状态"""
        try:
            with self.get_session() as db:
                # 执行简单查询测试连接
                if engine.dialect.name == "postgresql":
                    result = db.execute(text("SELECT 1"))
                else:
                    result = db.execute(text("SELECT 1"))
                
                result.fetchone()
                
                return {
                    "status": "healthy",
                    "type": engine.dialect.name,
                    "url": engine.url.render_as_string(hide_password=True)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "type": engine.dialect.name if engine else "unknown"
            }
    
    async def close(self):
        """关闭数据库连接"""
        await close_database()


# 全局数据库管理器实例
db_manager = DatabaseManager()