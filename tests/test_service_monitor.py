import pytest
from unittest.mock import patch, MagicMock
import xbmcaddon
import xbmcgui
import time
import os

from service_monitor import (
    OpenSubtitlesMonitor,
    OpenSubtitlesPlayer,
    run_service
)


def test_monitor_settings_changed():
    player = MagicMock()
    monitor = OpenSubtitlesMonitor(player)
    monitor.onSettingsChanged()
    player.reload_settings.assert_called_once()


def test_player_reload_settings():
    addon = xbmcaddon.Addon()
    addon.setSetting("auto_download", "true")
    addon.setSetting("auto_download_notify", "false")
    addon.setSetting("prompt_rating", "true")

    player = OpenSubtitlesPlayer()
    player.reload_settings()

    assert player.auto_download_enabled is True
    assert player.auto_download_notify is False
    assert player.prompt_rating_enabled is True


def test_player_av_started_auto_download_disabled():
    addon = xbmcaddon.Addon()
    addon.setSetting("auto_download", "false")

    player = OpenSubtitlesPlayer()
    player.isPlayingVideo = MagicMock(return_value=True)

    with patch("service_monitor.get_media_data") as mock_media:
        player.onAVStarted()
        mock_media.assert_not_called()


def test_player_av_started_auto_download_success(tmp_path):
    addon = xbmcaddon.Addon()
    addon.setSetting("auto_download", "true")
    addon.setSetting("auto_download_notify", "true")
    addon.setSetting("OSuser", "testuser")
    addon.setSetting("OSpass", "testpass")
    addon.setSetting("APIKey", "testkey")

    player = OpenSubtitlesPlayer()
    player.isPlayingVideo = MagicMock(return_value=True)
    player.getAvailableSubtitleStreams = MagicMock(return_value=[])
    player.setSubtitles = MagicMock()
    player.getTotalTime = MagicMock(return_value=7200.0)

    mock_media = {
        "query": "Inception",
        "year": "2010",
        "languages": "en"
    }

    mock_subs = [
        {
            "id": "sub_1",
            "_match_score": 5000.0,
            "attributes": {
                "release": "Inception.2010.1080p.BluRay-FLUX",
                "language": "en",
                "files": [{"file_id": 12345}]
            }
        }
    ]

    mock_download_res = {"content": b"1\n00:00:01,000 --> 00:00:04,000\nHello World\n"}

    temp_sub_dir = str(tmp_path)
    mock_dialog_inst = MagicMock()
    with patch("service_monitor.get_media_data", return_value=mock_media), \
         patch("service_monitor.get_file_path", return_value="/movies/Inception.2010.1080p.mkv"), \
         patch("service_monitor.OpenSubtitlesProvider.search_subtitles", return_value=mock_subs), \
         patch("service_monitor.OpenSubtitlesProvider.download_subtitle", return_value=mock_download_res), \
         patch("xbmcvfs.translatePath", return_value=temp_sub_dir), \
         patch("xbmcgui.Dialog", return_value=mock_dialog_inst):

        player.onAVStarted()

        player.setSubtitles.assert_called_once()
        mock_dialog_inst.notification.assert_called_once()
        assert player.active_session is not None
        assert player.active_session["file_id"] == 12345
        assert player.active_session["title"] == "Inception"


def test_player_playback_ended_rating_prompt():
    addon = xbmcaddon.Addon()
    addon.setSetting("prompt_rating", "true")
    addon.setSetting("OSuser", "testuser")
    addon.setSetting("OSpass", "testpass")
    addon.setSetting("APIKey", "testkey")

    player = OpenSubtitlesPlayer()
    player.prompt_rating_enabled = True
    player.active_session = {
        "file_id": 12345,
        "subtitle_id": "sub_1",
        "release": "Inception.2010.1080p.BluRay-FLUX",
        "title": "Inception",
        "start_time": time.time() - 3600, # Watched for 1 hour
        "total_time": 7200 # 2 hour movie (50% watched)
    }

    mock_dialog_inst = MagicMock()
    mock_dialog_inst.yesno.return_value = True

    with patch("xbmcgui.Dialog", return_value=mock_dialog_inst), \
         patch("service_monitor.OpenSubtitlesProvider.vote_subtitle", return_value=True) as mock_vote, \
         patch("threading.Thread") as mock_thread:

        def sync_thread_exec(target, daemon=True):
            target()
            return MagicMock()

        mock_thread.side_effect = sync_thread_exec

        player.onPlayBackEnded()

        mock_dialog_inst.yesno.assert_called_once()
        mock_vote.assert_called_once_with(12345, 5)
        mock_dialog_inst.notification.assert_called_once()
        assert player.active_session is None


def test_service_shutdown_graceful():
    """Verify monitor loop shuts down immediately when abort is requested."""
    with patch("service_monitor.OpenSubtitlesMonitor.abortRequested", side_effect=[False, True]), \
         patch("service_monitor.OpenSubtitlesMonitor.waitForAbort", return_value=True), \
         patch("threading.Thread"):
        run_service()


def test_check_and_refresh_account_status_success():
    from service_monitor import check_and_refresh_account_status
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "testuser")
    addon.setSetting("OSpass", "testpass")
    addon.setSetting("APIKey", "testkey")
    addon.setSetting("account_verified_at", "0") # Stale

    mock_user_info = {
        "level": "VIP Member",
        "vip": True,
        "remaining_downloads": 995,
        "allowed_downloads": 1000,
        "downloads_count": 5
    }

    with patch("service_monitor.OpenSubtitlesProvider.login"), \
         patch("service_monitor.OpenSubtitlesProvider.get_user_info", return_value=mock_user_info):
        check_and_refresh_account_status(force=True)

        assert addon.getSetting("account_status") == "OK (VIP)"
        assert "995/1000" in addon.getSetting("account_details")
        assert addon.getSetting("account_verified_at") != "0"


def test_check_and_refresh_account_status_fresh_skipped():
    from service_monitor import check_and_refresh_account_status
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "testuser")
    addon.setSetting("OSpass", "testpass")
    addon.setSetting("APIKey", "testkey")
    # Freshly checked 1 hour ago
    addon.setSetting("account_verified_at", str(time.time() - 3600))
    addon.setSetting("account_status", "OK (VIP)")

    with patch("service_monitor.OpenSubtitlesProvider.login") as mock_login:
        check_and_refresh_account_status(force=False)
        # Should skip network request because status is fresh
        mock_login.assert_not_called()

