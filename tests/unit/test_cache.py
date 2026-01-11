"""Unit tests for Redis caching."""

import unittest
from unittest.mock import MagicMock, patch
from src.infrastructure.cache.redis import RedisCache, cache_result


class TestRedisCache(unittest.TestCase):
    """Test RedisCache class."""

    def setUp(self):
        """Reset singleton."""
        RedisCache._instance = None

    @patch('src.infrastructure.cache.redis.redis')
    def test_singleton(self, mock_redis_pkg):
        """Test singleton pattern."""
        # Setup mock to return a client that doesn't fail ping
        mock_client = MagicMock()
        mock_redis_pkg.Redis.return_value = mock_client

        cache1 = RedisCache()
        cache2 = RedisCache()
        self.assertIs(cache1, cache2)

    @patch('src.infrastructure.cache.redis.redis')
    def test_get_set(self, mock_redis_pkg):
        """Test get and set methods."""
        mock_client = MagicMock()
        mock_redis_pkg.Redis.return_value = mock_client
        mock_client.get.return_value = '{"test": "value"}'

        cache = RedisCache()

        # Test Set
        cache.set("key", {"test": "value"})
        mock_client.setex.assert_called()

        # Test Get
        val = cache.get("key")
        self.assertEqual(val, {"test": "value"})


class TestCacheDecorator(unittest.TestCase):
    """Test cache_result decorator."""

    def setUp(self):
        """Reset singleton."""
        RedisCache._instance = None

    @patch('src.infrastructure.cache.redis.redis')
    def test_decorator_hits_cache(self, mock_redis_pkg):
        """Test decorator returns cached value."""
        mock_client = MagicMock()
        mock_redis_pkg.Redis.return_value = mock_client
        # Mock cache hit
        mock_client.get.return_value = '{"result": "cached"}'

        # Initialize cache to ensure client is set
        RedisCache()

        @cache_result(ttl=60)
        def my_func(arg):
            return {"result": "fresh"}

        result = my_func("test")
        self.assertEqual(result, {"result": "cached"})

    @patch('src.infrastructure.cache.redis.redis')
    def test_decorator_misses_cache(self, mock_redis_pkg):
        """Test decorator caches new value."""
        mock_client = MagicMock()
        mock_redis_pkg.Redis.return_value = mock_client
        # Mock cache miss
        mock_client.get.return_value = None

        RedisCache()

        @cache_result(ttl=60)
        def my_func(arg):
            return {"result": "fresh"}

        result = my_func("test")
        self.assertEqual(result, {"result": "fresh"})
        mock_client.setex.assert_called()


if __name__ == '__main__':
    unittest.main()