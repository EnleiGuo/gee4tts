import asyncio
import json
import hashlib
import pickle
from typing import Optional, Any, Dict
import logging
from datetime import datetime, timedelta

# 临时禁用 Redis 以避免兼容性问题
try:
    # import aioredis
    REDIS_AVAILABLE = False  # 强制使用内存缓存
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """统一缓存服务，支持Redis和内存缓存"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
        
    async def initialize(self):
        """初始化缓存服务"""
        if REDIS_AVAILABLE and settings.REDIS_URL:
            try:
                self.redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # 测试连接
                await self.redis_client.ping()
                logger.info("✅ Redis缓存服务连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败，使用内存缓存: {str(e)}")
                self.redis_client = None
        else:
            logger.info("📦 使用内存缓存服务")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if self.redis_client:
                # 使用Redis
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    self.cache_stats["hits"] += 1
                    return json.loads(cached_data)
            else:
                # 使用内存缓存
                cache_item = self.memory_cache.get(key)
                if cache_item and cache_item["expires_at"] > datetime.utcnow():
                    self.cache_stats["hits"] += 1
                    return cache_item["data"]
                elif cache_item:
                    # 过期删除
                    del self.memory_cache[key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"缓存获取失败 {key}: {str(e)}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            if self.redis_client:
                # 使用Redis
                cached_data = json.dumps(value, ensure_ascii=False, default=str)
                if expire:
                    await self.redis_client.setex(key, expire, cached_data)
                else:
                    await self.redis_client.set(key, cached_data)
            else:
                # 使用内存缓存
                expires_at = datetime.utcnow() + timedelta(
                    seconds=expire or settings.CACHE_EXPIRE_SECONDS
                )
                self.memory_cache[key] = {
                    "data": value,
                    "expires_at": expires_at
                }
                
                # 清理过期缓存
                await self._cleanup_expired_memory_cache()
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            
            self.cache_stats["deletes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {str(e)}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """按模式删除缓存"""
        try:
            deleted_count = 0
            
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count = await self.redis_client.delete(*keys)
            else:
                # 内存缓存模式匹配
                import fnmatch
                keys_to_delete = [
                    key for key in self.memory_cache.keys() 
                    if fnmatch.fnmatch(key, pattern)
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                deleted_count = len(keys_to_delete)
            
            logger.info(f"清理缓存模式 {pattern}: 删除{deleted_count}项")
            return deleted_count
            
        except Exception as e:
            logger.error(f"缓存模式清理失败 {pattern}: {str(e)}")
            return 0
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        # 创建稳定的键值
        key_parts = [str(prefix)]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = self.cache_stats.copy()
        
        if self.redis_client:
            try:
                info = await self.redis_client.info("memory")
                stats.update({
                    "type": "redis",
                    "redis_memory_used": info.get("used_memory_human", "unknown"),
                    "redis_keys": await self.redis_client.dbsize()
                })
            except:
                stats["type"] = "redis_error"
        else:
            stats.update({
                "type": "memory",
                "memory_keys": len(self.memory_cache),
                "memory_usage_mb": self._get_memory_cache_size()
            })
        
        # 计算命中率
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_rate"] = (
            stats["hits"] / total_requests if total_requests > 0 else 0
        )
        
        return stats
    
    async def _cleanup_expired_memory_cache(self):
        """清理过期的内存缓存"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if item["expires_at"] <= now
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        if expired_keys:
            logger.debug(f"清理过期缓存: {len(expired_keys)}项")
    
    def _get_memory_cache_size(self) -> float:
        """估算内存缓存大小(MB)"""
        try:
            size_bytes = len(pickle.dumps(self.memory_cache))
            return round(size_bytes / 1024 / 1024, 2)
        except:
            return 0.0
    
    async def close(self):
        """关闭缓存连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔌 Redis连接已关闭")


# 全局缓存实例
cache_service = CacheService()