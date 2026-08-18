import json
from time import time
import xbmcgui
from resources.lib.utilities import log


class Cache(object):
    """Caches Python values as JSON in Kodi window properties."""

    def __init__(self, key_prefix=""):
        self.key_prefix = key_prefix
        self._win = xbmcgui.Window(10000)
        self._index_key = f"{key_prefix}:__index__" if key_prefix else "__cache_index__"

    def _add_to_index(self, key):
        try:
            raw = self._win.getProperty(self._index_key)
            keys = set(json.loads(raw)) if raw else set()
            keys.add(key)
            self._win.setProperty(self._index_key, json.dumps(list(keys)))
        except Exception:
            pass

    def set(self, key, value, expires=60 * 60 * 24 * 7):
        log(__name__, f"caching {key}")
        full_key = f"{self.key_prefix}:{key}" if self.key_prefix else key
        expires_at = expires + time()

        cache_data_str = json.dumps(dict(value=value, expires=expires_at))
        self._win.setProperty(full_key, cache_data_str)
        self._add_to_index(full_key)

    def get(self, key, default=None):
        log(__name__, f"got request for {key} from cache")
        result = default
        full_key = f"{self.key_prefix}:{key}" if self.key_prefix else key

        cache_data_str = self._win.getProperty(full_key)
        if cache_data_str:
            try:
                cache_data = json.loads(cache_data_str)
                if cache_data.get("expires", 0) > time():
                    result = cache_data["value"]
                    log(__name__, f"got {key} from cache")
            except (ValueError, KeyError, TypeError):
                pass

        return result

    def get_stats(self):
        """Returns (active_item_count, total_bytes) of valid cached items."""
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
                            data = json.loads(val)
                            if data.get("expires", 0) > time():
                                count += 1
                                total_bytes += len(val.encode("utf-8"))
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
            if raw:
                keys = json.loads(raw)
                for k in keys:
                    self._win.clearProperty(k)
            self._win.clearProperty(self._index_key)
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
