import time
from resources.lib.cache import Cache

def test_cache_set_and_get():
    cache = Cache(key_prefix="test_prefix")
    cache.set("foo", {"data": 123}, expires=300)
    result = cache.get("foo")
    assert result == {"data": 123}

def test_cache_miss_returns_default():
    cache = Cache(key_prefix="test_prefix")
    result = cache.get("non_existent_key", default="fallback")
    assert result == "fallback"

def test_cache_expiration():
    cache = Cache(key_prefix="test_prefix")
    # Expired immediately
    cache.set("expired_key", "value", expires=-10)
    result = cache.get("expired_key", default=None)
    assert result is None

def test_cache_stats_and_clear():
    cache = Cache(key_prefix="stats_test")
    cache.set("item1", {"hello": "world"}, expires=300)
    cache.set("item2", {"foo": "bar"}, expires=300)
    
    count, total_bytes = cache.get_stats()
    assert count == 2
    assert total_bytes > 0
    
    cleared_count, cleared_bytes = cache.clear()
    assert cleared_count == 2
    assert cleared_bytes == total_bytes
    
    # After clear, items are gone
    assert cache.get("item1") is None
    assert cache.get("item2") is None
    count_after, bytes_after = cache.get_stats()
    assert count_after == 0
    assert bytes_after == 0
