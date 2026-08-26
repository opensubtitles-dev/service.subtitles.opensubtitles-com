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
    fast = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 8.0}
    slow = {"ffmpeg": "/usr/bin/ffmpeg", "encode_x_realtime": 1.2}
    none = {"ffmpeg": "", "encode_x_realtime": None}
    assert transcriber.choose_source(fast, str(local)) == "ffmpeg"
    assert transcriber.choose_source(slow, str(local)) == "upload"   # too slow to reencode
    assert transcriber.choose_source(none, "https://cdn/stream.m3u8") == "url"
    assert transcriber.choose_source(none, str(local)) == "upload"


def test_mock_pipeline_end_to_end(profile):
    progress = MagicMock()
    progress.iscanceled.return_value = False
    with patch.object(transcriber, "get_capabilities",
                      return_value={"ffmpeg": "", "encode_x_realtime": None, "io_mb_per_s": 50}), \
         patch.object(transcriber.xbmcgui, "DialogProgress", return_value=progress), \
         patch.object(transcriber.time, "sleep"):
        result = transcriber.run_transcription(
            None, "", {"file_original_path": "https://cdn/x.m3u8", "moviehash": "abc",
                       "file_size": 1}, "en", mock=True)
    assert result and os.path.exists(result)
    assert "AI transcription" in open(result).read()
    progress.close.assert_called_once()


def test_real_client_raises_not_deployed_on_404():
    session = MagicMock()
    session.post.return_value = MagicMock(status_code=404)
    client = transcriber.TranscriptionClient(session, "tok")
    with pytest.raises(transcriber.NotDeployed):
        client.create_job({"moviehash": "x"})


def test_real_client_cache_hit_on_409():
    session = MagicMock()
    resp = MagicMock(status_code=409)
    resp.json.return_value = {"subtitle_id": "555"}
    session.post.return_value = resp
    client = transcriber.TranscriptionClient(session, "tok")
    job = client.create_job({"moviehash": "x"})
    assert job["cache_hit"] and job["subtitle_id"] == "555"
