import pytest
from unittest.mock import patch, MagicMock
import xbmcaddon
import xbmcgui
import time
import os

import resources.lib.background_service as service_monitor
from resources.lib.background_service import (
    OpenSubtitlesMonitor,
    OpenSubtitlesPlayer,
    run_service
)


def test_monitor_settings_changed():
    player = MagicMock()
    monitor = OpenSubtitlesMonitor(player)
    with patch("resources.lib.background_service.threading.Thread") as thread:
        monitor.onSettingsChanged()
    player.reload_settings.assert_called_once()
    # Only the read-only display reconciler may be spawned - never a validator
    # that would hit the API (Test Connection is the single credential writer).
    assert thread.call_count == 1
    assert thread.call_args.kwargs["target"] is service_monitor._reconcile_account_display


def test_player_reload_settings():
    addon = xbmcaddon.Addon()
    addon.setSetting("auto_download", "true")
    addon.setSetting("prompt_rating", "true")

    player = OpenSubtitlesPlayer()
    player.reload_settings()

    assert player.auto_download_enabled is True
    assert player.prompt_rating_enabled is True


def test_player_av_started_auto_download_disabled():
    addon = xbmcaddon.Addon()
    addon.setSetting("auto_download", "false")

    player = OpenSubtitlesPlayer()
    player.isPlayingVideo = MagicMock(return_value=True)

    with patch("resources.lib.background_service.get_media_data") as mock_media:
        player.onAVStarted()
        mock_media.assert_not_called()


def test_player_av_started_auto_download_success(tmp_path):
    addon = xbmcaddon.Addon()
    addon.setSetting("auto_download", "true")
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

    def sync_thread(target=None, args=(), kwargs=None, daemon=True):
        target(*args, **(kwargs or {}))
        return MagicMock()

    with patch("resources.lib.background_service.get_media_data", return_value=mock_media), \
         patch("resources.lib.background_service.get_file_path", return_value="/movies/Inception.2010.1080p.mkv"), \
         patch("resources.lib.background_service.OpenSubtitlesProvider.search_subtitles", return_value=mock_subs), \
         patch("resources.lib.background_service.OpenSubtitlesProvider.download_subtitle", return_value=mock_download_res), \
         patch("xbmcvfs.translatePath", return_value=temp_sub_dir), \
         patch("xbmcgui.Dialog", return_value=mock_dialog_inst), \
         patch("resources.lib.background_service.threading.Thread", side_effect=sync_thread):

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
    mock_dialog_inst.select.return_value = 3       # "4 - Good"
    mock_dialog_inst.yesnocustom.return_value = 1  # sync: Yes

    def sync_thread_exec(target=None, args=(), kwargs=None, daemon=True):
        target(*args, **(kwargs or {}))
        return MagicMock()

    with patch("xbmcgui.Dialog", return_value=mock_dialog_inst), \
         patch("resources.lib.background_service.OpenSubtitlesProvider.rate_subtitle", return_value=True) as mock_rate, \
         patch("threading.Thread", side_effect=sync_thread_exec):

        player.onPlayBackEnded()

        mock_dialog_inst.select.assert_called_once()
        labels = mock_dialog_inst.select.call_args[0][1]
        assert len(labels) == 5 and labels[0].endswith("1 - Bad") and labels[4].endswith("5 - Excellent")
        mock_rate.assert_called_once_with("sub_1", 4, sync=True)
        mock_dialog_inst.notification.assert_called_once()
        assert player.active_session is None


def test_service_shutdown_graceful():
    """Verify monitor loop shuts down immediately when abort is requested."""
    with patch("resources.lib.background_service.OpenSubtitlesMonitor.abortRequested", side_effect=[False, True]), \
         patch("resources.lib.background_service.OpenSubtitlesMonitor.waitForAbort", return_value=True), \
         patch("threading.Thread"):
        run_service()




def test_rating_preview_shows_dialog_5s_into_playback_in_dev_mode():
    """test_flag_interceptor ON -> rating dialog preview fires after playback start."""
    import resources.lib.background_service as service_monitor
    addon = xbmcaddon.Addon()
    addon.setSetting("test_flag_interceptor", "true")
    addon.setSetting("auto_download", "false")

    player = OpenSubtitlesPlayer()
    player.isPlayingVideo = MagicMock(return_value=True)
    player.monitor = MagicMock()
    player.monitor.waitForAbort.return_value = False  # 5s elapse without abort

    dialog = MagicMock()
    dialog.select.return_value = 4       # 5 - Excellent
    dialog.yesnocustom.return_value = 1  # sync: Yes

    def sync_thread(target=None, args=(), kwargs=None, daemon=True):
        target(*args, **(kwargs or {}))
        return MagicMock()

    with patch("resources.lib.background_service.xbmcgui.Dialog", return_value=dialog), \
         patch("resources.lib.background_service.OpenSubtitlesProvider.rate_subtitle") as rate, \
         patch("resources.lib.background_service.threading.Thread", side_effect=sync_thread):
        player.onAVStarted()

    player.monitor.waitForAbort.assert_called_with(5)
    dialog.select.assert_called_once()               # the rating list appeared
    assert "Preview" in dialog.select.call_args[0][0]
    dialog.yesnocustom.assert_called_once()          # the sync question appeared
    rate.assert_not_called()                          # preview never submits
    addon.setSetting("test_flag_interceptor", "")     # don't leak into other tests


def test_dialog_snapshot_revert_is_reconciled_from_state_file():
    """Regression: OK dialog save reverted a passed Test Connection to stale 401."""
    import resources.lib.background_service as service_monitor
    addon = xbmcaddon.Addon()
    addon.setSetting("account_status", "Error 401 (Invalid credentials)")  # the revert
    addon.setSetting("account_logged_in", "false")

    truth = {"account_status": "OK (VIP)", "account_logged_in": "true", "ai_credits": "460"}
    with patch("resources.lib.background_service.load_account_state", return_value=truth), \
         patch("resources.lib.background_service.xbmc.getCondVisibility", return_value=False):
        service_monitor._reconcile_account_display()

    assert addon.getSetting("account_status") == "OK (VIP)"
    assert addon.getSetting("account_logged_in") == "true"
    assert addon.getSetting("ai_credits") == "460"
