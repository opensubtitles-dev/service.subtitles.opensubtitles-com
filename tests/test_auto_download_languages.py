"""Covers auto-download's Kodi-conflict standdown and multi-language top picks."""
import time
from unittest.mock import MagicMock, patch

import xbmcaddon

import resources.lib.background_service as service_monitor
from resources.lib.background_service import OpenSubtitlesPlayer


def _sub(sub_id, lang, release, file_id, score):
    return {"id": sub_id, "_match_score": score,
            "attributes": {"language": lang, "release": release,
                           "files": [{"file_id": file_id}]}}


def _player():
    player = OpenSubtitlesPlayer()
    player.isPlayingVideo = MagicMock(return_value=True)
    player.setSubtitles = MagicMock()
    player.getTotalTime = MagicMock(return_value=7200.0)
    player.auto_download_enabled = True
    return player


def test_stands_down_when_kodi_native_autodownload_is_on():
    service_monitor._kodi_autodownload_warned = False
    player = _player()

    def kodi_setting(name):
        return True if name == "subtitles.downloadfirst" else None

    dialog = MagicMock()
    with patch.object(player, "_kodi_setting", side_effect=kodi_setting), \
         patch.object(player, "_active_subtitle_state", return_value=None), \
         patch("resources.lib.background_service.get_media_data") as media, \
         patch("resources.lib.background_service.xbmcgui.Dialog", return_value=dialog):
        player._auto_download_flow()
        media.assert_not_called()          # stood down before any work
        dialog.notification.assert_called_once()

        player._auto_download_flow()       # second playback: no repeat nag
        assert dialog.notification.call_count == 1


def test_downloads_top_subtitle_for_every_preferred_language(tmp_path):
    service_monitor._kodi_autodownload_warned = False
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user")
    addon.setSetting("OSpass", "pass")
    addon.setSetting("APIKey", "key")

    player = _player()
    added_streams = []

    subs = [
        _sub("s_en_best", "en", "Movie.2024.1080p.BluRay-FLUX", 111, 9000.0),
        _sub("s_en_worse", "en", "Movie.2024.720p.WEB", 112, 4000.0),
        _sub("s_cs_best", "cs", "Movie.2024.1080p.CZ", 221, 8000.0),
    ]

    with patch.object(player, "_kodi_setting", return_value=None), \
         patch.object(player, "_active_subtitle_state", return_value=(False, "", "")), \
         patch.object(player, "_preferred_subtitle_languages", return_value=("cs", ["cs", "en"])), \
         patch.object(player, "_add_subtitle_stream", side_effect=added_streams.append), \
         patch("resources.lib.background_service.get_media_data", return_value={"query": "Movie", "year": "2024"}), \
         patch("resources.lib.background_service.get_file_path", return_value="/movies/Movie.2024.1080p.mkv"), \
         patch("resources.lib.background_service.OpenSubtitlesProvider.search_subtitles", return_value=subs) as search, \
         patch("resources.lib.background_service.OpenSubtitlesProvider.download_subtitle",
               return_value={"content": b"1\n00:00:01,000 --> 00:00:02,000\nHi\n"}) as download, \
         patch("xbmcvfs.translatePath", return_value=str(tmp_path)), \
         patch("resources.lib.background_service.xbmcgui.Dialog", return_value=MagicMock()):
        player._auto_download_flow()

    # Search asked for both languages in one call
    assert search.call_args[0][0]["languages"] == "cs,en"
    # One download per language, best of each - never the worse English one
    downloaded = {c.args[0]["file_id"] for c in download.call_args_list}
    assert downloaded == {111, 221}
    # Czech (primary) is the ACTIVE subtitle; English joined the stream list.
    # Files carry Kodi's own naming (<video>.<lang>.srt) so future plays
    # auto-detect them without a search.
    active_path = player.setSubtitles.call_args[0][0]
    assert active_path.endswith("Movie.2024.1080p.cs.srt")
    assert len(added_streams) == 1 and added_streams[0].endswith("Movie.2024.1080p.en.srt")
    # Session records the primary pick for the rating prompt
    assert player.active_session["file_id"] == 221


def test_storage_dir_follows_kodi_storagemode(tmp_path):
    """storagemode 0 = movie folder; custom folder when set; temp otherwise."""
    player = _player()

    with patch.object(player, "_kodi_setting", return_value=0):
        assert player._subtitle_destination_dir("/movies/Film/Film.2024.mkv") == "/movies/Film"
        # Streams cannot host a subtitle file next to them
        with patch("xbmcvfs.translatePath", return_value=""):
            assert player._subtitle_destination_dir("http://host/stream.mkv") is None

    with patch.object(player, "_kodi_setting", return_value=1),          patch("xbmcvfs.translatePath", return_value="/subs/custom"):
        assert player._subtitle_destination_dir("/movies/Film/Film.2024.mkv") == "/subs/custom"

    with patch.object(player, "_kodi_setting", return_value=1),          patch("xbmcvfs.translatePath", return_value=""):
        assert player._subtitle_destination_dir("/movies/Film/Film.2024.mkv") is None


def test_subtitle_copy_falls_back_to_direct_write_when_vfs_refuses(tmp_path):
    """Regression: xbmcvfs.copy returned False on plain local paths - files never
    landed in the movie folder even though it was writable."""
    player = _player()
    source = tmp_path / "os_auto_1.en.srt"
    source.write_bytes(b"1\n00:00:01,000 --> 00:00:02,000\nHi\n")
    target = tmp_path / "Movie.2024.en.srt"

    with patch("xbmcvfs.exists", return_value=False), \
         patch("xbmcvfs.copy", return_value=False):
        stored = player._store_subtitle_copy(str(source), str(target))

    assert stored == str(target)
    assert target.read_bytes() == source.read_bytes()


def test_subtitle_copy_reports_none_when_folder_is_unwritable(tmp_path):
    player = _player()
    source = tmp_path / "os_auto_1.en.srt"
    source.write_bytes(b"data")

    with patch("xbmcvfs.exists", return_value=False), \
         patch("xbmcvfs.copy", return_value=False):
        stored = player._store_subtitle_copy(str(source), "/nonexistent-root-dir/Movie.en.srt")

    assert stored is None
