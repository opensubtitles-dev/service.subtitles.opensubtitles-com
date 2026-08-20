"""Covers test_connection.py as the SINGLE WRITER of account state (v2.0.0).

Architecture decision 2026-08-19: the background service never writes account_*
settings - credentials validation, quota, VIP flag and AI credits are refreshed
exclusively by the Test Connection button. These tests pin that contract.
"""
from unittest.mock import MagicMock, patch

import xbmcaddon

import test_connection as probe


def _creds(user="4ge", password="pass"):
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", user)
    addon.setSetting("OSpass", password)
    addon.setSetting("APIKey", "key")
    return addon


def test_success_refreshes_everything_including_ai_credits():
    addon = _creds()
    provider = MagicMock()
    provider.get_user_info.return_value = {"level": "Sub-leecher", "vip": False,
                                           "remaining_downloads": 47, "allowed_downloads": 50,
                                           "downloads_count": 3}
    provider.get_ai_credits.return_value = 120

    with patch("test_connection.OpenSubtitlesProvider", return_value=provider), \
         patch("test_connection.xbmcgui.Dialog", return_value=MagicMock()):
        probe.test_connection()

    provider.get_ai_credits.assert_called_once()   # credits ALWAYS re-fetched, never cached
    assert addon.getSetting("account_status") == "Free account"
    assert addon.getSetting("account_logged_in") == "true"
    assert addon.getSetting("account_is_vip") == "false"
    assert addon.getSetting("ai_credits").startswith("120")   # "120  [ BUY AI CREDITS ]"
    assert "47/50" in addon.getSetting("account_details")


def test_vip_success_sets_vip_state():
    addon = _creds()
    provider = MagicMock()
    provider.get_user_info.return_value = {"level": "VIP Member", "vip": True,
                                           "remaining_downloads": 995, "allowed_downloads": 1000,
                                           "downloads_count": 5}
    provider.get_ai_credits.return_value = 2019

    with patch("test_connection.OpenSubtitlesProvider", return_value=provider), \
         patch("test_connection.xbmcgui.Dialog", return_value=MagicMock()):
        probe.test_connection()

    assert addon.getSetting("account_status") == "OK (VIP)"
    assert addon.getSetting("account_is_vip") == "true"
    assert addon.getSetting("ai_credits").startswith("2019")


def test_wrong_password_marks_not_logged_in_and_hides_stale_data():
    from resources.lib.exceptions import AuthenticationError

    addon = _creds(password="wrong")
    addon.setSetting("account_is_vip", "true")     # previous user's leftovers
    addon.setSetting("ai_credits", "2019")
    addon.setSetting("account_logged_in", "true")

    with patch("test_connection.OpenSubtitlesProvider") as provider_class, \
         patch("test_connection.xbmcgui.Dialog", return_value=MagicMock()):
        provider_class.return_value.login.side_effect = AuthenticationError("401")
        probe.test_connection()

    assert addon.getSetting("account_logged_in") == "false"   # Register reappears
    assert addon.getSetting("account_is_vip") == "false"
    assert addon.getSetting("ai_credits") == "Sign in to view"
    assert addon.getSetting("account_status") == "Error 401 (Invalid credentials)"


def test_missing_credentials_marks_not_logged_in():
    addon = _creds(user="", password="")
    addon.setSetting("account_logged_in", "true")

    with patch("test_connection.xbmcgui.Dialog", return_value=MagicMock()):
        probe.test_connection()

    assert addon.getSetting("account_logged_in") == "false"
    assert addon.getSetting("ai_credits") == "Sign in to view"
