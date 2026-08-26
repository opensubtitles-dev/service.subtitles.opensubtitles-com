
import os
import re
import sys
import unicodedata

import xbmc
import xbmcaddon
import xbmcgui

from urllib.parse import parse_qsl

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def get_user_agent():
    """The ONE User-Agent for every outbound request (API, guessit, GitHub).

    Policy: a single identity everywhere - "Opensubtitles.com Kodi plugin v<version>".
    tests/test_utilities.py fails the suite if any file hardcodes its own.
    """
    return f"Opensubtitles.com Kodi plugin v{__addon__.getAddonInfo('version')}"


def redact_path(path):
    """A playback path safe for the debug log.

    Streaming and plugin URLs routinely carry access tokens in the query
    string or credentials in the userinfo part - and debug logs are exactly
    what users paste on public forums. Local paths pass through untouched;
    anything with a scheme loses query, fragment and userinfo.
    """
    try:
        s = str(path)
        if "://" not in s:
            return s
        from urllib.parse import urlsplit
        parts = urlsplit(s)
        host = parts.netloc.rsplit("@", 1)[-1]      # drop user:pass@
        redacted = f"{parts.scheme}://{host}{parts.path}"
        if parts.query or parts.fragment or "@" in parts.netloc:
            redacted += "  [query/credentials redacted]"
        return redacted
    except Exception:
        return "[unloggable path]"


def log(module, msg):
    xbmc.log(f"### [{__addon_name__}:{module}] - {msg}", level=xbmc.LOGDEBUG)


_install_origin = None


def get_install_origin():
    """Repository id that installed this add-on, for the X-Kodi-Origin-Repo header.

    Kodi records the installing repository per add-on but exposes it nowhere in
    the Python API - only the addon database has it (installed.origin). Values:
    a repository id ('repository.opensubtitles-com', 'repository.xbmc.org'),
    'zip' for a manual zip install (empty origin in the DB), or 'unknown' when
    the DB cannot be read. Cached per process; read-only connection so we can
    never touch Kodi's DB state.
    """
    global _install_origin
    if _install_origin is None:
        _install_origin = "unknown"
        try:
            import glob
            import sqlite3
            import xbmcvfs
            db_dir = xbmcvfs.translatePath("special://database/")
            dbs = glob.glob(os.path.join(db_dir, "Addons*.db"))
            if dbs:
                # highest schema number = the database this Kodi actually uses
                newest = max(dbs, key=lambda p: int(re.sub(r"\D", "", os.path.basename(p)) or 0))
                con = sqlite3.connect(f"file:{newest}?mode=ro", uri=True)
                row = con.execute("SELECT origin FROM installed WHERE addonID = ?",
                                  (__addon__.getAddonInfo("id"),)).fetchone()
                con.close()
                if row is not None:
                    _install_origin = row[0] or "zip"
        except Exception:
            pass
    return _install_origin


# prints out msg to log and gives Kodi message with msg_id to user if msg_id provided
def error(module, msg_id=None, msg="", detail=""):
    if msg:
        message = msg
    elif msg_id:
        message = __language__(msg_id)
    else:
        message = "Add-on error with empty message"
    log(module, message)
    if msg_id:
        dialog_msg = f"{__language__(2103)}\n{__language__(msg_id)}"
        if detail:
            dialog_msg += f"\n\n[I]{detail}[/I]"
        xbmcgui.Dialog().ok(__addon_name__, dialog_msg)


def get_params(string=""):
    param = []
    if string == "":
        param_string = sys.argv[2][1:]
    else:
        param_string = string

    if len(param_string) >= 2:
        param = dict(parse_qsl(param_string))

    return param


def normalize_string(str_):
    if not str_:
        return ""
    return unicodedata.normalize("NFC", str_)


def check_and_get_account_status():
    """Returns the current account status, checking 24-hour expiration."""
    verified_at = __addon__.getSetting("account_verified_at")
    status = __addon__.getSetting("account_status")

    if not status or not verified_at or verified_at == "0":
        return "Not Verified"

    try:
        import time
        age = time.time() - float(verified_at)
        if age > 86400:  # Older than 24 hours
            expired_status = "Expired (>24h)"
            __addon__.setSetting("account_status", expired_status)
            __addon__.setSetting("account_details", "Click Test Connection to re-verify")
            return expired_status
        return status
    except (ValueError, TypeError):
        return "Not Verified"

