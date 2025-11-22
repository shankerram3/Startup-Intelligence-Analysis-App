"""
Unit tests for caching utilities
Tests cache operations without requiring actual Redis connection
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from utils.cache import (
    CacheManager,
    generate_cache_key,
    QueryCache,
    EntityCache,
    get_cache
)


class TestCacheKeyGeneration:
    """Test cache key generation"""

    def test_generate_basic_key(self):
        """Test basic cache key generation"""
        key = generate_cache_key("prefix", "arg1", "arg2")
        assert key.startswith("prefix:")
        assert len(key) > len("prefix:")

    def test_generate_key_with_kwargs(self):
        """Test cache key generation with kwargs"""
        key = generate_cache_key("query", "question", limit=10, offset=0)
        assert key.startswith("query:")

    def test_same_args_same_key(self):
        """Test same arguments produce same key"""
        key1 = generate_cache_key("test", "arg1", param="value")
        key2 = generate_cache_key("test", "arg1", param="value")
        assert key1 == key2

    def test_different_args_different_keys(self):
        """Test different arguments produce different keys"""
        key1 = generate_cache_key("test", "arg1")
        key2 = generate_cache_key("test", "arg2")
        assert key1 != key2

    def test_kwargs_order_independent(self):
        """Test kwargs order doesn't affect key"""
        key1 = generate_cache_key("test", a=1, b=2)
        key2 = generate_cache_key("test", b=2, a=1)
        assert key1 == key2


class TestCacheManager:
    """Test CacheManager class"""

    @patch('utils.cache.REDIS_AVAILABLE', False)
    def test_cache_disabled_when_redis_unavailable(self):
        """Test cache is disabled when Redis not available"""
        cache = CacheManager()
        assert cache.enabled is False

    @patch('utils.cache.REDIS_AVAILABLE', True)
    @patch('utils.cache.Redis')
    def test_cache_initialization(self, mock_redis_class):
        """Test cache manager initialization"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client

        cache = CacheManager()
        assert cache.enabled is True
        mock_client.ping.assert_called_once()

    @patch('utils.cache.REDIS_AVAILABLE', True)
    @patch('utils.cache.Redis')
    def test_cache_get_returns_none_when_disabled(self, mock_redis_class):
        """Test get returns None when cache is disabled"""
        cache = CacheManager(enabled=False)
        result = cache.get("test_key")
        assert result is None

    @patch('utils.cache.REDIS_AVAILABLE', True)
    @patch('utils.cache.Redis')
    def test_cache_set_returns_false_when_disabled(self, mock_redis_class):
        """Test set returns False when cache is disabled"""
        cache = CacheManager(enabled=False)
        result = cache.set("test_key", "test_value")
        assert result is False

    @patch('utils.cache.REDIS_AVAILABLE', True)
    @patch('utils.cache.Redis')
    def test_cache_exists(self, mock_redis_class):
        """Test cache exists check"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.exists.return_value = 1
        mock_redis_class.return_value = mock_client

        cache = CacheManager()
        result = cache.exists("test_key")
        assert result is True

    @patch('utils.cache.REDIS_AVAILABLE', True)
    @patch('utils.cache.Redis')
    def test_cache_delete(self, mock_redis_class):
        """Test cache delete"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.delete.return_value = 1
        mock_redis_class.return_value = mock_client

        cache = CacheManager()
        result = cache.delete("test_key")
        assert result is True

    @patch('utils.cache.REDIS_AVAILABLE', True)
    @patch('utils.cache.Redis')
    def test_cache_clear(self, mock_redis_class):
        """Test cache clear"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.flushdb.return_value = True
        mock_redis_class.return_value = mock_client

        cache = CacheManager()
        result = cache.clear()
        assert result is True

    @patch('utils.cache.REDIS_AVAILABLE', True)
    @patch('utils.cache.Redis')
    def test_cache_stats(self, mock_redis_class):
        """Test cache statistics retrieval"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.info.return_value = {
            "used_memory_human": "1M",
            "connected_clients": 5,
            "total_commands_processed": 1000
        }
        mock_redis_class.return_value = mock_client

        cache = CacheManager()
        stats = cache.get_stats()
        assert stats["enabled"] is True
        assert "used_memory" in stats


class TestQueryCache:
    """Test QueryCache helper class"""

    @patch('utils.cache.get_cache')
    def test_query_cache_get(self, mock_get_cache):
        """Test QueryCache.get"""
        mock_cache = Mock()
        mock_cache.get.return_value = {"answer": "test"}
        mock_get_cache.return_value = mock_cache

        result = QueryCache.get("test question")
        assert result == {"answer": "test"}

    @patch('utils.cache.get_cache')
    def test_query_cache_set(self, mock_get_cache):
        """Test QueryCache.set"""
        mock_cache = Mock()
        mock_cache.set.return_value = True
        mock_get_cache.return_value = mock_cache

        result = QueryCache.set("test question", {"answer": "test"})
        assert mock_cache.set.called

    @patch('utils.cache.get_cache')
    def test_query_cache_invalidate(self, mock_get_cache):
        """Test QueryCache.invalidate"""
        mock_cache = Mock()
        mock_cache.delete.return_value = True
        mock_get_cache.return_value = mock_cache

        QueryCache.invalidate("test question")
        assert mock_cache.delete.called


class TestEntityCache:
    """Test EntityCache helper class"""

    @patch('utils.cache.get_cache')
    def test_entity_cache_get(self, mock_get_cache):
        """Test EntityCache.get"""
        mock_cache = Mock()
        mock_cache.get.return_value = {"name": "TestCo", "type": "Company"}
        mock_get_cache.return_value = mock_cache

        result = EntityCache.get("TestCo")
        assert result["name"] == "TestCo"

    @patch('utils.cache.get_cache')
    def test_entity_cache_set(self, mock_get_cache):
        """Test EntityCache.set"""
        mock_cache = Mock()
        mock_cache.set.return_value = True
        mock_get_cache.return_value = mock_cache

        data = {"name": "TestCo", "type": "Company"}
        EntityCache.set("TestCo", data)
        assert mock_cache.set.called
