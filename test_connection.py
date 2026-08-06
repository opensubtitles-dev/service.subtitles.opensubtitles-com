import os
import sys

import xbmcaddon
import xbmcvfs

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")

# Kodi launches this file with RunScript(<file path>), which it treats as a script "invoked
# without an addon". It then appends *every* installed add-on's library directory to sys.path
# and puts ours last. Any other add-on shipping a top-level `resources` package therefore wins
# `import resources`, and our own submodules become invisible:
#   ModuleNotFoundError: No module named 'resources.lib.osclient'
# even when the add-on is installed correctly (issue #39, support ticket #168978).
# Put our own directory first, and drop any `resources` already bound, before importing ours.
_addon_path = xbmcvfs.translatePath(__addon__.getAddonInfo("path"))
sys.path = [p for p in sys.path if os.path.normpath(p) != os.path.normpath(_addon_path)]
sys.path.insert(0, _addon_path)
for _module in [m for m in list(sys.modules) if m == "resources" or m.startswith("resources.")]:
    del sys.modules[_module]

import xbmcgui
from requests import RequestException

from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.exceptions import (
    AuthenticationError,
    BadUsernameError,
    ConfigurationError,
    ProviderError,
    ServiceUnavailable,
    TooManyRequests,
)

__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def test_connection():
    username = __addon__.getSetting("OSuser")
    password = __addon__.getSetting("OSpass")
    api_key = __addon__.getSetting("APIKey")

    if not username or not password:
        xbmcgui.Dialog().ok(__addon_name__, __language__(32012))
        return

    try:
        provider = OpenSubtitlesProvider(api_key, username, password)
        provider.login()
        user_info = provider.get_user_info()
    except AuthenticationError:
        xbmcgui.Dialog().ok(__addon_name__, __language__(32003))
        return
    except BadUsernameError:
        xbmcgui.Dialog().ok(__addon_name__, __language__(32214))
        return
    except TooManyRequests:
        xbmcgui.Dialog().ok(__addon_name__, __language__(32007))
        return
    except ServiceUnavailable:
        xbmcgui.Dialog().ok(__addon_name__, __language__(32008))
        return
    except (ConfigurationError, ProviderError, RequestException) as e:
        xbmcgui.Dialog().ok(__addon_name__, str(e))
        return

    level = user_info.get("level", "N/A")
    vip = "Yes" if user_info.get("vip") else "No"
    remaining = user_info.get("remaining_downloads", "N/A")
    allowed = user_info.get("allowed_downloads", "N/A")
    downloads_count = user_info.get("downloads_count", "N/A")

    info_text = (
        f"Username: {username}\n"
        f"Level: {level}  |  VIP: {vip}\n"
        f"Downloads today: {downloads_count} / {allowed}\n"
        f"Remaining downloads: {remaining}"
    )

    xbmcgui.Dialog().ok(__language__(32011), info_text)


if __name__ == "__main__":
    test_connection()
