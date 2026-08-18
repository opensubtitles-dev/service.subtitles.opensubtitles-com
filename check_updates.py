import re
import sys
import xml.etree.ElementTree as ET
import requests

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString

REMOTE_MANIFEST_URLS = [
    "https://raw.githubusercontent.com/opensubtitles/service.subtitles.opensubtitles-com/master/addon.xml",
    "https://raw.githubusercontent.com/opensubtitles-dev/service.subtitles.opensubtitles-com/master/addon.xml",
    "https://opensubtitles.github.io/service.subtitles.opensubtitles-com/addons.xml",
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
    headers = {"User-Agent": "Kodi/OpenSubtitles.com-Updater"}
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
        dialog.ok(__addon_name__, f"{__language__(32219)}: v{current_version}\n\nCould not connect to update server. Please check your network connection.")
        return

    curr_tuple = parse_version_tuple(current_version)
    latest_tuple = parse_version_tuple(latest_version)

    if latest_tuple > curr_tuple:
        # Update available
        __addon__.setSetting("addon_version", f"{current_version} (Update: v{latest_version})")
        msg = (
            f"A new version of OpenSubtitles.com is available!\n\n"
            f"• Installed Version: v{current_version}\n"
            f"• Latest Version: v{latest_version}\n\n"
            f"Check Kodi repository for updates now?"
        )
        if dialog.yesno(__addon_name__, msg):
            xbmc.executebuiltin("UpdateAddonRepos")
            icon_path = xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("path"), "resources", "media", "os_logo_512x512.png"))
            dialog.notification(__addon_name__, "Checking repository for updates...", icon_path, 4000)
    else:
        # Up to date
        __addon__.setSetting("addon_version", f"{current_version} (Latest)")
        dialog.ok(__addon_name__, f"OpenSubtitles.com is up to date!\n\n• Installed Version: v{current_version} (Latest)")


if __name__ == "__main__":
    check_updates()
