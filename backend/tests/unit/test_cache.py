"""
缓存模块单元测试
"""
import pytest
import time
from unittest.mock import patch, MagicMock

# 导入待测试模块
from app.cache.memory_cache import MemoryCache
from app.cache.cache_factory import CacheFactory, CACHE_TYPE_MEMORY, CACHE_TYPE_REDIS

# 测试内存缓存
class TestMemoryCache:
    """内存缓存测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.cache = MemoryCache(prefix="test:")
    
    def teardown_method(self):
        """每个测试方法后执行"""
        # 清理缓存
        self.cache.clear()
    
    def test_set_get(self):
        """测试设置和获取"""
        # 设置缓存
        self.cache.set("key1", "value1")
        self.cache.set("key2", {"name": "测试"})
        self.cache.set("key3", [1, 2, 3])
        
        # 获取缓存
        assert self.cache.get("key1") == "value1"
        assert self.cache.get("key2") == {"name": "测试"}
        assert self.cache.get("key3") == [1, 2, 3]
        assert self.cache.get("not_exist") is None
        assert self.cache.get("not_exist", "默认值") == "默认值"
    
    def test_expire(self):
        """测试过期"""
        # 设置带过期时间的缓存
        self.cache.set("expire_key", "会过期的值", expire=1)
        
        # 立即获取应该存在
        assert self.cache.get("expire_key") == "会过期的值"
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后获取应该为None
        assert self.cache.get("expire_key") is None
    
    def test_delete(self):
        """测试删除"""
        # 设置缓存
        self.cache.set("delete_key", "要删除的值")
        
        # 确认存在
        assert self.cache.get("delete_key") == "要删除的值"
        
        # 删除
        result = self.cache.delete("delete_key")
        assert result is True
        
        # 确认已删除
        assert self.cache.get("delete_key") is None
        
        # 删除不存在的键
        result = self.cache.delete("not_exist")
        assert result is False
    
    def test_exists(self):
        """测试exists方法"""
        # 设置缓存
        self.cache.set("exists_key", "存在的值")
        
        # 检查存在
        assert self.cache.exists("exists_key") is True
        assert self.cache.exists("not_exist") is False
    
    def test_clear(self):
        """测试清除"""
        # 设置多个缓存
        self.cache.set("clear_key1", "值1")
        self.cache.set("clear_key2", "值2")
        self.cache.set("other_key", "其他值")
        
        # 清除特定模式的缓存
        count = self.cache.clear("clear_*")
        assert count == 2
        
        # 确认已清除
        assert self.cache.get("clear_key1") is None
        assert self.cache.get("clear_key2") is None
        assert self.cache.get("other_key") == "其他值"
        
        # 清除所有缓存
        count = self.cache.clear()
        assert count == 1
        assert self.cache.get("other_key") is None
    
    def test_incr(self):
        """测试递增"""
        # 设置计数器
        self.cache.set("counter", 5)
        
        # 递增
        result = self.cache.incr("counter")
        assert result == 6
        
        # 再次递增
        result = self.cache.incr("counter", 2)
        assert result == 8
        
        # 递增不存在的键
        result = self.cache.incr("new_counter")
        assert result == 1

# 测试缓存工厂
class TestCacheFactory:
    """缓存工厂测试类"""
    
    @patch('app.cache.cache_factory.redis_cache')
    @patch('app.cache.cache_factory.memory_cache')
    def test_cache_factory_redis(self, mock_memory_cache, mock_redis_cache):
        """测试Redis缓存工厂"""
        # 模拟Redis可用
        mock_redis_cache.health_check.return_value = True
        
        # 创建工厂
        factory = CacheFactory(cache_type=CACHE_TYPE_REDIS)
        
        # 验证使用了Redis缓存
        assert factory.get_type() == CACHE_TYPE_REDIS
        assert factory.cache == mock_redis_cache
    
    @patch('app.cache.cache_factory.redis_cache')
    @patch('app.cache.cache_factory.memory_cache')
    def test_cache_factory_redis_fallback(self, mock_memory_cache, mock_redis_cache):
        """测试Redis不可用时的降级"""
        # 模拟Redis不可用
        mock_redis_cache.health_check.return_value = False
        
        # 创建工厂
        factory = CacheFactory(cache_type=CACHE_TYPE_REDIS)
        
        # 验证降级使用了内存缓存
        assert factory.get_type() == CACHE_TYPE_MEMORY
        assert factory.cache == mock_memory_cache
    
    @patch('app.cache.cache_factory.redis_cache')
    @patch('app.cache.cache_factory.memory_cache')
    def test_cache_factory_memory(self, mock_memory_cache, mock_redis_cache):
        """测试内存缓存工厂"""
        # 创建工厂
        factory = CacheFactory(cache_type=CACHE_TYPE_MEMORY)
        
        # 验证使用了内存缓存
        assert factory.get_type() == CACHE_TYPE_MEMORY
        assert factory.cache == mock_memory_cache
        
        # 验证未检查Redis
        mock_redis_cache.health_check.assert_not_called()
