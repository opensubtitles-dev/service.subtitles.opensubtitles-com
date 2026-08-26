"""Kodi-side smoke test: import every shipped module inside the REAL embedded
Python of whichever Kodi version this runs in, then log one machine-readable
verdict line that the CI driver greps out of kodi.log.

Runs as an xbmc.service add-on so Kodi starts it automatically - headless
containers offer no reliable way to trigger a script by hand. CI-only; this
add-on is never shipped to users (not in scripts/addon_manifest.py).
"""
import sys
import traceback

import xbmc
import xbmcaddon
import xbmcvfs

TARGET_ADDON = "service.subtitles.opensubtitles-com"

# Everything service.py and the settings entry points pull in, in dependency
# order. data_collector/subtitle_downloader exercise xbmcplugin/xbmcgui;
# provider exercises the bundled requests module.
MODULES = [
    "resources.lib.exceptions",
    "resources.lib.utilities",
    "resources.lib.cache",
    "resources.lib.file_operations",
    "resources.lib.matcher",
    "resources.lib.data_collector",
    "resources.lib.osclient.model.request.abstract",
    "resources.lib.osclient.model.request.subtitles",
    "resources.lib.osclient.model.request.download",
    "resources.lib.osclient.provider",
    "resources.lib.subtitle_downloader",
]


def run():
    py = ".".join(str(v) for v in sys.version_info[:3])
    kodi = xbmc.getInfoLabel("System.BuildVersion")
    try:
        addon_path = xbmcvfs.translatePath(xbmcaddon.Addon(TARGET_ADDON).getAddonInfo("path"))
    except Exception:
        xbmc.log(f"SMOKETEST RESULT: FAIL | kodi={kodi} | python={py} | "
                 f"target add-on {TARGET_ADDON} not installed/enabled", xbmc.LOGINFO)
        return

    sys.path.insert(0, addon_path)
    failures = []
    for name in MODULES:
        try:
            __import__(name)
        except Exception:
            failures.append(name)
            xbmc.log(f"SMOKETEST IMPORT FAIL {name}:\n{traceback.format_exc()}", xbmc.LOGINFO)

    verdict = "PASS" if not failures else "FAIL"
    xbmc.log(f"SMOKETEST RESULT: {verdict} | kodi={kodi} | python={py} | "
             f"imported={len(MODULES) - len(failures)}/{len(MODULES)}"
             + (f" | failed={','.join(failures)}" if failures else ""), xbmc.LOGINFO)


if __name__ == "__main__":
    run()
