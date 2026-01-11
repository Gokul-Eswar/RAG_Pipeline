"""Redis caching implementation."""

import json
import functools
import hashlib
from typing import Any, Optional, Union
from src.utils.config import Config

try:
    import redis
except ImportError:
    redis = None


class RedisCache:
    """Redis cache wrapper."""

    _instance = None
    _client = None

    def __new__(cls):
        """Singleton pattern for Redis client."""
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        """Initialize Redis client."""
        if redis is None:
            print("Redis client not installed.")
            self._client = None
            return

        try:
            self._client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=1  # Fast fail if Redis not available
            )
            # Test connection
            self._client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self._client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._client:
            return None
        try:
            val = self._client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache."""
        if not self._client:
            return False
        try:
            self._client.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._client:
            return False
        try:
            return bool(self._client.delete(key))
        except Exception:
            return False


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results in Redis.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if Redis is not available
            cache = RedisCache()
            if not cache._client:
                return func(*args, **kwargs)

            try:
                # Create cache key from function name and arguments
                # For methods (args[0] is self), we might want to be careful not to include 'self' in hash
                # simpler approach: use module + func name + args string
                
                # Exclude 'self' from args if it's a method
                # This is a heuristic: if args[0] has 'client' or 'driver' attr, it's likely 'self' of a Repo
                call_args = args[1:] if args and hasattr(args[0], '__class__') else args
                
                key_str = f"{key_prefix or func.__name__}:{str(call_args)}:{str(kwargs)}"
                key_hash = hashlib.md5(key_str.encode()).hexdigest()
                cache_key = f"cache:{key_prefix or func.__name__}:{key_hash}"

                # Try get from cache
                cached_val = cache.get(cache_key)
                if cached_val is not None:
                    return cached_val

                # Execute function
                result = func(*args, **kwargs)

                # Cache result
                if result is not None:
                    cache.set(cache_key, result, ttl)

                return result
            except Exception as e:
                # Fallback to original function on any caching error
                print(f"Cache error: {e}")
                return func(*args, **kwargs)
        return wrapper
    return decorator
