"""Sync plumbing (docs/subtitle_sync_plan.md): toggle-gated row, honest
engine-pending behavior, delay-nudge detection. The alignment engine itself
arrives from project subsync - these tests cover the socket around it."""
from unittest.mock import patch, MagicMock

import pytest
import xbmcaddon


def test_engine_socket_raises_until_subsync_lands():
    from resources.lib import syncer
    assert syncer.engine_available() is False
    with pytest.raises(syncer.EngineNotAvailable):
        syncer.sync_subtitle("/tmp/x.srt")


def test_toggle_gates_is_enabled():
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("subtitle_sync_enabled", "false")
    assert syncer.is_enabled() is False
    addon.setSetting("subtitle_sync_enabled", "true")
    assert syncer.is_enabled() is True


def test_delay_nudge_fires_exactly_once_past_threshold():
    from resources.lib import syncer
    session = {}
    # baseline + two nudges: not yet
    assert syncer.register_delay_sample(session, "0.000 s") is False
    assert syncer.register_delay_sample(session, "0.250 s") is False
    assert syncer.register_delay_sample(session, "0.500 s") is False
    # third distinct nudge crosses the threshold - fires ONCE
    assert syncer.register_delay_sample(session, "0.750 s") is True
    assert syncer.register_delay_sample(session, "1.000 s") is False
    # repeats of a seen value never count
    session2 = {}
    for _ in range(10):
        assert syncer.register_delay_sample(session2, "0.250 s") is False


def test_sync_row_injected_only_when_enabled():
    from resources.lib.subtitle_downloader import SubtitleDownloader
    import xbmcplugin

    sd = SubtitleDownloader.__new__(SubtitleDownloader)
    sd.params = {"languages": "en"}
    sd.handle = 1
    addon = xbmcaddon.Addon()

    addon.setSetting("subtitle_sync_enabled", "false")
    with patch.object(xbmcplugin, "addDirectoryItem") as add:
        sd._inject_sync_row()
    assert not add.called

    addon.setSetting("subtitle_sync_enabled", "true")
    with patch.object(xbmcplugin, "addDirectoryItem") as add:
        sd._inject_sync_row()
    assert add.called
    assert "action=sync" in add.call_args[1]["url"]


def test_sync_action_shows_coming_soon_and_ends_listing():
    from resources.lib.subtitle_downloader import SubtitleDownloader
    import xbmcplugin, xbmcgui

    sd = SubtitleDownloader.__new__(SubtitleDownloader)
    sd.params = {"action": "sync"}
    sd.handle = 1
    dialog = MagicMock()
    with patch.object(xbmcgui, "Dialog", return_value=dialog), \
         patch("resources.lib.subtitle_downloader.get_file_path", return_value="/m/x.mkv"), \
         patch.object(xbmcplugin, "endOfDirectory") as end:
        sd.sync()
    assert dialog.ok.called, "coming-soon dialog must show"
    assert end.called, "listing must end cleanly"
