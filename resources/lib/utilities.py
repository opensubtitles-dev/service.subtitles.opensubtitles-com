
import sys
import unicodedata

import xbmc
import xbmcaddon
import xbmcgui

from urllib.parse import parse_qsl

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def log(module, msg):
    xbmc.log(f"### [{__addon_name__}:{module}] - {msg}", level=xbmc.LOGDEBUG)


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

