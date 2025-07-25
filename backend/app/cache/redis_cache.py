"""
Redis缓存模块 - 提供基于Redis的缓存功能
"""
import json
import time
from typing import Dict, Any, Optional, Union, List

import redis

from ..config import settings
from ..utils.logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 尝试导入Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis库未安装，将使用内存缓存代替")
    REDIS_AVAILABLE = False


class RedisCache:
    """Redis缓存实现"""
    
    def __init__(self, host: str = None, port: int = None, 
                password: str = None, db: int = 0, prefix: str = "novelforge:"):
        """
        初始化Redis缓存
        
        参数:
            host: Redis主机地址，默认从环境变量REDIS_HOST获取
            port: Redis端口，默认从环境变量REDIS_PORT获取
            password: Redis密码，默认从环境变量REDIS_PASSWORD获取
            db: Redis数据库索引
            prefix: 键前缀，用于隔离不同应用的缓存
        """
        self.prefix = prefix
        self.client = None
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis库未安装，缓存将不可用")
            return
        
        # 使用统一配置
        self.host = host or settings.redis_host
        self.port = port or settings.redis_port
        self.password = password or settings.redis_password
        self.db = db if db is not None else settings.redis_db
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=False,  # 不自动解码，使用pickle处理复杂对象
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # 测试连接
            self.client.ping()
            logger.info(f"Redis缓存已连接: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            self.client = None
    
    def _get_key(self, key: str) -> str:
        """
        获取带前缀的键名
        
        参数:
            key: 原始键名
        
        返回:
            带前缀的键名
        """
        return f"{self.prefix}{key}"
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存
        
        参数:
            key: 键名
            value: 值（支持任何可序列化的对象）
            expire: 过期时间（秒）
        
        返回:
            是否成功
        """
        if not self.client:
            return False
        
        try:
            # 使用pickle序列化，支持复杂对象
            serialized = pickle.dumps(value)
            full_key = self._get_key(key)
            
            if expire:
                result = self.client.setex(full_key, expire, serialized)
            else:
                result = self.client.set(full_key, serialized)
            
            return bool(result)
        except Exception as e:
            logger.error(f"设置缓存失败 [{key}]: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存
        
        参数:
            key: 键名
            default: 默认值（如果键不存在）
        
        返回:
            缓存值或默认值
        """
        if not self.client:
            return default
        
        try:
            full_key = self._get_key(key)
            value = self.client.get(full_key)
            
            if value is None:
                return default
            
            # 反序列化
            return pickle.loads(value)
        except Exception as e:
            logger.error(f"获取缓存失败 [{key}]: {str(e)}")
            return default
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        参数:
            key: 键名
        
        返回:
            是否成功
        """
        if not self.client:
            return False
        
        try:
            full_key = self._get_key(key)
            return bool(self.client.delete(full_key))
        except Exception as e:
            logger.error(f"删除缓存失败 [{key}]: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        参数:
            key: 键名
        
        返回:
            是否存在
        """
        if not self.client:
            return False
        
        try:
            full_key = self._get_key(key)
            return bool(self.client.exists(full_key))
        except Exception as e:
            logger.error(f"检查缓存存在失败 [{key}]: {str(e)}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间
        
        参数:
            key: 键名
            seconds: 过期时间（秒）
        
        返回:
            是否成功
        """
        if not self.client:
            return False
        
        try:
            full_key = self._get_key(key)
            return bool(self.client.expire(full_key, seconds))
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 [{key}]: {str(e)}")
            return False
    
    def clear(self, pattern: str = "*") -> int:
        """
        清除匹配的缓存
        
        参数:
            pattern: 匹配模式
        
        返回:
            清除的键数量
        """
        if not self.client:
            return 0
        
        try:
            full_pattern = self._get_key(pattern)
            keys = self.client.keys(full_pattern)
            
            if not keys:
                return 0
            
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"清除缓存失败 [{pattern}]: {str(e)}")
            return 0
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        增加计数器
        
        参数:
            key: 键名
            amount: 增加量
        
        返回:
            新值或None（失败）
        """
        if not self.client:
            return None
        
        try:
            full_key = self._get_key(key)
            return self.client.incrby(full_key, amount)
        except Exception as e:
            logger.error(f"增加计数器失败 [{key}]: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """
        检查Redis连接状态
        
        返回:
            是否连接正常
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.ping())
        except Exception as e:
            logger.error(f"Redis健康检查失败: {str(e)}")
            return False


# 创建默认Redis缓存实例
redis_cache = RedisCache()
