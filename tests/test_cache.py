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


def test_clear_keeps_entry_written_concurrently():
    """Clear Cache overlapping a write must not orphan the writer's entry:
    the index is reconciled, not blindly cleared."""
    import json as _json
    from unittest.mock import patch
    from resources.lib.cache import Cache

    c = Cache(key_prefix="race2")
    c.set("old", {"v": 1})
    real_clear = c._win.clearProperty
    state = {"injected": False}

    def clearing_with_concurrent_writer(prop):
        real_clear(prop)
        if prop == "race2:old" and not state["injected"]:
            state["injected"] = True
            # concurrent invocation writes a fresh entry mid-clear
            c._win.setProperty("race2:new", "gz:ignored")
            c._win.setProperty(c._index_key, _json.dumps(["race2:old", "race2:new"]))

    with patch.object(c._win, "clearProperty", side_effect=clearing_with_concurrent_writer):
        c.clear()

    idx_raw = c._win.getProperty(c._index_key)
    idx = _json.loads(idx_raw) if idx_raw else []
    assert "race2:new" in idx, "concurrently written key must stay indexed"
    assert "race2:old" not in idx
    assert c._win.getProperty("race2:new"), "concurrent entry's property must survive"


def test_index_lock_serializes_concurrent_writers():
    """Token spinlock: two threads adding different keys concurrently must
    both end up in the index - the exact interleaving the verify-retry
    approach could not survive."""
    import threading
    import json as _json
    from resources.lib.cache import Cache

    c = Cache(key_prefix="lock_test")
    errors = []

    def writer(name):
        try:
            for i in range(20):
                c.set(f"{name}_{i}", {"v": i})
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(f"w{t}",)) for t in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert not errors
    idx = set(_json.loads(c._win.getProperty(c._index_key)))
    expected = {f"lock_test:w{t}_{i}" for t in range(3) for i in range(20)}
    assert expected <= idx, f"lost {sorted(expected - idx)[:5]}"


def test_index_lock_steals_stale_lock():
    """A crashed invocation's leftover lock must not wedge the cache."""
    import json as _json
    from resources.lib.cache import Cache

    c = Cache(key_prefix="stale_lock")
    c._win.setProperty(c._lock_key, "deadbeef:1.0")  # ancient timestamp
    c.set("survivor", {"v": 1})
    idx = _json.loads(c._win.getProperty(c._index_key))
    assert "stale_lock:survivor" in idx
    assert not c._win.getProperty(c._lock_key), "lock must be released after steal"


def test_lock_fallback_merges_with_verification():
    """Even when the lock can never be acquired (permanent contention), the
    fallback must merge-and-verify, not blind-write once."""
    import json as _json
    from unittest.mock import patch
    from resources.lib import cache as cache_mod
    from resources.lib.cache import Cache

    c = Cache(key_prefix="livelock")
    # permanently held, never stale
    with patch.object(cache_mod, "_LOCK_STALE_SECONDS", 10**6):
        c._win.setProperty(c._lock_key, f"foreign:{__import__('time').time()}")
        real_set = c._win.setProperty
        state = {"clobbered": False}

        def clobbering_set(prop, value):
            real_set(prop, value)
            if prop == c._index_key and not state["clobbered"]:
                state["clobbered"] = True
                real_set(prop, '["livelock:other"]')  # concurrent overwrite

        with patch.object(cache_mod, "time", side_effect=__import__('time').time), \
             patch.object(c._win, "setProperty", side_effect=clobbering_set):
            c._add_to_index("livelock:mine")

    idx = set(_json.loads(c._win.getProperty(c._index_key)))
    assert "livelock:mine" in idx, "verified merge must survive the clobber"
