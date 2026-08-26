import pytest
from unittest.mock import patch, MagicMock
import xbmcaddon
import xbmcgui

from check_updates import (
    parse_version_tuple,
    extract_remote_version,
    fetch_latest_remote_version,
    check_updates
)

def test_parse_version_tuple():
    assert parse_version_tuple("1.0.15") == (1, 0, 15)
    assert parse_version_tuple("1.0.16.2") == (1, 0, 16, 2)
    assert parse_version_tuple("v2.0.0") == (2, 0, 0)
    assert parse_version_tuple("") == (0, 0, 0)
    assert parse_version_tuple("1.0.16") > parse_version_tuple("1.0.15")


def test_extract_remote_version_single_addon():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <addon id="service.subtitles.opensubtitles-com" version="1.0.16" name="OpenSubtitles.com">
    </addon>"""
    assert extract_remote_version(xml_content) == "1.0.16"


def test_extract_remote_version_repository_addons_xml():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <addons>
        <addon id="repository.opensubtitles-com" version="1.0.0" name="Repository">
        </addon>
        <addon id="service.subtitles.opensubtitles-com" version="1.0.16" name="OpenSubtitles.com">
        </addon>
    </addons>"""
    assert extract_remote_version(xml_content) == "1.0.16"


def test_check_updates_up_to_date():
    addon = xbmcaddon.Addon()

    with patch("check_updates.fetch_latest_remote_version", return_value="1.0.15"), \
         patch.object(addon, "getAddonInfo", return_value="1.0.15"), \
         patch("check_updates.__addon__.getAddonInfo", return_value="1.0.15"), \
         patch("check_updates.xbmcgui.Dialog") as mock_dialog:
        dialog_inst = MagicMock()
        mock_dialog.return_value = dialog_inst

        check_updates()

        dialog_inst.ok.assert_called_once()
        assert "up to date" in dialog_inst.ok.call_args[0][1].lower()


def test_check_updates_newer_version_available():
    addon = xbmcaddon.Addon()

    with patch("check_updates.fetch_latest_remote_version", return_value="1.0.16"), \
         patch.object(addon, "getAddonInfo", return_value="1.0.15"), \
         patch("check_updates.__addon__.getAddonInfo", return_value="1.0.15"), \
         patch("check_updates.xbmc.getCondVisibility", return_value=True), \
         patch("check_updates.xbmcgui.Dialog") as mock_dialog, \
         patch("check_updates.xbmc.executebuiltin") as mock_exec:
        dialog_inst = MagicMock()
        dialog_inst.yesno.return_value = True
        mock_dialog.return_value = dialog_inst

        check_updates()

        dialog_inst.yesno.assert_called_once()
        assert "v1.0.16" in dialog_inst.yesno.call_args[0][1]
        mock_exec.assert_called_with("UpdateAddonRepos")


def test_check_updates_network_failure():
    addon = xbmcaddon.Addon()
    addon.setSetting("addon_version", "1.0.15")

    with patch("check_updates.fetch_latest_remote_version", return_value=None), \
         patch("check_updates.xbmcgui.Dialog") as mock_dialog:
        dialog_inst = MagicMock()
        mock_dialog.return_value = dialog_inst

        check_updates()

        dialog_inst.ok.assert_called_once()
        assert "Could not connect" in dialog_inst.ok.call_args[0][1]


def test_check_updates_without_fast_track_repo_shows_both_versions():
    # Kodi origin pinning: without repository.opensubtitles-com the user cannot
    # receive the fast-track version, so the dialog must show both versions and
    # offer instructions instead of the update prompt.
    with patch("check_updates.fetch_latest_remote_version", return_value="1.0.22"), \
         patch("check_updates.fetch_official_kodi_version", return_value="1.0.16"), \
         patch("check_updates.__addon__.getAddonInfo", return_value="1.0.21"), \
         patch("check_updates.xbmc.getCondVisibility", return_value=False), \
         patch("check_updates.xbmc.executebuiltin") as mock_builtin, \
         patch("check_updates.xbmcgui.Dialog") as mock_dialog:
        dialog_inst = MagicMock()
        dialog_inst.yesno.return_value = False
        mock_dialog.return_value = dialog_inst

        check_updates()

        msg = dialog_inst.yesno.call_args[0][1]
        assert "1.0.22" in msg
        assert "1.0.16" in msg
        mock_builtin.assert_not_called()  # no UpdateAddonRepos without the repo


def test_check_updates_without_fast_track_repo_not_in_official():
    with patch("check_updates.fetch_latest_remote_version", return_value="1.0.22"), \
         patch("check_updates.fetch_official_kodi_version", return_value=None), \
         patch("check_updates.__addon__.getAddonInfo", return_value="1.0.21"), \
         patch("check_updates.xbmc.getCondVisibility", return_value=False), \
         patch("check_updates.xbmcgui.Dialog") as mock_dialog:
        dialog_inst = MagicMock()
        dialog_inst.yesno.return_value = True
        mock_dialog.return_value = dialog_inst

        check_updates()

        assert "not yet available" in dialog_inst.yesno.call_args[0][1]
        dialog_inst.textviewer.assert_called_once()  # instructions on Yes
