from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    PROJECT_NAME: str = "火山引擎TTS API服务"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3010",
        "http://192.168.50.213:3010",
        "https://your-frontend-domain.com"
    ]
    
    # 数据库配置
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # 缓存配置
    CACHE_ENABLED: bool = False  # 临时禁用缓存
    CACHE_TTL: int = 3600  # 缓存过期时间（秒）
    CACHE_MAX_SIZE: int = 1000  # 最大缓存条目数
    CACHE_EXPIRE_SECONDS: int = 3600  # 兼容性保留
    
    # JWT认证配置
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"  # 兼容性保留
    JWT_ALGORITHM: str = "HS256"  # 兼容性保留
    
    # 用户认证配置
    AUTH_ENABLED: bool = False  # 是否启用认证（默认关闭）
    ALLOW_ANONYMOUS: bool = True  # 是否允许匿名用户
    DEFAULT_USER_QUOTA: int = 1000  # 默认用户每日配额
    REQUIRE_EMAIL_VERIFICATION: bool = False  # 是否需要邮箱验证
    
    # API密钥配置
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "tts"
    
    # 火山引擎配置
    VOLCANO_APP_ID: str = ""
    VOLCANO_ACCESS_TOKEN: str = ""
    VOLCANO_CLUSTER: str = "volcano_tts"
    VOLCANO_HOST: str = "openspeech.bytedance.com"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 从 tts_config.json 加载火山引擎配置
        self._load_volcano_config()
    
    def _load_volcano_config(self):
        """从 tts_config.json 加载火山引擎配置"""
        import json
        try:
            # 查找 config 文件
            config_paths = [
                "./tts_config.json",
                "../tts_config.json",
                "../../tts_config.json",
                "tts_config.json"
            ]
            
            config_data = None
            for path in config_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    print(f"✅ 从 {path} 加载火山引擎配置")
                    break
                except FileNotFoundError:
                    continue
            
            if config_data:
                self.VOLCANO_APP_ID = config_data.get("appid", "")
                self.VOLCANO_ACCESS_TOKEN = config_data.get("token", "")
                self.VOLCANO_CLUSTER = config_data.get("cluster", "volcano_tts")
                print(f"🔧 火山引擎配置已加载: APP_ID={self.VOLCANO_APP_ID[:8]}...")
            else:
                print("⚠️ 未找到 tts_config.json 文件，使用环境变量配置")
                
        except Exception as e:
            print(f"❌ 加载火山引擎配置失败: {e}")
            print("📝 请确保 tts_config.json 文件格式正确")
    
    # 文件存储配置
    AUDIO_FILES_PATH: str = "./audio_files"
    TEMP_FILES_PATH: str = "./temp_files"
    MAX_FILE_SIZE_MB: int = 100
    AUDIO_FILE_EXPIRE_HOURS: int = 24
    
    # 速率限制配置
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1小时
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # TTS服务配置
    MAX_TEXT_LENGTH: int = 1000
    DEFAULT_VOICE_ID: str = "zh_female_shuangkuaisisi_emo_v2_mars_bigtts"
    MAX_CONCURRENT_SYNTHESIS: int = 10
    SYNTHESIS_TIMEOUT: int = 30
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.AUDIO_FILES_PATH, exist_ok=True)
os.makedirs(settings.TEMP_FILES_PATH, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)