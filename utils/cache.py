"""
Caching utilities using Redis for performance optimization
Provides decorators and helpers for caching expensive operations
"""

import hashlib
import json
import os
import pickle
from functools import wraps
from typing import Any, Callable, Optional, Union

from dotenv import load_dotenv

try:
    import redis
    from redis import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

load_dotenv()


class CacheConfig:
    """Redis cache configuration"""

    # Support Redis URL (e.g., redis://user:password@host:port/db)
    REDIS_URL = os.getenv("REDIS_URL", None)
    
    # Individual config (used if REDIS_URL not provided)
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    # Convert empty strings to None to avoid issues with docker-compose empty defaults
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None) or None
    REDIS_USERNAME = os.getenv("REDIS_USERNAME", None) or None
    
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1 hour


class CacheManager:
    """
    Centralized cache management using Redis

    Example:
        cache = CacheManager()
        cache.set("key", {"data": "value"}, ttl=300)
        result = cache.get("key")
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize cache manager

        Args:
            enabled: Whether caching is enabled
        """
        self.enabled = enabled and CacheConfig.CACHE_ENABLED and REDIS_AVAILABLE
        self._client: Optional[Redis] = None

        if self.enabled:
            try:
                # Use Redis URL if provided, otherwise use individual config
                if CacheConfig.REDIS_URL:
                    # Parse Redis URL: redis://[username]:[password]@host:port[/db]
                    self._client = Redis.from_url(
                        CacheConfig.REDIS_URL,
                        decode_responses=False,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        max_connections=50,  # Connection pool size
                        retry_on_timeout=True,
                    )
                else:
                    # Use individual config parameters
                    self._client = Redis(
                        host=CacheConfig.REDIS_HOST,
                        port=CacheConfig.REDIS_PORT,
                        db=CacheConfig.REDIS_DB,
                        password=CacheConfig.REDIS_PASSWORD,
                        username=CacheConfig.REDIS_USERNAME,
                        decode_responses=False,  # We'll handle encoding/decoding
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        max_connections=50,  # Connection pool size
                        retry_on_timeout=True,
                    )
                # Test connection
                self._client.ping()
            except Exception as e:
                # Only show warning if caching was explicitly enabled
                # If CACHE_ENABLED is false, this code shouldn't run, but just in case
                if CacheConfig.CACHE_ENABLED:
                    print(f"⚠️ Redis connection failed: {e}. Caching disabled. (This is not an error - the app works without Redis)")
                self.enabled = False
                self._client = None

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self._client:
            return None

        try:
            value = self._client.get(key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (any picklable object)
            ttl: Time to live in seconds (default: CacheConfig.DEFAULT_TTL)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self._client:
            return False

        try:
            ttl = ttl or CacheConfig.DEFAULT_TTL
            serialized = pickle.dumps(value)
            self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self._client:
            return False

        try:
            self._client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear all cache entries

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self._client:
            return False

        try:
            self._client.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.enabled or not self._client:
            return False

        try:
            return bool(self._client.exists(key))
        except Exception as e:
            print(f"Cache exists check error for key {key}: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self._client:
            return {"enabled": False}

        try:
            info = self._client.info()
            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """
    Get global cache manager instance

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from function arguments

    Args:
        prefix: Key prefix (typically function name)
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string

    Example:
        key = generate_cache_key("query", "what is AI", top_k=10)
        # Returns: "query:hash_of_args"
    """
    # Create a stable representation of arguments
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}
    key_str = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()[:16]

    return f"{prefix}:{key_hash}"


def cached(ttl: int = CacheConfig.DEFAULT_TTL, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Optional key prefix (defaults to function name)

    Example:
        @cached(ttl=300, key_prefix="search")
        def expensive_search(query: str, limit: int = 10):
            # Expensive operation
            return results
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def async_cached(
    ttl: int = CacheConfig.DEFAULT_TTL, key_prefix: Optional[str] = None
):
    """
    Decorator factory to cache async function results

    Args:
        ttl: Time to live in seconds
        key_prefix: Optional key prefix (defaults to function name)

    Example:
        @async_cached(ttl=300)
        async def fetch_data(article_id: int):
            # Expensive async operation
            return data
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute async function
            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern

    Args:
        pattern: Redis key pattern (e.g., "query:*", "company:123:*")

    Returns:
        Number of keys deleted

    Example:
        # Invalidate all query caches
        invalidate_cache_pattern("query:*")

        # Invalidate specific company caches
        invalidate_cache_pattern("company:456:*")
    """
    cache = get_cache()

    if not cache.enabled or not cache._client:
        return 0

    try:
        keys = cache._client.keys(pattern)
        if keys:
            return cache._client.delete(*keys)
        return 0
    except Exception as e:
        print(f"Cache invalidation error for pattern {pattern}: {e}")
        return 0


# Specific cache helpers for common operations


class QueryCache:
    """Helper class for caching query results"""

    @staticmethod
    def get(question: str) -> Optional[dict]:
        """Get cached query result"""
        cache = get_cache()
        key = generate_cache_key("query", question)
        return cache.get(key)

    @staticmethod
    def set(question: str, result: dict, ttl: int = 3600):
        """Cache query result"""
        cache = get_cache()
        key = generate_cache_key("query", question)
        cache.set(key, result, ttl=ttl)

    @staticmethod
    def invalidate(question: str):
        """Invalidate specific query cache"""
        cache = get_cache()
        key = generate_cache_key("query", question)
        cache.delete(key)

    @staticmethod
    def clear_all():
        """Clear all query caches"""
        return invalidate_cache_pattern("query:*")


class EntityCache:
    """Helper class for caching entity data"""

    @staticmethod
    def get(entity_name: str) -> Optional[dict]:
        """Get cached entity data"""
        cache = get_cache()
        key = generate_cache_key("entity", entity_name)
        return cache.get(key)

    @staticmethod
    def set(entity_name: str, data: dict, ttl: int = 7200):
        """Cache entity data"""
        cache = get_cache()
        key = generate_cache_key("entity", entity_name)
        cache.set(key, data, ttl=ttl)

    @staticmethod
    def invalidate(entity_name: str):
        """Invalidate specific entity cache"""
        cache = get_cache()
        key = generate_cache_key("entity", entity_name)
        cache.delete(key)

    @staticmethod
    def clear_all():
        """Clear all entity caches"""
        return invalidate_cache_pattern("entity:*")
