import pytest
from unittest.mock import patch, MagicMock
from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.data_collector import get_language_data
from resources.lib.exceptions import AuthenticationError, BadUsernameError, TooManyRequests, ServiceUnavailable
import xbmcaddon

def test_search_cache_duration_setting_caching_behavior():
    """Verify that search_cache_duration > 0 caches results and avoids duplicate network requests."""
    addon = xbmcaddon.Addon()
    addon.setSetting("search_cache_duration", "5")  # 5 minutes

    provider = OpenSubtitlesProvider(api_key="test_api_key", username="", password="")

    with patch.object(provider.session, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {
                    "id": "123",
                    "attributes": {
                        "release": "Test.Release.2024",
                        "language": "en"
                    }
                }
            ]
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        # First search: cache miss -> queries network
        results1 = provider.search_subtitles({"query": "Dune", "languages": "en"})
        assert results1 is not None
        assert len(results1) == 1
        assert mock_get.call_count == 1

        # Second identical search: cache hit -> returns cached data, NO new network request
        results2 = provider.search_subtitles({"query": "Dune", "languages": "en"})
        assert results2 == results1
        assert mock_get.call_count == 1, "Expected cache hit without issuing a second network request"

def test_search_cache_disabled_when_duration_is_zero():
    """Verify that search_cache_duration = 0 disables caching completely."""
    addon = xbmcaddon.Addon()
    addon.setSetting("search_cache_duration", "0")  # Disabled

    provider = OpenSubtitlesProvider(api_key="test_api_key", username="", password="")

    with patch.object(provider.session, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"id": "456", "attributes": {"release": "Avatar"}}]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        # First search
        provider.search_subtitles({"query": "Avatar", "languages": "en"})
        assert mock_get.call_count == 1

        # Second search: caching is disabled -> queries network again
        provider.search_subtitles({"query": "Avatar", "languages": "en"})
        assert mock_get.call_count == 2, "Expected second network request when search_cache_duration=0"

def test_filter_settings_propagation_in_data_collector():
    """Verify that filter settings from settings.xml are correctly mapped in get_language_data."""
    addon = xbmcaddon.Addon()
    addon.setSetting("hearing_impaired", "only")
    addon.setSetting("foreign_parts_only", "exclude")
    addon.setSetting("machine_translated", "include")
    addon.setSetting("ai_translated", "exclude")

    params = {"languages": "English"}
    lang_data = get_language_data(params)

    assert lang_data["hearing_impaired"] == "only"
    assert lang_data["foreign_parts_only"] == "exclude"
    assert lang_data["machine_translated"] == "include"
    assert lang_data["ai_translated"] == "exclude"
    assert lang_data["languages"] == "en"

def test_account_status_updated_on_test_connection():
    """Verify that test_connection updates account_status with verification status and timestamp."""
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "test_user")
    addon.setSetting("OSpass", "test_pass")
    
    from test_connection import test_connection
    
    with patch("test_connection.OpenSubtitlesProvider") as mock_provider_class, \
         patch("test_connection.xbmcgui.Dialog"):
        mock_instance = MagicMock()
        mock_instance.get_user_info.return_value = {
            "vip": True,
            "level": "OpenSubtitles Legends",
            "remaining_downloads": 993,
            "allowed_downloads": 1000,
            "downloads_count": 7
        }
        mock_provider_class.return_value = mock_instance
        
        test_connection()
        
        status = addon.getSetting("account_status")
        details = addon.getSetting("account_details")
        checked_at = addon.getSetting("account_checked_at")
        assert status == "OK (VIP)"
        assert details == "Quota: 993/1000 left | Level: OpenSubtitles Legends"
        assert len(checked_at) >= 10

def test_test_connection_empty_credentials():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "")
    addon.setSetting("OSpass", "")
    from test_connection import test_connection
    with patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        assert addon.getSetting("account_status") == "Not Verified (Missing credentials)"
        assert addon.getSetting("account_details") == "Please enter username and password"
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_401_invalid_credentials():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "wrong_user")
    addon.setSetting("OSpass", "wrong_pass")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=AuthenticationError("401 Unauthorized")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        assert addon.getSetting("account_status") == "Error 401 (Invalid credentials)"
        assert addon.getSetting("account_details") == "Check username and password"
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_400_bad_username():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user@example.com")
    addon.setSetting("OSpass", "password")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=BadUsernameError("400 Bad Request")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        assert addon.getSetting("account_status") == "Error 400 (Bad username)"
        assert addon.getSetting("account_details") == "Use username, not email address"
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_429_rate_limit():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user")
    addon.setSetting("OSpass", "pass")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=TooManyRequests("429 Too Many Requests")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        assert addon.getSetting("account_status") == "Error 429 (Rate limit exceeded)"
        assert addon.getSetting("account_details") == "Please wait before trying again"
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_500_503_server_error():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user")
    addon.setSetting("OSpass", "pass")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=ServiceUnavailable("503 Service Unavailable")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        assert addon.getSetting("account_status") == "Error (Server/Network issue)"
        assert addon.getSetting("account_details") == "OpenSubtitles.com is currently unreachable"
        assert addon.getSetting("account_verified_at") == "0"


def test_kodi_preferred_language_priority_ordering():
    from resources.lib.subtitle_downloader import SubtitleDownloader

    addon = xbmcaddon.Addon()
    addon.setSetting("smart_ranking", "true")

    # When Kodi passes preferredlanguage=English with languages=Czech,English,Spanish
    test_argv = ["plugin://service.subtitles.opensubtitles-com/", "1", "?action=search&languages=Czech%2cEnglish%2cSpanish&preferredlanguage=English"]
    with patch("sys.argv", test_argv), \
         patch("resources.lib.subtitle_downloader.get_file_path", return_value="/movies/Test.Movie.2024.1080p.mkv"), \
         patch("resources.lib.subtitle_downloader.get_file_data", return_value={"filename": "Test.Movie.2024.1080p.mkv", "basename": "Test.Movie.2024.1080p.mkv"}), \
         patch("resources.lib.subtitle_downloader.get_media_data", return_value={"query": "Test Movie"}), \
         patch("resources.lib.subtitle_downloader._call_guessit_api", return_value=None), \
         patch("resources.lib.subtitle_downloader.xbmcgui.DialogProgressBG"):
        sd = SubtitleDownloader()
        sd.search()

    # Preferred language (English) must be placed #1, followed by Czech and Spanish
    assert sd.preferred_languages == ["en", "cs", "es"]


def test_adaptive_language_memory():
    import xbmcgui
    from resources.lib.subtitle_downloader import SubtitleDownloader

    win = xbmcgui.Window(10000)
    win.setProperty("os_com:last_downloaded_lang", "sk")  # User previously downloaded Slovak

    # Kodi requests Czech, English, Slovak (with preferredlanguage=Czech)
    test_argv = ["plugin://service.subtitles.opensubtitles-com/", "1", "?action=search&languages=Czech%2cEnglish%2cSlovak&preferredlanguage=Czech"]
    with patch("sys.argv", test_argv), \
         patch("resources.lib.subtitle_downloader.get_file_path", return_value="/movies/Test.Movie.2024.1080p.mkv"), \
         patch("resources.lib.subtitle_downloader.get_file_data", return_value={"filename": "Test.Movie.2024.1080p.mkv", "basename": "Test.Movie.2024.1080p.mkv"}), \
         patch("resources.lib.subtitle_downloader.get_media_data", return_value={"query": "Test Movie"}), \
         patch("resources.lib.subtitle_downloader._call_guessit_api", return_value=None), \
         patch("resources.lib.subtitle_downloader.xbmcgui.DialogProgressBG"):
        sd = SubtitleDownloader()
        sd.search()

    # Adaptive Language Memory promotes Slovak (sk) to #1 ahead of Czech and English!
    assert sd.preferred_languages == ["sk", "cs", "en"]


def test_hearing_impaired_kodi_setting_reflection():
    from resources.lib.data_collector import get_language_data, is_kodi_hearing_impaired_preferred
    from resources.lib.matcher import rank_subtitles

    addon = xbmcaddon.Addon()
    addon.setSetting("hearing_impaired", "exclude")

    # When Kodi system setting for hearing impaired is enabled
    mock_jsonrpc = '{"id": 1, "jsonrpc": "2.0", "result": {"value": true}}'
    with patch("xbmc.executeJSONRPC", return_value=mock_jsonrpc):
        assert is_kodi_hearing_impaired_preferred() is True
        
        lang_data = get_language_data({"languages": "English", "preferredlanguage": "English"})
        # Should automatically switch from default exclude to include
        assert lang_data["hearing_impaired"] == "include"

    # Ranking test: HI subtitle gets boosted when prefer_hearing_impaired=True
    sub_regular = {"id": "1", "attributes": {"release": "Movie.1080p.BluRay-FLUX", "hearing_impaired": False}}
    sub_hi = {"id": "2", "attributes": {"release": "Movie.1080p.BluRay-FLUX", "hearing_impaired": True}}

    ranked = rank_subtitles([sub_regular, sub_hi], "Movie.1080p.BluRay-FLUX.mkv", prefer_hearing_impaired=True)
    assert ranked[0]["id"] == "2", "Hearing impaired subtitle should rank #1 when user prefers HI"


def test_get_language_data_missing_languages_param():
    """A search invocation with no languages parameter must not raise -
    unquote(None) was a TypeError that aborted the whole search."""
    lang_data = get_language_data({})
    assert isinstance(lang_data, dict)
    assert "languages" in lang_data


def test_translation_filters_never_send_only():
    """The API accepts include/exclude for machine_translated/ai_translated;
    a stored 'only' from the old UI must map to include, not break requests."""
    addon = xbmcaddon.Addon()
    addon.setSetting("machine_translated", "only")
    addon.setSetting("ai_translated", "only")
    lang_data = get_language_data({"languages": "English"})
    assert lang_data["machine_translated"] == "include"
    assert lang_data["ai_translated"] == "include"


def test_settings_xml_offers_no_only_for_translation_filters():
    import os, re
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    xml = open(os.path.join(repo, "resources", "settings.xml"), encoding="utf-8").read()
    for setting_id in ("machine_translated", "ai_translated"):
        block = xml.split(f'<setting id="{setting_id}"')[1].split("</setting>")[0]
        assert ">only<" not in block, f"{setting_id} must not offer 'only'"


def test_guessit_failure_log_hides_url(monkeypatch):
    import xbmc
    from unittest.mock import patch
    from resources.lib import data_collector

    logged = []
    import urllib.request
    with patch.object(urllib.request, "urlopen",
                      side_effect=Exception("HTTP Error at https://api.opensubtitles.com/utilities/guessit?filename=SECRET-NAME.mkv")), \
         patch.object(xbmc, "log", side_effect=lambda msg, level=0: logged.append(str(msg))):
        result = data_collector._call_guessit_api("SECRET-NAME.mkv")
    assert result is None
    assert "SECRET-NAME" not in "".join(l for l in logged if "Failed to call" in l)
