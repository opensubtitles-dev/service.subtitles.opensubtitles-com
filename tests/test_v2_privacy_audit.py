"""Regressions from the v2.0 deep audit: no viewing history in service logs,
shape-safe transcription client, controlled URL handling."""
import os
import time
from unittest.mock import patch, MagicMock

import pytest
import xbmc


SECRET = "SECRETV2TITLE"


def test_auto_download_flow_logs_no_viewing_history(tmp_path):
    from resources.lib import background_service as bs

    player = bs.OpenSubtitlesPlayer.__new__(bs.OpenSubtitlesPlayer)
    player.monitor = None
    player.auto_download_enabled = True
    player.prompt_rating_enabled = False
    player.active_session = None
    player.setSubtitles = MagicMock()
    player.getTotalTime = lambda: 3600
    player.isPlayingVideo = lambda: True

    subs = [{"id": 1, "attributes": {
        "language": "en", "release": f"{SECRET}.2024.1080p.BluRay",
        "feature_details": {"title": SECRET, "movie_name": SECRET},
        "files": [{"file_id": 111}]}}]
    media = {"query": SECRET, "tv_show_title": "", "original_title": SECRET,
             "search_fallbacks": [{"query": SECRET, "year": None}]}
    logged = []
    with patch.object(player, "_kodi_setting", return_value=None), \
         patch.object(player, "_active_subtitle_state",
                      return_value=(True, "", f"{SECRET} track")), \
         patch.object(xbmc, "log", side_effect=lambda m, level=0: logged.append(str(m))):
        # early-skip branch: enabled subtitle with a NAMED track
        player._auto_download_flow()
    assert SECRET not in "\n".join(logged), "track name leaked"

    logged.clear()
    import xbmcaddon
    xbmcaddon.Addon().setSetting("OSuser", "u")
    xbmcaddon.Addon().setSetting("OSpass", "p")
    with patch.object(player, "_kodi_setting", return_value=None), \
         patch.object(player, "_active_subtitle_state", return_value=(False, "", "")), \
         patch.object(player, "_preferred_subtitle_languages", return_value=("en", ["en"])), \
         patch.object(player, "_add_subtitle_stream"), \
         patch("resources.lib.background_service.get_media_data", return_value=dict(media)), \
         patch("resources.lib.background_service.get_file_path",
               return_value=f"/movies/{SECRET}.2024.mkv"), \
         patch("resources.lib.background_service.OpenSubtitlesProvider.search_subtitles",
               return_value=subs), \
         patch("resources.lib.background_service.OpenSubtitlesProvider.download_subtitle",
               return_value={"content": b"1\n00:00:01,000 --> 00:00:02,000\nHi\n"}), \
         patch("xbmcvfs.translatePath", return_value=str(tmp_path)), \
         patch("resources.lib.background_service.xbmcgui.Dialog", return_value=MagicMock()), \
         patch.object(xbmc, "log", side_effect=lambda m, level=0: logged.append(str(m))):
        player._auto_download_flow()
    leaks = [l for l in logged if SECRET in l]
    assert not leaks, f"viewing history leaked: {leaks[:2]}"


def test_transcription_check_rejects_non_object_bodies():
    from resources.lib.transcriber import TranscriptionClient, TranscriptionError
    client = TranscriptionClient.__new__(TranscriptionClient)
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status.return_value = None
    r.json.return_value = ["not", "an", "object"]
    with pytest.raises(TranscriptionError):
        client._check(r)


def test_transcription_result_url_must_be_http(tmp_path):
    from resources.lib import transcriber
    with patch.object(transcriber, "_profile_dir", return_value=str(tmp_path)):
        with pytest.raises(transcriber.TranscriptionError):
            transcriber._save_completed_result(MagicMock(), {"url": "ftp://evil/x"})


def test_upload_resume_carries_no_paths(tmp_path):
    from resources.lib.upload_eligibility import check_upload_eligibility, format_resume
    sub = tmp_path / f"{SECRET}.en.srt"
    sub.write_text("1\n00:00:01,000 --> 00:00:02,000\nHi\n" * 30)
    session = {"sub_path": str(sub), "origin": "local", "total_time": 100,
               "last_position": 90, "media": {}, "sub_language": "en"}
    eligible, checks = check_upload_eligibility(session, True)
    assert SECRET not in format_resume(eligible, checks), "path leaked into the resume"
