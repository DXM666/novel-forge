"""
缓存工厂模块 - 提供统一的缓存接口
根据配置自动选择Redis缓存或内存缓存
"""
from typing import Optional, Any, Dict, List, Union

# 导入缓存实现
from . import redis_cache
from . import memory_cache
from ..config import settings
from ..utils.logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 缓存类型
CACHE_TYPE_REDIS = "redis"
CACHE_TYPE_MEMORY = "memory"


class CacheFactory:
    """缓存工厂，提供统一的缓存接口"""
    
    def __init__(self, cache_type: Optional[str] = None):
        """
        初始化缓存工厂
        
        参数:
            cache_type: 缓存类型，可选为 redis 或 memory，如果为None则使用配置设置
        """
        # 优先使用参数中的缓存类型，如果没有指定则使用配置设置
        self.cache_type = cache_type or settings.cache_type.value
        
        # 初始化缓存实例
        if self.cache_type == CACHE_TYPE_REDIS:
            # 检查Redis是否可用
            if redis_cache.health_check():
                self.cache = redis_cache
                logger.info("使用Redis缓存")
            else:
                logger.warning("Redis不可用，降级使用内存缓存")
                self.cache = memory_cache
                self.cache_type = CACHE_TYPE_MEMORY
        else:
            self.cache = memory_cache
            logger.info("使用内存缓存")
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存
        
        参数:
            key: 键名
            value: 值
            expire: 过期时间（秒）
        
        返回:
            是否成功
        """
        return self.cache.set(key, value, expire)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存
        
        参数:
            key: 键名
            default: 默认值（如果键不存在）
        
        返回:
            缓存值或默认值
        """
        return self.cache.get(key, default)
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        参数:
            key: 键名
        
        返回:
            是否成功
        """
        return self.cache.delete(key)
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        参数:
            key: 键名
        
        返回:
            是否存在
        """
        return self.cache.exists(key)
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间
        
        参数:
            key: 键名
            seconds: 过期时间（秒）
        
        返回:
            是否成功
        """
        return self.cache.expire(key, seconds)
    
    def clear(self, pattern: str = "*") -> int:
        """
        清除匹配的缓存
        
        参数:
            pattern: 匹配模式
        
        返回:
            清除的键数量
        """
        return self.cache.clear(pattern)
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        增加计数器
        
        参数:
            key: 键名
            amount: 增加量
        
        返回:
            新值或None（失败）
        """
        return self.cache.incr(key, amount)
    
    def health_check(self) -> bool:
        """
        检查缓存状态
        
        返回:
            是否可用
        """
        return self.cache.health_check()
    
    def get_type(self) -> str:
        """
        获取当前使用的缓存类型
        
        返回:
            缓存类型
        """
        return self.cache_type


# 创建默认缓存实例
cache = CacheFactory()
