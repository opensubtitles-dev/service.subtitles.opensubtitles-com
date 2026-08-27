"""Regression tests for get_file_data path normalization.

The historic code stripped six characters from EVERY non-temp path (a leftover
of "rar://" prefix handling), which mangled the basename of plain local paths -
"/tv/E1.mkv" became ".mkv" - and with it the fallback search query and smart
ranking. Flagged by review on the Kodi repo submission (PR #4809).
"""
from unittest.mock import patch

from resources.lib.file_operations import get_file_data


def _no_hash(*_args, **_kwargs):
    return 0, "0000000000000000"


def test_local_path_keeps_full_basename():
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("/movies/The.Matrix.1999.1080p.mkv")
    assert item["basename"] == "The.Matrix.1999.1080p.mkv"
    assert item["file_original_path"] == "/movies/The.Matrix.1999.1080p.mkv"


def test_short_local_path_not_mangled():
    # "/tv/E1.mkv"[6:] == ".mkv" - the exact failure mode of the old slice
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("/tv/E1.mkv")
    assert item["basename"] == "E1.mkv"


def test_rar_path_keeps_archive_content_basename():
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("rar://%2fmovies%2ffoo.rar/The.Movie.2020.mkv")
    assert item["rar"] is True
    assert item["basename"] == "The.Movie.2020.mkv"


def test_stack_path_uses_first_part():
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("stack:///movies/part1.mkv , /movies/part2.mkv")
    assert item["file_original_path"] == "/movies/part1.mkv"
    assert item["basename"] == "part1.mkv"


def test_small_file_returns_size_and_empty_hash():
    # Files under 128 KiB cannot produce the OpenSubtitles hash; the search
    # must continue hashless instead of dying on the old "SizeError" scalar.
    from unittest.mock import MagicMock
    small = MagicMock()
    small.size.return_value = 1000
    small.__enter__ = lambda s: small
    small.__exit__ = lambda s, *a: False
    with patch("resources.lib.file_operations.xbmcvfs.File", return_value=small):
        item = get_file_data("/tv/E1.mkv")
    assert item["basename"] == "E1.mkv"
    assert item["file_size"] == 1000
    assert item["moviehash"] == ""


def test_hash_failure_degrades_to_hashless_search():
    with patch("resources.lib.file_operations.hash_file", side_effect=Exception("bad rar")):
        item = get_file_data("rar://%2fmovies%2ffoo.rar/The.Movie.2020.mkv")
    assert item["basename"] == "The.Movie.2020.mkv"
    assert "moviehash" not in item  # absent, falsy - search proceeds without it


def test_clean_temp_directory_spares_fresh_files(tmp_path):
    # Overlapping invocations must not delete each other's just-written
    # subtitle; only stale entries go.
    import time as _time
    import resources.lib.subtitle_downloader as sd
    fresh = tmp_path / "TempSubtitle.111.en.srt"
    fresh.write_text("fresh")
    stale = tmp_path / "TempSubtitle.222.de.srt"
    stale.write_text("stale")
    old = _time.time() - sd.TEMP_MAX_AGE_SECONDS - 60
    import os as _os
    _os.utime(stale, (old, old))
    with patch.object(sd, "__temp__", str(tmp_path)):
        sd.clean_temp_directory()
    assert fresh.exists()
    assert not stale.exists()


def test_player_tvshowid_does_not_clobber_library_id():
    # Non-library playback: VideoPlayer.TvShowDBID is empty and must not erase
    # the tvshowid the filename->library lookup found (it gates the
    # original-title / parent-id JSON-RPC refinement).
    from resources.lib.data_collector import _apply_player_tvshowid
    with patch("resources.lib.data_collector.xbmc.getInfoLabel", return_value=""):
        item = {"tvshowid": "42"}
        _apply_player_tvshowid(item)
        assert item["tvshowid"] == "42"

        empty = {}
        _apply_player_tvshowid(empty)
        assert empty["tvshowid"] == ""  # key must exist for len() downstream

    with patch("resources.lib.data_collector.xbmc.getInfoLabel", return_value="7"):
        item = {"tvshowid": "42"}
        _apply_player_tvshowid(item)
        assert item["tvshowid"] == "7"  # a real player DBID wins


def test_unique_subtitle_path_is_invocation_unique():
    # os.getpid() is constant across Kodi sub-interpreter invocations, so the
    # path must differ per call, not per process.
    from resources.lib.subtitle_downloader import unique_subtitle_path
    a = unique_subtitle_path("/tmp/x", "en", "srt")
    b = unique_subtitle_path("/tmp/x", "en", "srt")
    assert a != b
    assert a.endswith(".en.srt") and a.startswith("/tmp/x/TempSubtitle.")


def test_official_kodi_version_falls_back_to_buildversion():
    # System.BuildVersionShort is not universal; System.BuildVersion
    # ("21.3 (21.3.0) Git:...") must carry the branch mapping alone.
    import check_updates as cu

    labels = {"System.BuildVersionShort": "", "System.BuildVersion": "21.3 (21.3.0) Git:x"}
    seen = {}

    class Resp:
        status_code = 200

        @staticmethod
        def iter_content(chunk_size=0):
            return iter([b'<addon id="service.subtitles.opensubtitles-com" version="1.0.9"/>'])

    def fake_get(url, **kw):
        seen["url"] = url
        return Resp()

    with patch("check_updates.xbmc.getInfoLabel", side_effect=lambda l: labels.get(l, "")), \
         patch("check_updates.requests.get", side_effect=fake_get):
        assert cu.fetch_official_kodi_version() == "1.0.9"
    assert "/omega/" in seen["url"]  # major 21 -> omega branch

    # Neither label parseable -> None, never an exception
    with patch("check_updates.xbmc.getInfoLabel", return_value=""):
        assert cu.fetch_official_kodi_version() is None


def test_redact_path_strips_tokens_and_credentials():
    # Debug logs are what users paste on forums - stream URLs with tokens or
    # userinfo must never reach them raw (security finding, PR #4814).
    from resources.lib.utilities import redact_path
    r = redact_path("https://user:secret@cdn.example.com/movie.mkv?token=abc123#f")
    assert "secret" not in r and "abc123" not in r and "user" not in r
    assert "cdn.example.com/movie.mkv" in r and "redacted" in r
    assert redact_path("/local/path/movie.mkv") == "/local/path/movie.mkv"
    assert redact_path("smb://server/share/file.mkv") == "smb://server/share/file.mkv"


def test_media_data_filename_derivation_strips_url_query():
    # basename of a raw URL keeps "?token=..." glued to the name - both a
    # credential leak in logs and garbage for guessit (full-codebase review).
    from urllib.parse import urlsplit, unquote
    import os
    url = "https://cdn.example.com/path/My.Movie.2024.mkv?token=SECRET123"
    filename = os.path.basename(unquote(urlsplit(url).path))
    assert filename == "My.Movie.2024.mkv"
    assert "SECRET" not in filename


def test_safe_media_filename_survives_encoded_tokens():
    # '%3Ftoken%3D' decodes into a fresh '?token=' - one-layer stripping
    # reintroduced the secret (mirror-review finding, internal PR #47).
    from resources.lib.utilities import safe_media_filename
    assert safe_media_filename(
        "https://cdn.example.com/video%3Ftoken%3DSECRET99.mkv") == "video"
    assert safe_media_filename(
        "plugin://plugin.video.x/?url=https%3A%2F%2Fcdn%2FMovie.mkv%3Ftoken%3DS") == ""
    assert safe_media_filename(
        "https://cdn.example.com/path/My.Movie.2024.mkv?token=SECRET") == "My.Movie.2024.mkv"
    assert safe_media_filename("/local/My.Movie.mkv") == "My.Movie.mkv"
    assert "SECRET" not in safe_media_filename(
        "https://u:SECRET@cdn/x%23frag%3Ftoken%3DSECRET.mkv")


def test_stack_url_member_basename_sheds_token(monkeypatch):
    """stack:// whose first member is a token-bearing stream URL: the derived
    basename must not retain the query string."""
    from unittest.mock import patch
    from resources.lib import file_operations

    stack = ("stack://ftp://cdn.example/part1.mkv?token=SECRET-STACK-TOKEN"
             " , ftp://cdn.example/part2.mkv?token=SECRET-STACK-TOKEN")
    with patch.object(file_operations, "hash_file", return_value=(0, "")):
        item = file_operations.get_file_data(stack)
    assert "SECRET-STACK-TOKEN" not in item["basename"]
    assert item["basename"] == "part1.mkv"


def test_hash_failure_log_never_contains_path(monkeypatch):
    """A vfs/OS exception message embeds the raw path (token included); the
    hash-failure log line must carry only the exception class."""
    import xbmc
    from unittest.mock import patch
    from resources.lib import file_operations

    secret_path = "ftp://cdn.example/v.mkv?token=SECRET-HASH-TOKEN"
    logged = []
    with patch.object(file_operations, "hash_file",
                      side_effect=OSError(f"cannot open {secret_path}")), \
         patch.object(xbmc, "log", side_effect=lambda msg, level=0: logged.append(str(msg))):
        item = file_operations.get_file_data(secret_path)
    assert "SECRET-HASH-TOKEN" not in "\n".join(logged)
    assert "moviehash" not in item or not item.get("moviehash")


def test_malformed_size_property_degrades_to_hashless(monkeypatch):
    """A nonnumeric videoinfo.current_size from a playback integration must
    not abort the search - just skip the size."""
    import xbmc
    from unittest.mock import patch
    from resources.lib import file_operations

    props = {"Window(10000).Property(videoinfo.current_path)": "/movies/x.mkv",
             "Window(10000).Property(videoinfo.current_size)": "not-a-number",
             "Window(10000).Property(videoinfo.current_oshash)": ""}
    with patch.object(xbmc, "getInfoLabel", side_effect=lambda k: props.get(k, "")), \
         patch.object(file_operations, "hash_file", return_value=(0, "")):
        item = file_operations.get_file_data("http://cdn.example/v.mkv")
    assert "file_size" not in item
    assert item["basename"] == "x.mkv"


def test_multipart_rar_last_split_index_is_integer():
    """Python 3 turned '/' into float division; the float index blew up the
    %d filename formatting for multipart RARs, losing the moviehash."""
    from resources.lib.file_operations import get_last_split

    # the exact expression hash_rar uses, with realistic sizes
    s_unpack_size, s_divide_body = 1_468_006_400, 104_857_600
    index = (s_unpack_size - 1) // s_divide_body
    assert isinstance(index, int)
    assert get_last_split("/m/video.part01.rar", index) == "/m/video.part14.rar"
    assert get_last_split("/m/video.001", index) == "/m/video.014"
