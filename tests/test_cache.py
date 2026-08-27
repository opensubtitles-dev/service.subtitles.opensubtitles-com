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


def test_cache_uses_gzip_compression():
    cache = Cache(key_prefix="gz_test")
    large_data = {"subtitles": [{"release": f"Release.Name.2024.1080p-{i}", "downloads": i * 100} for i in range(50)]}
    cache.set("large_item", large_data, expires=300)

    # Check underlying window property directly to confirm 'gz:' prefix
    raw_prop = cache._win.getProperty("gz_test:large_item")
    assert raw_prop.startswith("gz:")

    # Decompressed result matches original data structure exactly
    retrieved = cache.get("large_item")
    assert retrieved == large_data


def test_add_to_index_recovers_from_concurrent_overwrite():
    """Window properties have no CAS: a concurrent invocation can clobber the
    index between our read and write. The verify-retry loop must re-add the
    key when the first write is lost."""
    from unittest.mock import patch
    from resources.lib.cache import Cache

    c = Cache(key_prefix="race_test")
    real_set = c._win.setProperty
    state = {"clobbered": False}

    def clobbering_set(prop, value):
        real_set(prop, value)
        if prop == c._index_key and not state["clobbered"]:
            state["clobbered"] = True
            # concurrent writer's list lands after ours, without our key
            real_set(prop, '["race_test:other_key"]')

    with patch.object(c._win, "setProperty", side_effect=clobbering_set):
        c.set("mine", {"v": 1})

    import json as _json
    idx = _json.loads(c._win.getProperty(c._index_key))
    assert "race_test:mine" in idx
    assert "race_test:other_key" in idx, "concurrent writer's key must survive the merge"
