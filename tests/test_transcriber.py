"""AI transcription pipeline tests (resources/lib/transcriber.py).

Everything mocked - the real API is PROPOSED-only. The mock client makes the
whole pipeline executable, which is exactly what the Development-tab setting
does inside Kodi.
"""
import json
import os
from unittest.mock import patch, MagicMock

import pytest

from resources.lib import transcriber


@pytest.fixture
def profile(tmp_path):
    with patch.object(transcriber, "_profile_dir", return_value=str(tmp_path)):
        yield tmp_path


def test_capabilities_probe_runs_once_and_caches(profile):
    # "test capabilities first, save locally, never run again"
    with patch.object(transcriber, "find_ffmpeg", return_value="/usr/bin/ffmpeg") as ff, \
         patch.object(transcriber, "_benchmark_ffmpeg", return_value=8.5) as bench, \
         patch.object(transcriber, "_benchmark_io", return_value=120.0), \
         patch.object(transcriber.os.path, "exists", return_value=True):
        caps1 = transcriber.get_capabilities()
        caps2 = transcriber.get_capabilities()
    assert caps1["encode_x_realtime"] == 8.5
    assert caps2 == caps1
    assert bench.call_count == 1          # benchmark ran exactly once
    assert json.load(open(profile / "transcription_caps.json"))["schema"] == transcriber.CAPS_SCHEMA


def test_capabilities_cache_invalidates_when_ffmpeg_vanishes(profile):
    (profile / "transcription_caps.json").write_text(json.dumps(
        {"schema": transcriber.CAPS_SCHEMA, "ffmpeg": "/gone/ffmpeg"}))
    with patch.object(transcriber, "find_ffmpeg", return_value=None), \
         patch.object(transcriber, "_benchmark_io", return_value=50.0):
        caps = transcriber.get_capabilities()
    assert caps["ffmpeg"] == ""           # re-probed, not served stale


def test_choose_source_ladder(tmp_path):
    """The rung ladder (docs/audio_extraction_matrix.md): ffmpeg first, then
    the platform-native routes, then pure-Python demux - never a premature
    install hint while a native route remains."""
    from unittest.mock import patch
    import xbmc
    from resources.lib import transcriber

    local = tmp_path / "movie.mkv"
    local.write_bytes(b"x" * 1024)
    fast = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 8.0}
    slow = {"ffmpeg": "", "encode_x_realtime": None}

    with patch.object(xbmc, "getCondVisibility", return_value=False), \
         patch("os.path.exists", side_effect=lambda p: p == str(local)):
        assert transcriber.choose_source(fast, str(local)) == "ffmpeg"
        assert transcriber.choose_source(slow, str(local)) == "pydemux"
        assert transcriber.choose_source(slow, "/gone.mkv") == "too_big"

    # AAC rungs run by default and self-park for 24h when the live server
    # rejects an AAC upload (measured 2026-08-29 - MP3-only today).
    def android(cond):
        return "Android" in cond
    with patch.object(xbmc, "getCondVisibility", side_effect=android):
        assert transcriber.choose_source(slow, str(local)) == "android_ndk"
        transcriber.note_aac_rejected()
        assert transcriber.choose_source(slow, str(local)) == "pydemux"
    import xbmcgui
    xbmcgui.Window(10000).setProperty(transcriber._AAC_REJECTED_PROP, "")

    def osx(cond):
        return "OSX" in cond
    with patch.object(xbmc, "getCondVisibility", side_effect=osx), \
         patch("os.path.exists", side_effect=lambda p: p in (str(local), "/usr/bin/afconvert")):
        assert transcriber.choose_source(slow, str(local)) == "afconvert"
        transcriber.note_aac_rejected()
        assert transcriber.choose_source(slow, str(local)) == "pydemux"
    xbmcgui.Window(10000).setProperty(transcriber._AAC_REJECTED_PROP, "")

def test_mock_pipeline_end_to_end(profile, tmp_path):
    media = tmp_path / "episode.mkv"
    media.write_bytes(b"tiny media")
    progress = MagicMock()
    progress.iscanceled.return_value = False
    with patch.object(transcriber, "get_capabilities",
                      return_value={"ffmpeg": "", "encode_x_realtime": None, "io_mb_per_s": 50}), \
         patch.object(transcriber.xbmcgui, "DialogProgress", return_value=progress), \
         patch.object(transcriber.time, "sleep"):
        result = transcriber.run_transcription(
            None, "", {"file_original_path": str(media), "moviehash": "abc",
                       "file_size": 10}, "en", mock=True)
    assert result and os.path.exists(result)
    assert "AI transcription" in open(result).read()
    progress.close.assert_called_once()


def test_real_client_raises_not_deployed_on_404(tmp_path):
    media = tmp_path / "a.m4a"
    media.write_bytes(b"x")
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=404)
    client = transcriber.TranscriptionClient(session, "tok")
    with pytest.raises(transcriber.NotDeployed):
        client.create_job("aws", "auto", str(media))


def test_real_client_enforces_100mb_cap(tmp_path):
    media = tmp_path / "a.m4a"
    media.write_bytes(b"x")
    client = transcriber.TranscriptionClient(MagicMock(), "tok")
    with patch.object(transcriber.os.path, "getsize",
                      return_value=transcriber.MAX_UPLOAD_BYTES + 1), \
         pytest.raises(transcriber.TranscriptionError):
        client.create_job("aws", "auto", str(media))


def test_real_client_create_job_sends_spec_shape(tmp_path):
    # POST /ai/transcribe: query params api+language, multipart file (spec:
    # docs/opensubtitles_api_reference.html)
    media = tmp_path / "a.m4a"
    media.write_bytes(b"x")
    session = MagicMock()
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"status": "CREATED", "correlation_id": "abc123"}
    session.post.return_value = resp
    client = transcriber.TranscriptionClient(session, "tok")
    job = client.create_job("aws", "auto", str(media))
    assert job["correlation_id"] == "abc123"
    kwargs = session.post.call_args.kwargs
    assert kwargs["data"] == {"api": "aws", "language": "auto"}   # form fields, measured
    assert "file" in kwargs["files"]
    assert kwargs["headers"]["Authorization"] == "Bearer tok"


def test_completed_result_accepts_inline_subtitle(profile):
    state = {"status": "COMPLETED", "subtitles": "1\n00:00:01,000 --> 00:00:02,000\nhello\n"}
    path = transcriber._save_completed_result(MagicMock(), state)
    assert open(path).read().startswith("1\n")


def test_extraction_targets_32k_mono_mp3():
    """The LIVE server accepts only MPEG Audio (measured 2026-08-29) - the
    ffmpeg extraction must stay pinned to 32k mono MP3 until AAC is enabled
    server-side."""
    import inspect
    from resources.lib import transcriber
    src = inspect.getsource(transcriber.extract_audio)
    for token in ('"-ac", "1"', '"-ar", "16000"', '"32k"', '"libmp3lame"'):
        assert token in src, f"extraction lost {token}"


def test_ffmpeg_probe_covers_libreelec_tools_addon():
    from resources.lib.transcriber import FFMPEG_EXTRA_PATHS
    assert any("tools.ffmpeg-tools" in p for p in FFMPEG_EXTRA_PATHS)


def test_install_hint_is_platform_specific_and_honest():
    from unittest.mock import patch
    import xbmc
    from resources.lib.transcriber import ffmpeg_install_hint

    def platform_is(name):
        return lambda cond: name in cond

    with patch.object(xbmc, "getCondVisibility", side_effect=platform_is("OSX")):
        assert "brew install ffmpeg" in ffmpeg_install_hint()
    with patch.object(xbmc, "getCondVisibility", side_effect=platform_is("Windows")):
        assert "winget install ffmpeg" in ffmpeg_install_hint()
    with patch.object(xbmc, "getCondVisibility", side_effect=platform_is("Android")):
        hint = ffmpeg_install_hint()
        assert "does not allow" in hint and "100 MB" in hint  # honest, no false promise
    with patch.object(xbmc, "getCondVisibility", return_value=False):
        assert "package manager" in ffmpeg_install_hint()


def test_gstreamer_rung_probes_and_validates_output(tmp_path, monkeypatch):
    """extract_gstreamer: probes binary + encoder plugin, rejects empty
    output, honest errors when absent."""
    from unittest.mock import patch, MagicMock
    from resources.lib import transcriber

    with patch.object(transcriber, "find_gst_launch", return_value=None):
        with pytest.raises(transcriber.TranscriptionError):
            transcriber.extract_gstreamer("/v/x.mkv")

    with patch.object(transcriber, "find_gst_launch", return_value="/usr/bin/gst-launch-1.0"), \
         patch.object(transcriber, "_gst_mp3_encoder", return_value=None):
        with pytest.raises(transcriber.TranscriptionError):
            transcriber.extract_gstreamer("/v/x.mkv")

    out_file = {"path": None}

    class FakeProc:
        returncode = 0
        def poll(self):
            with open(out_file["path"], "wb") as f:
                f.write(b"\xff\xf1" + b"\x00" * 64)
            return 0

    def fake_popen(cmd, **kw):
        out_file["path"] = cmd[-1].split("location=", 1)[1]
        return FakeProc()

    with patch.object(transcriber, "find_gst_launch", return_value="/usr/bin/gst-launch-1.0"), \
         patch.object(transcriber, "_gst_mp3_encoder", return_value="lamemp3enc"), \
         patch.object(transcriber, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(transcriber.subprocess, "Popen", side_effect=fake_popen):
        result = transcriber.extract_gstreamer("/v/x.mkv")
    assert result.endswith(".mp3") and os.path.getsize(result) > 0


def test_aac_rejection_triggers_mp3_retry(tmp_path):
    """A 'media format not valid' 400 on an AAC rung's upload must record the
    hold and retry the SAME job through an MP3-capable rung in one flow."""
    from unittest.mock import patch, MagicMock
    import xbmc, xbmcgui
    from resources.lib import transcriber
    from resources.lib import android_audio

    xbmcgui.Window(10000).setProperty(transcriber._AAC_REJECTED_PROP, "")
    src = tmp_path / "movie.mkv"
    src.write_bytes(b"\x1aE\xdf\xa3" + b"\x00" * 64)
    caps = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 8.0}
    # force the android rung first despite viable ffmpeg
    order = ["android_ndk", "ffmpeg"]

    def fake_choose(c, f):
        return order.pop(0)

    def fake_android(path, progress=None):
        out = tmp_path / "a.aac"; out.write_bytes(b"\xff\xf1" + b"\x00" * 32)
        return str(out)

    def fake_ffmpeg(ff, path, progress=None):
        out = tmp_path / "a.mp3"; out.write_bytes(b"ID3" + b"\x00" * 32)
        return str(out)

    reject = MagicMock()
    reject.response = MagicMock(text='{"error":"media format not valid, only MPEG Audio allowed"}')
    uploads = []

    class FakeClient:
        headers = {}
        def get_credits(self):
            return None
        def list_apis(self):
            return [{"name": "nano", "display_name": "n", "price": 0,
                     "languages_supported": [{"language_code": "auto"}]}]
        def create_job(self, api, lang, path, progress=None):
            uploads.append(path)
            if path.endswith(".aac"):
                import requests
                e = requests.HTTPError("400")
                e.response = reject.response
                raise e
            return {"status": "CREATED", "correlation_id": "c9"}
        def poll(self, cid):
            done = tmp_path / "r.srt"
            done.write_text("1\n00:00:01,000 --> 00:00:02,000\nHi\n")
            return {"status": "COMPLETED", "url": "file://" + str(done)}

    with patch.object(transcriber, "get_capabilities", return_value=caps), \
         patch.object(transcriber, "choose_source", side_effect=fake_choose), \
         patch.object(transcriber, "extract_android", side_effect=fake_android), \
         patch.object(transcriber, "extract_audio", side_effect=fake_ffmpeg), \
         patch.object(transcriber, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(transcriber, "TranscriptionClient", return_value=FakeClient()), \
         patch("resources.lib.transcriber.xbmcgui.DialogProgress",
               return_value=MagicMock(iscanceled=lambda: False)):
        result = transcriber.run_transcription(MagicMock(), "tok",
                                               {"file_original_path": str(src)}, "en")
    assert len(uploads) == 2 and uploads[0].endswith(".aac") and uploads[1].endswith(".mp3")
    assert result.endswith("r.srt")
    assert not transcriber.server_accepts_aac(), "hold must be recorded"
    xbmcgui.Window(10000).setProperty(transcriber._AAC_REJECTED_PROP, "")


# --- language matching + server error surfacing (Kodi field bug 2026-08-29:
# "Slovak" -> "auto" -> openai 400 with the server body hidden) ---------------

def test_match_code_exact_prefix_and_none():
    assert transcriber._match_code("sk", {"sk", "en"}) == "sk"
    assert transcriber._match_code("sk", {"sk-SK", "en-US"}) == "sk-SK"   # aws style
    assert transcriber._match_code("sk", {"auto", "en"}) is None          # auto never matches
    assert transcriber._match_code("", {"sk"}) is None
    assert transcriber._match_code("pt-br", {"pt-BR", "pt-PT"}) == "pt-BR"


def test_pick_engine_prefix_match_keeps_regional_engines():
    apis = [{"name": "aws", "languages_supported": [{"language_code": "sk-SK"}]},
            {"name": "assembly", "languages_supported": [{"language_code": "en"}]}]
    with patch.object(transcriber.xbmcgui, "Dialog") as dlg:
        dlg.return_value.select.return_value = 0
        assert transcriber._pick_engine(apis, "sk")["name"] == "aws"


def test_check_surfaces_server_error_body(tmp_path):
    media = tmp_path / "a.mp3"
    media.write_bytes(b"x")
    session = MagicMock()
    resp = MagicMock(status_code=400)
    resp.json.return_value = {"status": "ERROR",
                              "data": ["language not supported", None]}
    session.post.return_value = resp
    client = transcriber.TranscriptionClient(session, "tok")
    with pytest.raises(transcriber.TranscriptionError) as e:
        client.create_job("openai", "auto", str(media))
    assert "language not supported" in str(e.value)
    assert e.value.response is resp        # AAC-retry flow reads .response


def test_engine_without_auto_gets_honest_error_not_400(tmp_path):
    """openai offers no 'auto'; an unmatched language must fail locally with
    an actionable message instead of a guaranteed server 400."""
    import xbmc
    src = tmp_path / "movie.mp4"
    src.write_bytes(b"\x00" * 64)
    caps = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 50.0}
    with patch.object(transcriber, "get_capabilities", return_value=caps), \
         patch.object(xbmc, "getCondVisibility", return_value=False), \
         patch.object(transcriber, "MockTranscriptionClient") as mock_client, \
         patch("resources.lib.transcriber.xbmcgui.DialogProgress",
               return_value=MagicMock(iscanceled=lambda: False)):
        mock_client.return_value.list_apis.return_value = [
            {"name": "openai", "display_name": "OpenAI Whisper", "price": 0.033,
             "languages_supported": [{"language_code": "en-US"}]}]
        with pytest.raises(transcriber.TranscriptionError) as e:
            transcriber.run_transcription(
                None, "", {"file_original_path": str(src)}, "xx", mock=True)
    assert "OpenAI Whisper" in str(e.value)
    assert "automatic language detection" in str(e.value)


def test_check_surfaces_error_key_shape(tmp_path):
    """Measured live: 4xx bodies arrive as {"error": "...", "STATUS": "ERROR"}."""
    media = tmp_path / "a.mp3"
    media.write_bytes(b"x")
    session = MagicMock()
    resp = MagicMock(status_code=400)
    resp.json.return_value = {"error": "not enough credits", "STATUS": "ERROR"}
    session.post.return_value = resp
    client = transcriber.TranscriptionClient(session, "tok")
    with pytest.raises(transcriber.TranscriptionError, match="not enough credits"):
        client.create_job("nano", "sk", str(media))


def test_zero_credits_blocks_before_extraction(tmp_path):
    """0-credit accounts get the honest dialog BEFORE any ffmpeg/upload work."""
    import xbmc
    src = tmp_path / "movie.mp4"
    src.write_bytes(b"\x00" * 64)
    caps = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 50.0}
    extract = MagicMock()
    with patch.object(transcriber, "get_capabilities", return_value=caps), \
         patch.object(xbmc, "getCondVisibility", return_value=False), \
         patch.object(transcriber, "extract_audio", extract), \
         patch.object(transcriber, "MockTranscriptionClient") as mock_client, \
         patch("resources.lib.transcriber.xbmcgui.DialogProgress",
               return_value=MagicMock(iscanceled=lambda: False)):
        mock_client.return_value.list_apis.return_value = [
            {"name": "nano", "display_name": "Nano", "price": 0.0075,
             "languages_supported": [{"language_code": "sk"}]}]
        mock_client.return_value.get_credits.return_value = 0
        with pytest.raises(transcriber.TranscriptionError) as e:
            transcriber.run_transcription(
                None, "", {"file_original_path": str(src)}, "sk", mock=True)
    assert "0 AI credits" in str(e.value)
    assert not extract.called
