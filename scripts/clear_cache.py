import os
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
from resources.lib.cache import Cache

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__version__ = __addon__.getAddonInfo("version")
__icon__ = xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("path"), "resources", "media", "os_logo_512x512.png"))

def clear_cache():
    total_items = 0
    total_bytes = 0

    # Clear memory cache across all prefixes used by provider and add-on
    for prefix in ("os_com", "OpenSubtitles", "os_library", ""):
        cache = Cache(prefix)
        items, b = cache.clear()
        total_items += items
        total_bytes += b

    # Also clean temporary subtitle downloads directory
    profile_temp = xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("profile"), "temp"))
    oss_temp = xbmcvfs.translatePath("special://temp/oss/")
    files_deleted = 0
    for temp_dir in (profile_temp, oss_temp):
        if xbmcvfs.exists(temp_dir):
            dirs, files = xbmcvfs.listdir(temp_dir)
            for f in files:
                file_path = os.path.join(temp_dir, f)
                try:
                    xbmcvfs.delete(file_path)
                    files_deleted += 1
                except Exception:
                    pass

    kb_cleared = round(total_bytes / 1024, 2)
    msg = f"Cache cleared: {total_items} items ({kb_cleared} KB freed)"
    if files_deleted:
        msg += f" | {files_deleted} temp files deleted"
    xbmcgui.Dialog().notification(f"{__addon_name__} v{__version__}", msg, __icon__, 3500, False)

if __name__ == "__main__":
    try:
        clear_cache()
    finally:
        xbmc.executebuiltin(f"Addon.OpenSettings({__addon__.getAddonInfo('id')})")
