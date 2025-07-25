"""
内存缓存模块 - 提供基于内存的缓存功能
当Redis不可用时作为备选方案
"""
import time
import logging
import threading
from typing import Any, Dict, List, Optional, Union, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, prefix: str = "novelforge:"):
        """
        初始化内存缓存
        
        参数:
            prefix: 键前缀，用于隔离不同应用的缓存
        """
        self.prefix = prefix
        self.cache = {}  # 存储缓存数据
        self.expiry = {}  # 存储过期时间
        self.lock = threading.RLock()  # 线程锁，确保线程安全
        
        # 启动清理过期缓存的线程
        self._start_cleanup_thread()
    
    def _get_key(self, key: str) -> str:
        """
        获取带前缀的键名
        
        参数:
            key: 原始键名
        
        返回:
            带前缀的键名
        """
        return f"{self.prefix}{key}"
    
    def _start_cleanup_thread(self):
        """启动清理过期缓存的线程"""
        def cleanup_expired():
            while True:
                self._cleanup_expired()
                time.sleep(60)  # 每分钟清理一次
        
        thread = threading.Thread(target=cleanup_expired, daemon=True)
        thread.start()
    
    def _cleanup_expired(self):
        """清理过期的缓存"""
        now = time.time()
        expired_keys = []
        
        with self.lock:
            for key, expire_time in self.expiry.items():
                if expire_time <= now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.cache.pop(key, None)
                self.expiry.pop(key, None)
        
        if expired_keys:
            logger.debug(f"已清理 {len(expired_keys)} 个过期缓存")
    
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
        full_key = self._get_key(key)
        
        with self.lock:
            self.cache[full_key] = value
            
            if expire:
                self.expiry[full_key] = time.time() + expire
            elif full_key in self.expiry:
                # 如果之前设置了过期时间，现在不设置，则删除过期设置
                self.expiry.pop(full_key, None)
        
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存
        
        参数:
            key: 键名
            default: 默认值（如果键不存在）
        
        返回:
            缓存值或默认值
        """
        full_key = self._get_key(key)
        
        with self.lock:
            # 检查是否过期
            if full_key in self.expiry and time.time() > self.expiry[full_key]:
                self.cache.pop(full_key, None)
                self.expiry.pop(full_key, None)
                return default
            
            return self.cache.get(full_key, default)
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        参数:
            key: 键名
        
        返回:
            是否成功
        """
        full_key = self._get_key(key)
        
        with self.lock:
            if full_key in self.cache:
                self.cache.pop(full_key, None)
                self.expiry.pop(full_key, None)
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        参数:
            key: 键名
        
        返回:
            是否存在
        """
        full_key = self._get_key(key)
        
        with self.lock:
            # 检查是否过期
            if full_key in self.expiry and time.time() > self.expiry[full_key]:
                self.cache.pop(full_key, None)
                self.expiry.pop(full_key, None)
                return False
            
            return full_key in self.cache
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间
        
        参数:
            key: 键名
            seconds: 过期时间（秒）
        
        返回:
            是否成功
        """
        full_key = self._get_key(key)
        
        with self.lock:
            if full_key in self.cache:
                self.expiry[full_key] = time.time() + seconds
                return True
            return False
    
    def clear(self, pattern: str = "*") -> int:
        """
        清除匹配的缓存
        
        参数:
            pattern: 匹配模式（支持*通配符）
        
        返回:
            清除的键数量
        """
        import fnmatch
        
        full_pattern = self._get_key(pattern)
        count = 0
        
        with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if fnmatch.fnmatch(k, full_pattern)]
            
            for key in keys_to_delete:
                self.cache.pop(key, None)
                self.expiry.pop(key, None)
                count += 1
        
        return count
    
    def incr(self, key: str, amount: int = 1) -> int:
        """
        增加计数器
        
        参数:
            key: 键名
            amount: 增加量
        
        返回:
            新值
        """
        full_key = self._get_key(key)
        
        with self.lock:
            # 检查是否过期
            if full_key in self.expiry and time.time() > self.expiry[full_key]:
                self.cache.pop(full_key, None)
                self.expiry.pop(full_key, None)
                self.cache[full_key] = amount
                return amount
            
            # 如果键不存在或不是数字，初始化为0
            if full_key not in self.cache or not isinstance(self.cache[full_key], (int, float)):
                self.cache[full_key] = 0
            
            self.cache[full_key] += amount
            return self.cache[full_key]
    
    def health_check(self) -> bool:
        """
        检查缓存状态
        
        返回:
            总是返回True，因为内存缓存总是可用
        """
        return True


# 创建默认内存缓存实例
memory_cache = MemoryCache()
