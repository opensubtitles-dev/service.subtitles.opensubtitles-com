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
    with patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": ""}), \
         patch.object(syncer, "_extract_audio", return_value=str(audio)), \
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
    with patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": ""}), \
         patch.object(syncer, "_extract_audio", return_value=str(audio)), \
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
    with patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": ""}), \
         patch.object(syncer, "_extract_audio", return_value=str(audio)), \
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


def test_fingerprint_follows_reference_recipe():
    """/v1/spec recipe: 512-sample chunks, floor+6dB threshold, smoothing,
    10 ms grid, vad tag energy-v1."""
    import base64, json
    from resources.lib import syncer
    # 3000 chunks: alternating runs of 40 loud / 40 quiet (well above the
    # opening/closing scale) - half the timeline is speech
    dbs = ([-60.0] * 40 + [-20.0] * 40) * 38
    samples = len(dbs) * 512
    with patch.object(syncer, "_decode_chunk_db", return_value=(dbs, samples)):
        fp = json.loads(syncer._full_fingerprint("ffmpeg", "/v.mkv"))
    assert fp["v"] == 1 and fp["frame_ms"] == 10
    assert fp["vad"] == "energy-v1"
    assert fp["duration_ms"] == samples // 16
    mask = base64.b64decode(fp["mask_b64"])
    bits = [(mask[i >> 3] >> (7 - (i & 7))) & 1 for i in range(200)]
    # first 40 chunks (1280 ms = 128 frames) are quiet -> zero frames
    assert not any(bits[:120])


def test_chunk_smoothing_opening_and_closing():
    from resources.lib import syncer
    quiet, loud = -60.0, -20.0
    # lone hit dropped (opening 1)
    dec = syncer._chunk_decisions([quiet] * 20 + [loud] + [quiet] * 20)
    assert not any(dec)
    # gap of 8 bridged, gap of 9 not (closing 8)
    dec = syncer._chunk_decisions([loud] * 3 + [quiet] * 8 + [loud] * 3 + [quiet] * 30)
    assert all(dec[:14])
    dec = syncer._chunk_decisions([loud] * 3 + [quiet] * 9 + [loud] * 3 + [quiet] * 30)
    assert not any(dec[3:12])


def test_sparse_fingerprint_for_long_films():
    """>30 min media takes the recipe's sparse option: bisection windows,
    zero mask outside, windows declared in the envelope."""
    import base64, json
    from resources.lib import syncer
    dbs_window = ([-20.0] * 30 + [-60.0] * 30) * 31        # ~60s, half speech
    calls = []
    def fake_decode(ffmpeg, path, progress=None, seek_s=None, dur_s=None):
        calls.append(seek_s)
        return dbs_window, len(dbs_window) * 512
    with patch.object(syncer, "_decode_chunk_db", side_effect=fake_decode):
        fp = json.loads(syncer._sparse_fingerprint("ffmpeg", "/v.mkv", 7200.0))
    assert fp["vad"] == "energy-v1"
    assert fp["duration_ms"] == 7200000
    ws = fp["windows"]
    assert ws == sorted(ws) and len(ws) >= 20   # 20% of 2h in 60s windows
    assert all(e - s == 60000 for s, e in ws)
    assert all(s is not None for s in calls), "sparse must decode windows, not the file"
    # mask must be zero outside the declared windows
    mask = base64.b64decode(fp["mask_b64"])
    def frame(i):
        return (mask[i >> 3] >> (7 - (i & 7))) & 1
    in_any = lambda ms: any(s <= ms < e for s, e in ws)
    for probe_ms in range(0, 7200000, 97010):
        if not in_any(probe_ms):
            assert frame(probe_ms // 10) == 0, f"speech outside windows at {probe_ms}"


def test_fingerprint_fast_path_skips_audio_extraction(tmp_path):
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://subsync.example")
    srt = tmp_path / "a.srt"; srt.write_text("x")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00")
    post, get = _mock_service(["done"],
                              {"type": "constant", "offset_ms": 90, "scale": 1.0, "confidence": 0.99})
    extract = MagicMock()
    with patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": "/usr/bin/ffmpeg"}), \
         patch.object(syncer, "_media_duration_s", return_value=0.0), \
         patch.object(syncer, "_full_fingerprint", return_value='{"v":1}'), \
         patch.object(syncer, "_extract_audio", extract), \
         patch.object(syncer, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", post), patch("requests.get", get):
        result = syncer.sync_subtitle(str(srt), video_path=str(vid))
    assert result["offset_ms"] == 90
    assert not extract.called, "fast path must not extract audio"
    assert "fingerprint" in post.call_args[1]["files"]
    addon.setSetting("sync_service_url", "")


def test_fingerprint_low_confidence_falls_back_to_audio(tmp_path):
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://subsync.example")
    srt = tmp_path / "a.srt"; srt.write_text("x")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00")
    audio = tmp_path / "a.ogg"; audio.write_bytes(b"OggS")
    fp_post, fp_get = _mock_service(["done"],
                                    {"type": "constant", "offset_ms": 0, "scale": 1.0, "confidence": 0.3})
    au_post, au_get = _mock_service(["done"],
                                    {"type": "constant", "offset_ms": 130, "scale": 1.0, "confidence": 0.95})
    posts = MagicMock(side_effect=[fp_post.return_value, au_post.return_value])
    gets = MagicMock(side_effect=list(fp_get.side_effect) + list(au_get.side_effect))
    with patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": "/usr/bin/ffmpeg"}), \
         patch.object(syncer, "_media_duration_s", return_value=0.0), \
         patch.object(syncer, "_full_fingerprint", return_value='{"v":1}'), \
         patch.object(syncer, "_extract_audio", return_value=str(audio)), \
         patch.object(syncer, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", posts), patch("requests.get", gets):
        result = syncer.sync_subtitle(str(srt), video_path=str(vid))
    assert result["offset_ms"] == 130, "audio-tier result must win after weak fingerprint"
    assert posts.call_count == 2
    addon.setSetting("sync_service_url", "")


def _resp(status=200, json_body=None, content=b"", headers=None):
    r = MagicMock(status_code=status, content=content, headers=headers or {})
    r.json.return_value = json_body or {}
    return r


def test_moviehash_instant_path_skips_all_media_work(tmp_path):
    """Server knows the release -> job = moviehash + subtitle only (measured
    0.6 s on production); no hashing of audio, no fingerprint, no extraction."""
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://sync.example")
    srt = tmp_path / "a.srt"; srt.write_text("x")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00")
    done = {"status": "done", "result": {
        "transform": {"type": "constant", "offset_ms": 90, "scale": 1.0, "confidence": 0.99},
        "engine_used": "correlate", "subtitle_url": "/v1/jobs/j/subtitle", "warnings": []}}
    gets = MagicMock(side_effect=[_resp(200, {"known": True}),
                                  _resp(200, done),
                                  _resp(200, content=b"1\n00:00:01,000 --> 00:00:02,000\nx\n")])
    post = MagicMock(return_value=_resp(202, {"job_id": "j"}))
    fp = MagicMock(); extract = MagicMock()
    with patch("resources.lib.file_operations.hash_file", return_value=(1, "6fc5a843e68b5b3f")), \
         patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": "/usr/bin/ffmpeg"}), \
         patch.object(syncer, "_media_duration_s", return_value=0.0), \
         patch.object(syncer, "_full_fingerprint", fp), \
         patch.object(syncer, "_extract_audio", extract), \
         patch.object(syncer, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", post), patch("requests.get", gets):
        result = syncer.sync_subtitle(str(srt), video_path=str(vid))
    assert result["offset_ms"] == 90
    assert not fp.called and not extract.called
    assert post.call_args[1]["data"] == {"moviehash": "6fc5a843e68b5b3f"}
    assert "fingerprint" not in post.call_args[1]["files"]
    addon.setSetting("sync_service_url", "")


def test_moviehash_cache_race_falls_through_to_fingerprint(tmp_path):
    """known:true but the job 422s (moviehash_unknown race) -> fingerprint
    rung runs instead of surfacing the error."""
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://sync.example")
    srt = tmp_path / "a.srt"; srt.write_text("x")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00")
    done = {"status": "done", "result": {
        "transform": {"type": "constant", "offset_ms": 130, "scale": 1.0, "confidence": 0.99},
        "engine_used": "correlate", "subtitle_url": "/v1/jobs/j2/subtitle", "warnings": []}}
    gets = MagicMock(side_effect=[_resp(200, {"known": True}),
                                  _resp(200, done),
                                  _resp(200, content=b"srt")])
    posts = MagicMock(side_effect=[
        _resp(422, {"error": {"code": "moviehash_unknown", "message": "no cached fingerprint"}}),
        _resp(202, {"job_id": "j2"})])
    with patch("resources.lib.file_operations.hash_file", return_value=(1, "aa" * 8)), \
         patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": "/usr/bin/ffmpeg"}), \
         patch.object(syncer, "_media_duration_s", return_value=0.0), \
         patch.object(syncer, "_full_fingerprint", return_value='{"v":1}'), \
         patch.object(syncer, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", posts), patch("requests.get", gets):
        result = syncer.sync_subtitle(str(srt), video_path=str(vid))
    assert result["offset_ms"] == 130
    assert posts.call_count == 2
    assert "fingerprint" in posts.call_args[1]["files"]
    assert posts.call_args[1]["data"] == {"moviehash": "aa" * 8}
    addon.setSetting("sync_service_url", "")


def test_rate_limit_surfaces_retry_after(tmp_path):
    from resources.lib import syncer
    addon = xbmcaddon.Addon()
    addon.setSetting("sync_service_url", "https://sync.example")
    srt = tmp_path / "a.srt"; srt.write_text("x")
    vid = tmp_path / "a.mkv"; vid.write_bytes(b"\x00")
    audio = tmp_path / "a.ogg"; audio.write_bytes(b"OggS")
    gets = MagicMock(return_value=_resp(200, {"known": False}))
    post = MagicMock(return_value=_resp(429, headers={"Retry-After": "42"}))
    with patch("resources.lib.file_operations.hash_file", return_value=(1, "bb" * 8)), \
         patch("resources.lib.transcriber.get_capabilities", return_value={"ffmpeg": ""}), \
         patch.object(syncer, "_extract_audio", return_value=str(audio)), \
         patch.object(syncer, "POLL_SECONDS", 0), \
         patch("requests.post", post), patch("requests.get", gets):
        with pytest.raises(syncer.SyncError, match="42 seconds"):
            syncer.sync_subtitle(str(srt), video_path=str(vid))
    addon.setSetting("sync_service_url", "")
