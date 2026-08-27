import base64
import gzip
import json
import uuid
from time import time, sleep
import xbmcgui
from resources.lib.utilities import log

# How long an index-lock holder may be presumed alive. Anything older is a
# crashed invocation's leftover and gets stolen.
_LOCK_STALE_SECONDS = 2.0


class Cache(object):
    """Caches Python values as gzip-compressed JSON in Kodi window properties."""

    def __init__(self, key_prefix=""):
        self.key_prefix = key_prefix
        self._win = xbmcgui.Window(10000)
        self._index_key = f"{key_prefix}:__index__" if key_prefix else "__cache_index__"
        self._lock_key = self._index_key + ":__lock__"

    def _with_index_lock(self, mutate):
        """Runs mutate() holding a cross-invocation mutex on the index.

        Window properties offer no compare-and-swap, so a bare read-modify-write
        lets two overlapping invocations drop each other's keys no matter how
        often each verifies - a slower writer that read first can overwrite a
        faster writer AFTER its verification passed. Individual property reads
        and writes ARE atomic though, which is enough for a token spinlock:
        write your token, read back, and only the writer whose token survived
        proceeds - the loser retries. A lock left behind by a crashed
        invocation is stolen after _LOCK_STALE_SECONDS; if the lock cannot be
        won at all, mutate() runs unlocked - the pre-lock behavior, never worse.
        """
        token = uuid.uuid4().hex
        try:
            for _ in range(100):
                current = self._win.getProperty(self._lock_key)
                if current:
                    try:
                        held_since = float(current.split(":", 1)[1])
                    except (IndexError, ValueError):
                        held_since = 0.0
                    if time() - held_since < _LOCK_STALE_SECONDS:
                        sleep(0.002)
                        continue
                self._win.setProperty(self._lock_key, f"{token}:{time()}")
                sleep(0.001)  # let a colliding writer's set land before we re-read
                if self._win.getProperty(self._lock_key).startswith(token):
                    try:
                        mutate()
                    finally:
                        self._win.clearProperty(self._lock_key)
                    return
        except Exception:
            pass
        try:
            mutate()
        except Exception:
            pass

    def _add_to_index(self, key):
        def mutate():
            raw = self._win.getProperty(self._index_key)
            keys = set(json.loads(raw)) if raw else set()
            keys.add(key)
            self._win.setProperty(self._index_key, json.dumps(sorted(keys)))
        self._with_index_lock(mutate)

    def set(self, key, value, expires=60 * 60 * 24 * 7):
        log(__name__, f"caching {key}")
        full_key = f"{self.key_prefix}:{key}" if self.key_prefix else key
        expires_at = expires + time()

        raw_json = json.dumps(dict(value=value, expires=expires_at)).encode("utf-8")
        compressed = gzip.compress(raw_json)
        b64_str = base64.b64encode(compressed).decode("ascii")
        self._win.setProperty(full_key, f"gz:{b64_str}")
        self._add_to_index(full_key)

    def get(self, key, default=None):
        log(__name__, f"got request for {key} from cache")
        result = default
        full_key = f"{self.key_prefix}:{key}" if self.key_prefix else key

        prop_val = self._win.getProperty(full_key)
        if prop_val:
            try:
                if prop_val.startswith("gz:"):
                    compressed = base64.b64decode(prop_val[3:])
                    raw_json = gzip.decompress(compressed).decode("utf-8")
                    cache_data = json.loads(raw_json)
                else:
                    # Discard legacy uncompressed cache or attempt fallback
                    cache_data = json.loads(prop_val)

                if cache_data.get("expires", 0) > time():
                    result = cache_data["value"]
                    log(__name__, f"got {key} from cache")
            except Exception:
                pass

        return result

    def get_stats(self):
        """Returns (active_item_count, total_compressed_bytes) of valid cached items."""
        count = 0
        total_bytes = 0
        try:
            raw = self._win.getProperty(self._index_key)
            if raw:
                keys = json.loads(raw)
                for k in keys:
                    val = self._win.getProperty(k)
                    if val:
                        try:
                            if val.startswith("gz:"):
                                compressed = base64.b64decode(val[3:])
                                raw_json = gzip.decompress(compressed).decode("utf-8")
                                data = json.loads(raw_json)
                            else:
                                data = json.loads(val)

                            if data.get("expires", 0) > time():
                                count += 1
                                total_bytes += len(val.encode("ascii"))
                        except Exception:
                            pass
        except Exception:
            pass
        return count, total_bytes

    def clear(self):
        """Clears all cached properties from memory and returns (cleared_count, cleared_bytes)."""
        count, total_bytes = self.get_stats()
        try:
            raw = self._win.getProperty(self._index_key)
            cleared = set(json.loads(raw)) if raw else set()
            for k in cleared:
                self._win.clearProperty(k)

            # A concurrent invocation can append to the index while we clear.
            # Blindly clearing the index would orphan its live property, so
            # under the same lock as _add_to_index, rewrite the index to
            # whatever arrived meanwhile minus the keys we cleared.
            def mutate():
                cur_raw = self._win.getProperty(self._index_key)
                remaining = (set(json.loads(cur_raw)) if cur_raw else set()) - cleared
                if remaining:
                    self._win.setProperty(self._index_key, json.dumps(sorted(remaining)))
                else:
                    self._win.clearProperty(self._index_key)
            self._with_index_lock(mutate)
        except Exception:
            pass
        return count, total_bytes


def get_total_cache_stats():
    """Returns (total_count, total_bytes, formatted_str) across all cache prefixes."""
    total_count = 0
    total_bytes = 0
    for prefix in ("os_com", "OpenSubtitles", "os_library", ""):
        c = Cache(prefix)
        cnt, b = c.get_stats()
        total_count += cnt
        total_bytes += b

    kb = round(total_bytes / 1024, 1)
    formatted = f"{total_count} items ({kb} KB)"
    return total_count, total_bytes, formatted


def sync_cache_stats_setting():
    """Updates the cache_stats setting in add-on configuration."""
    try:
        import xbmcaddon
        addon = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
        _, _, formatted = get_total_cache_stats()
        addon.setSetting("cache_stats", formatted)
        return formatted
    except Exception:
        return None
