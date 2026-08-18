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
        assert status.startswith("OK: VIP | 993/1000 left")
        assert "Checked:" in status

def test_test_connection_empty_credentials():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "")
    addon.setSetting("OSpass", "")
    from test_connection import test_connection
    with patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        status = addon.getSetting("account_status")
        assert status.startswith("Missing credentials")
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_401_invalid_credentials():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "wrong_user")
    addon.setSetting("OSpass", "wrong_pass")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=AuthenticationError("401 Unauthorized")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        status = addon.getSetting("account_status")
        assert status.startswith("Error 401: Invalid credentials")
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_400_bad_username():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user@example.com")
    addon.setSetting("OSpass", "password")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=BadUsernameError("400 Bad Request")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        status = addon.getSetting("account_status")
        assert status.startswith("Error 400: Use username, not email")
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_429_rate_limit():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user")
    addon.setSetting("OSpass", "pass")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=TooManyRequests("429 Too Many Requests")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        status = addon.getSetting("account_status")
        assert status.startswith("Error 429: Rate limit exceeded")
        assert addon.getSetting("account_verified_at") == "0"

def test_test_connection_500_503_server_error():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user")
    addon.setSetting("OSpass", "pass")
    from test_connection import test_connection
    with patch("test_connection.OpenSubtitlesProvider.login", side_effect=ServiceUnavailable("503 Service Unavailable")), \
         patch("test_connection.xbmcgui.Dialog"):
        test_connection()
        status = addon.getSetting("account_status")
        assert status.startswith("Error: Server/Network issue")
        assert addon.getSetting("account_verified_at") == "0"
