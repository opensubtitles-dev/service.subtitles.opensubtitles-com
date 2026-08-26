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
    local = tmp_path / "movie.mkv"
    local.write_text("x")
    big = tmp_path / "big.mkv"
    big.write_bytes(b"x")
    fast = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 8.0}
    slow = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 1.2}
    none = {"ffmpeg": "", "encode_x_realtime": None}
    assert transcriber.choose_source(fast, str(local)) == "ffmpeg"
    assert transcriber.choose_source(slow, str(local)) == "upload"   # small file fits the 100 MB cap
    assert transcriber.choose_source(none, str(local)) == "upload"
    with patch.object(transcriber.os.path, "getsize", return_value=transcriber.MAX_UPLOAD_BYTES + 1):
        assert transcriber.choose_source(none, str(big)) == "too_big"
    assert transcriber.choose_source(none, "https://cdn/stream.m3u8") == "too_big"  # no URL mode in the API


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
    assert kwargs["params"] == {"api": "aws", "language": "auto"}
    assert "file" in kwargs["files"]
    assert kwargs["headers"]["Authorization"] == "Bearer tok"


def test_completed_result_accepts_inline_subtitle(profile):
    state = {"status": "COMPLETED", "subtitles": "1\n00:00:01,000 --> 00:00:02,000\nhello\n"}
    path = transcriber._save_completed_result(MagicMock(), state)
    assert open(path).read().startswith("1\n")
