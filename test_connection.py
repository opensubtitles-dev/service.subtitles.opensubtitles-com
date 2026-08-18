from datetime import datetime
from requests.exceptions import RequestException

import xbmc
import xbmcgui
import xbmcaddon

from resources.lib.exceptions import (
    AuthenticationError,
    BadUsernameError,
    ConfigurationError,
    ProviderError,
    ServiceUnavailable,
    TooManyRequests,
)
from resources.lib.osclient.provider import OpenSubtitlesProvider

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def test_connection():
    username = __addon__.getSetting("OSuser")
    password = __addon__.getSetting("OSpass")
    api_key = __addon__.getSetting("APIKey")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not username or not password:
        __addon__.setSetting("account_status", f"Missing credentials - Checked: {now_str}")
        __addon__.setSetting("account_verified_at", "0")
        xbmcgui.Dialog().ok(__addon_name__, __language__(32012))
        return

    try:
        provider = OpenSubtitlesProvider(api_key, username, password)
        provider.login()
        user_info = provider.get_user_info()
    except AuthenticationError as e:
        __addon__.setSetting("account_status", f"Error 401: Invalid credentials - Checked: {now_str}")
        __addon__.setSetting("account_verified_at", "0")
        xbmcgui.Dialog().ok(__addon_name__, f"{__language__(32003)}\n\n[I]{e}[/I]")
        return
    except BadUsernameError as e:
        __addon__.setSetting("account_status", f"Error 400: Use username, not email - Checked: {now_str}")
        __addon__.setSetting("account_verified_at", "0")
        xbmcgui.Dialog().ok(__addon_name__, __language__(32214))
        return
    except TooManyRequests as e:
        __addon__.setSetting("account_status", f"Error 429: Rate limit exceeded - Checked: {now_str}")
        __addon__.setSetting("account_verified_at", "0")
        xbmcgui.Dialog().ok(__addon_name__, f"{__language__(32007)}\n\n[I]{e}[/I]")
        return
    except ServiceUnavailable as e:
        __addon__.setSetting("account_status", f"Error: Server/Network issue - Checked: {now_str}")
        __addon__.setSetting("account_verified_at", "0")
        xbmcgui.Dialog().ok(__addon_name__, f"{__language__(32008)}\n\n[I]{e}[/I]")
        return
    except (ConfigurationError, ProviderError, RequestException) as e:
        __addon__.setSetting("account_status", f"Error: {e} - Checked: {now_str}")
        __addon__.setSetting("account_verified_at", "0")
        xbmcgui.Dialog().ok(__addon_name__, str(e))
        return

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")
    now_epoch = int(now.timestamp())

    level = user_info.get("level", "User")
    vip = "Yes" if user_info.get("vip") else "No"
    remaining = user_info.get("remaining_downloads", "N/A")
    allowed = user_info.get("allowed_downloads", "N/A")
    downloads_count = user_info.get("downloads_count", "N/A")

    vip_badge = "VIP" if user_info.get("vip") else level
    status_text = f"OK: {vip_badge} | {remaining}/{allowed} left | Checked: {now_str}"
    __addon__.setSetting("account_status", status_text)
    __addon__.setSetting("account_verified_at", str(now_epoch))

    version = __addon__.getAddonInfo("version")
    info_text = (
        f"Username: {username}\n"
        f"Level: {level}  |  VIP: {vip}\n"
        f"Downloads today: {downloads_count} / {allowed}\n"
        f"Remaining downloads: {remaining}"
    )

    xbmcgui.Dialog().ok(f"{__addon_name__} v{version}", info_text)


if __name__ == "__main__":
    try:
        test_connection()
    finally:
        # Kodi saved the settings and closed the dialog before starting this script (see
        # <close> in settings.xml), which is what lets us read credentials the user has only
        # just typed. Put them back where they were once they dismiss the result.
        xbmc.executebuiltin(f"Addon.OpenSettings({__addon__.getAddonInfo('id')})")
