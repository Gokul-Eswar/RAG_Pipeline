"""Unit tests for Redis caching."""

import json
import pytest
from unittest.mock import MagicMock, patch
import src.infrastructure.cache.redis as redis_module
from src.infrastructure.cache.redis import RedisCache, cache_result

class TestRedisCache:
    @pytest.fixture
    def mock_redis(self):
        # Create a mock for the redis library
        mock_lib = MagicMock()
        mock_client = MagicMock()
        mock_lib.Redis.return_value = mock_client
        
        # Patch the 'redis' attribute in the source module
        with patch.object(redis_module, 'redis', mock_lib):
            # Reset singleton before test
            RedisCache._instance = None
            yield mock_lib

    def tearDown(self):
        RedisCache._instance = None

    def test_singleton(self, mock_redis):
        """Test that RedisCache is a singleton."""
        cache1 = RedisCache()
        cache2 = RedisCache()
        assert cache1 is cache2
        # verify Redis was initialized once
        mock_redis.Redis.assert_called_once()

    def test_get_set(self, mock_redis):
        """Test get and set operations."""
        # Ensure singleton is reset
        RedisCache._instance = None
        cache = RedisCache()
        
        # Test Set
        cache.set("key", {"a": 1})
        mock_redis.Redis.return_value.setex.assert_called_with("key", 3600, '{"a": 1}')
        
        # Test Get
        mock_redis.Redis.return_value.get.return_value = '{"a": 1}'
        val = cache.get("key")
        assert val == {"a": 1}

    def test_cache_decorator(self, mock_redis):
        """Test the cache decorator."""
        RedisCache._instance = None
        
        # Setup mock behavior
        mock_client = mock_redis.Redis.return_value
        mock_client.get.return_value = None # First call miss
        
        @cache_result(ttl=60)
        def expensive_func(x, y):
            return x + y

        # First call: Cache miss, execute function
        result = expensive_func(2, 3)
        assert result == 5
        mock_client.setex.assert_called()
        
        # Second call: Cache hit logic is inside the decorator which re-instantiates RedisCache
        # We need to make sure the mocked client returns the value now
        # The decorator creates a NEW RedisCache() instance (or gets singleton)
        
        # Simulate cache hit for next call
        mock_client.get.return_value = '5'
        
        result_cached = expensive_func(2, 3)
        assert result_cached == 5
