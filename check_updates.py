import os
import re
import sys
import json
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

FAST_TRACK_REPO_ID = "repository.opensubtitles-com"

# Kodi 19+ pins add-on updates to the repository the add-on was installed from
# (its "origin"). Without our fast-track repository installed, Kodi will only
# ever update this add-on from the official Kodi repository - telling the user a
# newer fast-track version exists would just be a version they cannot receive.
KODI_BRANCH_BY_MAJOR = {19: "matrix", 20: "nexus", 21: "omega", 22: "piers"}


def fetch_official_kodi_version():
    """Version in the official Kodi repository for this Kodi release, or None.

    Reads the addon.xml straight from the xbmc/repo-plugins branch matching the
    running Kodi major version. 404 simply means the add-on is not (yet) in the
    official repository for that release.
    """
    # System.BuildVersionShort is not present on every Kodi release;
    # System.BuildVersion ("21.3 (21.3.0) Git:...") exists everywhere - parse
    # whichever yields a leading major number.
    major = None
    for label in ("System.BuildVersionShort", "System.BuildVersion"):
        try:
            major = int(re.match(r"(\d+)", xbmc.getInfoLabel(label) or "").group(1))
            break
        except (ValueError, AttributeError):
            continue
    if major is None:
        return None
    branch = KODI_BRANCH_BY_MAJOR.get(major)
    if not branch:
        return None
    url = (f"https://raw.githubusercontent.com/xbmc/repo-plugins/{branch}/"
           f"service.subtitles.opensubtitles-com/addon.xml")
    try:
        resp = requests.get(url, headers={"User-Agent": get_user_agent()}, timeout=6)
        if resp.status_code == 200:
            return extract_remote_version(resp.text)
    except Exception:
        pass
    return None


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


def fast_track_repo_state():
    """'enabled', 'disabled', or 'missing' for the fast-track repository.

    Deliberately JSON-RPC: System.HasAddon stays true for a DISABLED add-on
    (verified live 2026-08-25), and a disabled repository serves no updates.
    A missing add-on returns an error payload, so no "result" key.
    """
    try:
        resp = json.loads(xbmc.executeJSONRPC(json.dumps({
            "jsonrpc": "2.0", "id": 1,
            "method": "Addons.GetAddonDetails",
            "params": {"addonid": FAST_TRACK_REPO_ID, "properties": ["enabled"]},
        })))
        addon = resp.get("result", {}).get("addon")
        if not addon:
            return "missing"
        return "enabled" if addon.get("enabled") else "disabled"
    except Exception:
        return "missing"


def show_fast_track_instructions(dialog, repo_state):
    if repo_state == "disabled":
        # The repository is already there - re-enabling is one step, don't bury
        # it in the full install walkthrough.
        dialog.ok(__addon_name__,
                  "The OpenSubtitles.com repository is installed but disabled.\n"
                  "Enable it under Add-ons > My add-ons > Add-on repository to receive updates.")
        return
    dialog.textviewer(
        f"{__addon_name__} - fast-track updates",
        "Kodi only updates an add-on from the repository it was installed from. "
        "To receive updates as soon as they are released, install the official "
        "OpenSubtitles.com repository:\n\n"
        "1. Settings > System > Add-ons: enable Unknown sources\n"
        "2. Settings > File manager > Add source: https://kodi.opensubtitles.com\n"
        "3. Add-ons > Install from zip file > that source > repository.opensubtitles-com.zip\n"
        "4. Install from repository > OpenSubtitles.com Official Repository > "
        "Subtitles > OpenSubtitles.com > Install\n\n"
        "Full instructions with screenshots: https://kodi.opensubtitles.com")


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

    # Without an ENABLED fast-track repository, Kodi's origin pinning means no
    # update we advertise can actually be delivered - Kodi only updates an
    # add-on from the repository it was installed from. Both the
    # update-available and the up-to-date dialog must say so, or the user is
    # left believing updates work.
    repo_state = fast_track_repo_state()

    if latest_tuple > curr_tuple:
        if repo_state != "enabled":
            official_version = fetch_official_kodi_version()
            official_part = f"v{official_version}" if official_version else "not yet available"
            msg = (
                f"Fast-track repo: [B]v{latest_version}[/B]  |  Official Kodi repo: {official_part}\n"
                f"(installed: v{current_version})\n"
                f"Show how to enable fast-track updates?"
            )
            if dialog.yesno(__addon_name__, msg):
                show_fast_track_instructions(dialog, repo_state)
            return

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
                # The add-on info dialog behind us populates its labels once at
                # open and no builtin repaints it - Container.Refresh only
                # reaches the list underneath (verified live 2026-08-25: info
                # screen kept showing the old version and icon). Close the stale
                # modal so the user lands on the refreshed list; harmless no-op
                # when no info dialog is open.
                xbmc.executebuiltin("Dialog.Close(addoninformation)")
                xbmc.executebuiltin("Container.Refresh")
            else:
                # Timeout or cancel - the install may still land, or auto-update
                # may be disabled in Kodi. Say so instead of going silent.
                dialog.ok(__addon_name__,
                          "Update is still installing in the background.\n"
                          "If nothing happens, update from My add-ons or enable auto-updates.")
    else:
        # Up to date - but without an enabled fast-track repository the NEXT
        # update will never arrive; say so now instead of a clean bill of health.
        if repo_state != "enabled":
            state_word = "disabled" if repo_state == "disabled" else "not installed"
            if dialog.yesno(__addon_name__,
                            f"Up to date - [B]v{current_version}[/B] is the latest version.\n"
                            f"Fast-track repository {state_word} - future updates will NOT arrive automatically.\n"
                            f"Show how to enable fast-track updates?"):
                show_fast_track_instructions(dialog, repo_state)
        else:
            dialog.ok(__addon_name__, f"Up to date - [B]v{current_version}[/B] is the latest version.")


if __name__ == "__main__":
    check_updates()
