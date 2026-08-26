import os
import re
import sys
import xml.etree.ElementTree as ET
import requests

import xbmc
import xbmcgui
import xbmcaddon

# --- addon import path guard (keep this above any `resources.*` import) ------------
# RunScript(<file path>) runs this "without an addon", so Kodi puts every installed
# add-on's library directory on sys.path ahead of ours and a foreign top-level
# `resources` package shadows ours. This script imports nothing from `resources` today;
# the guard is here so that adding such an import later cannot silently break it.
# See test_connection.py for the full story (issue #39).
_addon_path = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.normpath(p) != _addon_path]
sys.path.insert(0, _addon_path)
# Only evict a *foreign* `resources`; re-importing our own would duplicate its classes.
_res = sys.modules.get("resources")
if _res is not None and not any(os.path.normpath(p).startswith(_addon_path)
                                for p in getattr(_res, "__path__", [])):
    for _module in [m for m in list(sys.modules) if m == "resources" or m.startswith("resources.")]:
        del sys.modules[_module]
# -----------------------------------------------------------------------------------

from resources.lib.utilities import get_user_agent

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString

REMOTE_MANIFEST_URLS = [
    "https://kodi.opensubtitles.com/addons.xml",
    "https://raw.githubusercontent.com/opensubtitles/service.subtitles.opensubtitles-com/master/addon.xml",
    "https://raw.githubusercontent.com/opensubtitles-dev/service.subtitles.opensubtitles-com/master/addon.xml",
]


def parse_version_tuple(v_str):
    """Converts version string (e.g. '1.0.15') into integer tuple for comparison."""
    if not v_str:
        return (0, 0, 0)
    numbers = re.findall(r"\d+", str(v_str))
    return tuple(int(n) for n in numbers) if numbers else (0, 0, 0)


def extract_remote_version(xml_content):
    """Extracts the version attribute for service.subtitles.opensubtitles-com from XML content."""
    root = ET.fromstring(xml_content)
    if root.tag == "addon" and root.attrib.get("id") == "service.subtitles.opensubtitles-com":
        return root.attrib.get("version")
    elif root.tag == "addons":
        for addon in root.findall("addon"):
            if addon.attrib.get("id") == "service.subtitles.opensubtitles-com":
                return addon.attrib.get("version")
    return None


def fetch_latest_remote_version():
    """Queries remote repositories and returns latest remote version string or None."""
    headers = {"User-Agent": get_user_agent()}
    for url in REMOTE_MANIFEST_URLS:
        try:
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                v = extract_remote_version(resp.text)
                if v:
                    return v
        except Exception:
            continue
    return None


def check_updates():
    current_version = __addon__.getAddonInfo("version") or "1.0.15"
    dialog = xbmcgui.Dialog()

    try:
        latest_version = fetch_latest_remote_version()
    except Exception as e:
        latest_version = None

    if not latest_version:
        dialog.ok(__addon_name__, f"Could not connect to update server (installed: v{current_version}).\nPlease check your network connection.")
        return

    curr_tuple = parse_version_tuple(current_version)
    latest_tuple = parse_version_tuple(latest_version)

    if latest_tuple > curr_tuple:
        # Update available. Compact on purpose: the dialog scrolls past ~3 lines
        # and cannot be resized (skin-owned) - no blank lines, no bullet rows.
        msg = (
            f"New version available: v{current_version} → [B]v{latest_version}[/B]\n"
            f"Check Kodi repository for updates now?"
        )
        if dialog.yesno(__addon_name__, msg):
            xbmc.executebuiltin("UpdateAddonRepos")
            # Kodi refreshes repos and installs the update in the background with
            # no feedback of its own - the user is left staring at settings while
            # the add-on silently swaps underneath. Poll the add-on database until
            # the installed version reaches the target so we can report a definitive
            # result. Fresh Addon() each poll: long-lived instances serve a stale
            # snapshot (docs/kodi_api_internals.md gotcha 12).
            addon_id = __addon__.getAddonInfo("id")
            monitor = xbmc.Monitor()
            progress = xbmcgui.DialogProgress()
            progress.create(__addon_name__, f"Updating to [B]v{latest_version}[/B]…")
            updated = False
            wait_seconds = 60
            for elapsed in range(wait_seconds):
                if monitor.abortRequested() or progress.iscanceled():
                    break
                progress.update(int(elapsed * 100 / wait_seconds))
                if monitor.waitForAbort(1):
                    break
                installed = xbmcaddon.Addon(addon_id).getAddonInfo("version")
                if parse_version_tuple(installed) >= latest_tuple:
                    updated = True
                    break
            progress.close()
            if updated:
                dialog.ok(__addon_name__, f"Updated to [B]v{installed}[/B].")
            else:
                # Timeout or cancel - the install may still land, or auto-update
                # may be disabled in Kodi. Say so instead of going silent.
                dialog.ok(__addon_name__,
                          "Update is still installing in the background.\n"
                          "If nothing happens, update from My add-ons or enable auto-updates.")
    else:
        # Up to date
        dialog.ok(__addon_name__, f"Up to date - [B]v{current_version}[/B] is the latest version.")


if __name__ == "__main__":
    check_updates()
