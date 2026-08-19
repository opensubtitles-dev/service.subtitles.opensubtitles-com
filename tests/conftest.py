import sys
from unittest.mock import MagicMock

class MockMonitor:
    def __init__(self):
        self._abort = False

    def abortRequested(self):
        return self._abort

    def waitForAbort(self, timeout=0):
        return self._abort

    def onSettingsChanged(self):
        pass

    def onNotification(self, sender, method, data):
        pass


class MockPlayer:
    def __init__(self):
        self._playing = True

    def isPlayingVideo(self):
        return self._playing

    def getAvailableSubtitleStreams(self):
        return []

    def setSubtitles(self, path):
        pass

    def getTotalTime(self):
        return 7200.0

    def getTime(self):
        return 3600.0

    def onAVStarted(self):
        pass

    def onPlayBackStopped(self):
        pass

    def onPlayBackEnded(self):
        pass


# Create mock objects for Kodi C-extension modules before any resources are imported
if "xbmc" not in sys.modules:
    xbmc_mock = MagicMock()
    xbmc_mock.LOGDEBUG = 0
    xbmc_mock.LOGINFO = 1
    xbmc_mock.LOGWARNING = 2
    xbmc_mock.LOGERROR = 3
    xbmc_mock.LOGFATAL = 4
    xbmc_mock.log = MagicMock()
    xbmc_mock.getInfoLabel = MagicMock(return_value="")
    xbmc_mock.executebuiltin = MagicMock()
    xbmc_mock.Monitor = MockMonitor
    xbmc_mock.Player = MockPlayer
    sys.modules["xbmc"] = xbmc_mock

if "xbmcaddon" not in sys.modules:
    class MockAddon:
        _settings = {
            "OSuser": "test_user",
            "OSpass": "test_pass",
            "APIKey": "mock_api_key",
            "hearing_impaired": "include",
            "foreign_parts_only": "include",
            "machine_translated": "exclude",
            "ai_translated": "include",
            "search_cache_duration": "180"
        }

        def __init__(self, addon_id="service.subtitles.opensubtitles-com"):
            self.addon_id = addon_id

        def getAddonInfo(self, key):
            info = {
                "id": "service.subtitles.opensubtitles-com",
                "name": "OpenSubtitles.com",
                "version": "1.0.14",
                "path": "/mock/path/service.subtitles.opensubtitles-com"
            }
            return info.get(key, "")

        def getSetting(self, key):
            return self._settings.get(key, "")

        def setSetting(self, key, value):
            self._settings[key] = str(value)

        def getLocalizedString(self, string_id):
            return f"String_{string_id}"

    xbmcaddon_mock = MagicMock()
    xbmcaddon_mock.Addon = MockAddon
    sys.modules["xbmcaddon"] = xbmcaddon_mock


if "xbmcgui" not in sys.modules:
    class MockWindow:
        _storage = {}

        def __init__(self, window_id=10000):
            self.window_id = window_id

        def getProperty(self, key):
            return self._storage.get(key, "")

        def setProperty(self, key, value):
            self._storage[key] = str(value)

        def clearProperty(self, key):
            self._storage.pop(key, None)

    xbmcgui_mock = MagicMock()
    xbmcgui_mock.Window = MockWindow
    xbmcgui_mock.Dialog = MagicMock()
    xbmcgui_mock.ListItem = MagicMock()
    sys.modules["xbmcgui"] = xbmcgui_mock

if "xbmcvfs" not in sys.modules:
    xbmcvfs_mock = MagicMock()
    xbmcvfs_mock.translatePath = lambda p: p.replace("special://home", "/mock/kodi_home").replace("special://temp", "/mock/temp")
    xbmcvfs_mock.exists = MagicMock(return_value=True)
    sys.modules["xbmcvfs"] = xbmcvfs_mock

if "xbmcplugin" not in sys.modules:
    xbmcplugin_mock = MagicMock()
    sys.modules["xbmcplugin"] = xbmcplugin_mock

import pytest

@pytest.fixture(autouse=True)
def reset_mock_state():
    """Reset shared mock settings and window properties before every test."""
    sys.modules["xbmcaddon"].Addon._settings = {
        "OSuser": "test_user",
        "OSpass": "test_pass",
        "APIKey": "mock_api_key",
        "hearing_impaired": "include",
        "foreign_parts_only": "include",
        "machine_translated": "exclude",
        "ai_translated": "include",
        "search_cache_duration": "180"
    }
    sys.modules["xbmcgui"].Window._storage = {}

