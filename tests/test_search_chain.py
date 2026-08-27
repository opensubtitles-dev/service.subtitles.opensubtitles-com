"""The ordered search fallback chain built by get_media_data().

OS.com ANDs every search parameter, so the add-on cannot send "everything it knows" in one
request - it sends one precise query and falls back only if that returns nothing. The order
matters, and each tier exists for a specific real-world failure:

  1. show id + season/episode   - the normal case (Umbrella, POV, a healthy library)
  2. the episode's own id alone - Seren-style add-ons, and mis-scraped libraries whose
                                  parent id OS.com has never seen (issue #40)
  3. title + season/episode     - no usable id at all
  4. the raw release filename   - everything above missed; uploaders often name subtitles
                                  after the release

Tier 2 was silently lost once already, when merging a release branch reshuffled this block
and moved it onto the movie path where it was unreachable. Every test passed at the time.
Hence this file: it asserts the shape of the *whole chain*, not one attempt.
"""
from unittest.mock import patch

from resources.lib.data_collector import get_media_data

LOCAL_FILE = "/tv/Succession/Season 02/Succession.S02E01.1080p.WEB.h264-TBS.mkv"
CDN_URL = "https://nexus-098.neur.tb-cdn.st/dld/5999b664-ad4d-4b63-a2e9-2fb9531e0dfc"

INFO_LABELS = {
    "videoplayer.tvshowtitle": "Succession",
    "videoplayer.season": "2",
    "videoplayer.episode": "1",
    "videoplayer.uniqueid(imdb)": "8543048",   # the episode's own id
    "videoplayer.tvshowdbid": "1926",
    "videoplayer.year": "2019",
}

TVSHOW_DETAILS = (
    '{"jsonrpc":"2.0","id":"1","result":{"tvshowdetails":'
    '{"originaltitle":"Succession","imdbnumber":"tt7660850","uniqueid":{}}}}'
)


def _plan(playing_file):
    """Return (item, fallback overrides) exactly as get_media_data() builds them."""
    with patch("xbmc.getInfoLabel", side_effect=lambda t: INFO_LABELS.get(str(t).lower(), "")), \
         patch("xbmc.executeJSONRPC", return_value=TVSHOW_DETAILS), \
         patch("resources.lib.data_collector.get_file_path", return_value=playing_file):
        item = get_media_data()
    return item, item.get("search_fallbacks") or []


def test_primary_attempt_uses_the_show_id_with_season_and_episode():
    item, _ = _plan(LOCAL_FILE)
    assert item.get("parent_imdb_id") == 7660850
    assert item.get("season_number") == "2"
    assert item.get("episode_number") == "1"
    assert not item.get("query"), "query is redundant alongside a show id and over-constrains"


def test_episode_id_is_kept_as_a_fallback_behind_the_show_id():
    """The tier that went missing in the v1.0.15 merge.

    A library `imdbnumber` can hold a non-IMDb id (a TVDB id, say). The show-id attempt then
    matches nothing, and the episode id the player gave us is the only thing left that works.
    """
    _, fallbacks = _plan(LOCAL_FILE)
    assert any(f.get("imdb_id") == 8543048 for f in fallbacks), (
        "no episode-id fallback: a wrong parent id will now return zero subtitles instead of "
        "falling back to the episode's own id. See issue #40."
    )


def test_title_search_is_a_fallback():
    _, fallbacks = _plan(LOCAL_FILE)
    assert any(f.get("query") == "Succession" and f.get("season_number") == "2"
               for f in fallbacks), "no title + season/episode fallback"


def test_release_filename_is_the_last_resort():
    _, fallbacks = _plan(LOCAL_FILE)
    assert fallbacks, "no fallbacks at all"
    last = fallbacks[-1]
    assert last.get("query") == "Succession.S02E01.1080p.WEB.h264-TBS", (
        "the raw release filename should be the final attempt, with its extension stripped"
    )
    assert not any(last.get(k) for k in
                   ("imdb_id", "tmdb_id", "parent_imdb_id", "parent_tmdb_id",
                    "season_number", "episode_number")), (
        "the filename attempt must travel alone - it is a text search, and any id or "
        "season/episode alongside it just over-constrains the query"
    )


def test_fallbacks_are_ordered_ids_then_title_then_filename():
    _, fallbacks = _plan(LOCAL_FILE)
    kinds = []
    for f in fallbacks:
        if f.get("imdb_id") or f.get("tmdb_id"):
            kinds.append("id")
        elif f.get("season_number") or f.get("episode_number"):
            kinds.append("title")
        else:
            kinds.append("filename")
    assert kinds == sorted(kinds, key=["id", "title", "filename"].index), (
        f"fallbacks are out of order: {kinds}. Cheap, precise attempts must come first."
    )


def test_streamed_source_contributes_no_filename_attempt():
    """For a stream the "filename" is a CDN path: no release info, and not ours to send."""
    _, fallbacks = _plan(CDN_URL)
    for f in fallbacks:
        query = str(f.get("query") or "")
        assert "nexus" not in query and "5999b664" not in query, (
            f"a CDN path leaked into a search query: {query!r}"
        )


def test_non_numeric_parent_imdb_from_features_does_not_abort():
    # /features returning a truthy non-numeric parent_imdb_id must fall through
    # to the id-alone episode path, never ValueError out of the search
    # (mirror-review finding, internal PR #45).
    from unittest.mock import patch, MagicMock
    from resources.lib.subtitle_downloader import SubtitleDownloader
    import sys as _sys
    with patch.object(_sys, "argv", ["plugin://x", "1", "?action=search"]):
        sd = SubtitleDownloader.__new__(SubtitleDownloader)
    sd.open_subtitles = MagicMock()
    sd.open_subtitles.get_feature_info.return_value = {
        "feature_type": "Episode", "parent_imdb_id": "not-a-number",
        "season_number": 2, "episode_number": 3}
    result = sd._resolve_ambiguous_id({"imdb_id": 999})
    assert result is not None
    assert result.get("parent_imdb_id") is None or isinstance(result.get("parent_imdb_id"), int)


def test_fallback_attempt_clears_unnamed_id_fields():
    """A retry must be the attempt's reading alone: ids resolved into the
    primary query (e.g. parent_imdb_id from /features) must not leak into a
    fallback attempt that names a different id."""
    from unittest.mock import patch
    from resources.lib.subtitle_downloader import SubtitleDownloader

    test_argv = ["plugin://service.subtitles.opensubtitles-com/", "1",
                 "?action=search&languages=English"]
    with patch("sys.argv", test_argv):
        sd = SubtitleDownloader.__new__(SubtitleDownloader)
    sd.params = {"action": "search", "languages": "English"}
    sd.sub_format = "srt"
    sd.subtitles = {}
    seen = []

    def fake_search(q):
        seen.append(dict(q))
        return {}, True

    media = {"query": "", "parent_imdb_id": 123456, "season_number": "3",
             "episode_number": "4", "search_fallbacks": [{"imdb_id": 999}]}
    with patch("resources.lib.subtitle_downloader.get_file_path", return_value="/tv/x.mkv"), \
         patch("resources.lib.subtitle_downloader.get_file_data",
               return_value={"filename": "x.mkv", "basename": "x.mkv"}), \
         patch("resources.lib.subtitle_downloader.get_media_data", return_value=media), \
         patch("resources.lib.subtitle_downloader.get_language_data",
               return_value={"languages": "en"}), \
         patch("resources.lib.subtitle_downloader._call_guessit_api", return_value=None), \
         patch.object(sd, "_search_subtitles", side_effect=fake_search):
        sd.search()

    assert len(seen) == 2
    retry = seen[1]
    assert retry["imdb_id"] == 999
    assert retry["parent_imdb_id"] is None, "resolved parent id must not over-constrain the retry"
    assert retry["season_number"] == "3", "non-id context stays inherited"


def test_resolve_ambiguous_id_accepts_season_zero():
    """/features resolving a specials episode (season 0) must keep the parent
    id + season/episode coordinates, not degrade to an id-only search."""
    from unittest.mock import patch, MagicMock
    from resources.lib.subtitle_downloader import SubtitleDownloader

    sd = SubtitleDownloader.__new__(SubtitleDownloader)
    sd.open_subtitles = MagicMock()
    sd.open_subtitles.get_feature_info.return_value = {
        "feature_type": "episode", "parent_imdb_id": "436992",
        "season_number": 0, "episode_number": 4}
    resolved = sd._resolve_ambiguous_id({"imdb_id": 1000001})
    assert resolved["parent_imdb_id"] == 436992
    assert resolved["season_number"] == "0"
    assert resolved["episode_number"] == "4"
