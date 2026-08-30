"""Sync plumbing + the live subsync HTTP engine (docs/subtitle_sync_plan.md):
toggle-gated row, service-configured gating, job lifecycle against a mocked
service (contract measured live 2026-08-29), honest low-confidence rejection,
delay-nudge detection."""
from unittest.mock import patch, MagicMock

import pytest
import xbmcaddon


def test_engine_gated_on_configured_service_url():
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "")
    assert syncer.engine_available() is False
    with pytest.raises(syncer.EngineNotAvailable):
        syncer.sync_subtitle("/tmp/x.srt")
    addon.setSetting("sync_service_url", "https://subsync.example")
    assert syncer.engine_available() is True
    addon.setSetting("sync_service_url", "")


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


def test_sync_action_unconfigured_shows_pending_dialog_and_ends_listing():
    from resources.lib.subtitle_downloader import SubtitleDownloader
    import xbmcplugin, xbmcgui

    xbmcaddon.Addon().setSetting("sync_service_url", "")
    sd = SubtitleDownloader.__new__(SubtitleDownloader)
    sd.params = {"action": "sync"}
    sd.handle = 1
    dialog = MagicMock()
    with patch.object(xbmcgui, "Dialog", return_value=dialog), \
         patch.object(xbmcgui, "DialogProgress", return_value=MagicMock()), \
         patch("resources.lib.subtitle_downloader.get_file_path", return_value="/m/x.mkv"), \
         patch.object(xbmcplugin, "endOfDirectory") as end:
        sd.sync()
    assert dialog.ok.called, "engine-pending dialog must show"
    assert end.called, "listing must end cleanly"


def _mock_service(status_flow, transform, warnings=(), sub_body=b"1\n00:00:01,000 --> 00:00:02,000\nHi\n"):
    """requests.post/get mocks speaking the measured subsync contract."""
    post = MagicMock(return_value=MagicMock(
        status_code=202, json=lambda: {"job_id": "j_test"}))
    polls = [MagicMock(status_code=200, json=lambda s=s: {
        "status": s, "stage": "vad", "progress": 0.5, "error": "boom" if s in ("error", "failed") else None,
        "result": ({"transform": transform, "engine_used": "correlate",
                    "subtitle_url": "/v1/jobs/j_test/subtitle",
                    "warnings": list(warnings)} if s == "done" else None)})
             for s in status_flow]
    sub = MagicMock(status_code=200, content=sub_body)
    get = MagicMock(side_effect=polls + [sub])
    return post, get


def test_sync_subtitle_happy_path(tmp_path):
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://subsync.example")
    srt = tmp_path / "a.srt"; srt.write_text("1\n00:00:01,000 --> 00:00:02,000\nx\n")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00" * 32)
    audio = tmp_path / "a.ogg"; audio.write_bytes(b"OggS")
    post, get = _mock_service(["processing", "done"],
                              {"type": "constant", "offset_ms": 130, "scale": 1.0, "confidence": 0.99})
    with patch.object(syncer, "_extract_audio", return_value=str(audio)), \
         patch.object(syncer, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", post), patch("requests.get", get):
        result = syncer.sync_subtitle(str(srt), video_path=str(vid))
    assert result["offset_ms"] == 130
    assert result["fps_scale"] == 1.0
    assert result["method"] == "correlate"
    assert result["path"] != str(srt), "original must never be touched"
    import os
    assert os.path.exists(result["path"])
    addon.setSetting("sync_service_url", "")


def test_sync_subtitle_rejects_low_confidence(tmp_path):
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://subsync.example")
    srt = tmp_path / "a.srt"; srt.write_text("x")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00")
    audio = tmp_path / "a.ogg"; audio.write_bytes(b"OggS")
    post, get = _mock_service(["done"],
                              {"type": "linear", "offset_ms": -187020, "scale": 0.8, "confidence": 0.19},
                              warnings=[{"code": "different_cut_suspected", "message": "low"}])
    with patch.object(syncer, "_extract_audio", return_value=str(audio)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", post), patch("requests.get", get):
        with pytest.raises(syncer.SyncError, match="not confident"):
            syncer.sync_subtitle(str(srt), video_path=str(vid))
    addon.setSetting("sync_service_url", "")


def test_sync_subtitle_surfaces_server_error(tmp_path):
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://subsync.example")
    srt = tmp_path / "a.srt"; srt.write_text("x")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00")
    audio = tmp_path / "a.ogg"; audio.write_bytes(b"OggS")
    post, get = _mock_service(["error"], {})
    with patch.object(syncer, "_extract_audio", return_value=str(audio)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", post), patch("requests.get", get):
        with pytest.raises(syncer.SyncError, match="failed on the server"):
            syncer.sync_subtitle(str(srt), video_path=str(vid))
    addon.setSetting("sync_service_url", "")


def test_env_auth_fallback(tmp_path):
    """Dev convenience: gitignored .env supplies Basic auth until the real
    auth scheme lands; settings always win; malformed file -> None."""
    from resources.lib import syncer
    env = tmp_path / ".env"
    env.write_text("# comment\nSUBSYNC_USER=u1\nSUBSYNC_PASS=p1\nOTHER=x\n")
    assert syncer._read_env_auth(str(env)) == ("u1", "p1")
    env.write_text("OTHER=x\n")
    assert syncer._read_env_auth(str(env)) is None
    assert syncer._read_env_auth(str(tmp_path / "missing")) is None
