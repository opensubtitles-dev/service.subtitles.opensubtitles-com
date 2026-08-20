import pytest
from unittest.mock import patch, MagicMock
import xbmcaddon
from resources.lib.data_collector import get_media_data, _extract_basic_tv_info
from resources.lib.matcher import calculate_match_score, rank_subtitles
from resources.lib.osclient.provider import OpenSubtitlesProvider


def test_extract_basic_tv_info_various_formats():
    # SxxExx format
    show1, s1, e1 = _extract_basic_tv_info("House.of.the.Dragon.S02E04.The.Red.Dragon.1080p.mkv")
    assert show1 == "House of the Dragon"
    assert s1 == "02"
    assert e1 == "04"

    # NxNN format
    show2, s2, e2 = _extract_basic_tv_info("The.Office.US.2x12.The.Injury.720p.avi")
    assert show2 == "The Office US"
    assert s2 == "2"
    assert e2 == "12"

    # Lowercase s01e01
    show3, s3, e3 = _extract_basic_tv_info("stranger.things.s04e09.1080p.mkv")
    assert show3.lower() == "stranger things"
    assert s3 == "04"
    assert e3 == "09"


def test_get_media_data_tv_episode_with_parent_imdb():
    """Verify TV episode with parent show IMDb ID configures query & fallback correctly."""
    with patch("xbmc.getInfoLabel") as mock_info, \
         patch("resources.lib.data_collector._query_kodi_library_for_show", return_value=(903747, None, 1)), \
         patch("resources.lib.data_collector.get_file_path", return_value="/tv/Breaking Bad/Season 5/Breaking.Bad.S05E16.mkv"), \
         patch("resources.lib.utilities.get_params", return_value={"languages": "English", "preferredlanguage": "English"}):

        def info_side_effect(tag):
            mapping = {
                "videoplayer.tvshowtitle": "Breaking Bad",
                "videoplayer.season": "5",
                "videoplayer.episode": "16",
                "videoplayer.title": "Felina",
                "videoplayer.tvshow.imdbnumber": "tt0903747",  # Parent show IMDb ID
                "listitem.property(tvshow.imdbnumber)": "tt0903747",
            }
            return mapping.get(str(tag).lower(), "")

        mock_info.side_effect = info_side_effect

        media_data = get_media_data()

        # Strategy: Use parent_imdb_id + season + episode
        assert int(media_data.get("parent_imdb_id")) == 903747
        assert str(media_data.get("season_number")) == "5"
        assert str(media_data.get("episode_number")) == "16"
        assert media_data.get("imdb_id") is None
        
        # Primary query string is blanked so ID search is clean
        assert media_data.get("query") == ""

        # Fallback attempt exists in case parent ID returns 0 results
        assert len(media_data.get("search_fallbacks", [])) > 0
        fallback = media_data["search_fallbacks"][0]
        assert fallback.get("query") == "Breaking Bad" or fallback.get("parent_imdb_id") is not None


def test_tv_episode_search_and_fallback_execution():
    """Simulate provider searching for TV episode with primary parent ID and fallback."""
    provider = OpenSubtitlesProvider(api_key="test_api", username="", password="")

    # When primary search returns empty, fallback search is triggered
    primary_query = {
        "parent_imdb_id": "0903747",
        "season_number": "5",
        "episode_number": "16",
        "query": "",
        "languages": "en",
        "search_fallbacks": [
            {"query": "Breaking Bad", "season_number": "5", "episode_number": "16", "languages": "en"}
        ]
    }

    with patch.object(provider.session, "get") as mock_get:
        # 1st call (parent_imdb_id): returns 0 results
        resp_empty = MagicMock()
        resp_empty.status_code = 200
        resp_empty.json.return_value = {"data": []}
        resp_empty.raise_for_status.return_value = None

        # 2nd call (fallback title): returns 2 results
        resp_fallback = MagicMock()
        resp_fallback.status_code = 200
        resp_fallback.json.return_value = {
            "data": [
                {"id": "sub_1", "attributes": {"release": "Breaking.Bad.S05E16.Felina.1080p.BluRay-ROVERS", "language": "en"}},
                {"id": "sub_2", "attributes": {"release": "Breaking.Bad.S05E16.720p.HDTV", "language": "en"}}
            ]
        }
        resp_fallback.raise_for_status.return_value = None

        mock_get.side_effect = [resp_empty, resp_fallback]

        # Execute search with fallback
        results = provider.search_subtitles(primary_query)
        if not results and primary_query.get("search_fallbacks"):
            for fb in primary_query["search_fallbacks"]:
                results = provider.search_subtitles(fb)
                if results:
                    break

        assert len(results) == 2
        assert results[0]["attributes"]["release"] == "Breaking.Bad.S05E16.Felina.1080p.BluRay-ROVERS"


def test_tv_episode_ranking_exact_release_group():
    """Verify smart matcher accurately ranks TV episode releases (BluRay-ROVERS vs HDTV-LOL)."""
    video_file = "Breaking.Bad.S05E16.Felina.1080p.BluRay.x264-ROVERS.mkv"

    sub_exact = {
        "id": "exact",
        "attributes": {
            "release": "Breaking.Bad.S05E16.Felina.1080p.BluRay.x264-ROVERS",
            "language": "en",
            "download_count": 500
        }
    }

    sub_hdtv = {
        "id": "hdtv",
        "attributes": {
            "release": "Breaking.Bad.S05E16.720p.HDTV.x264-LOL",
            "language": "en",
            "download_count": 5000  # Higher downloads but wrong source/group
        }
    }

    ranked = rank_subtitles([sub_hdtv, sub_exact], video_file, smart_ranking=True, preferred_languages=["en"])
    assert ranked[0]["id"] == "exact", "Exact BluRay-ROVERS release must rank #1 over generic HDTV release"



def test_dev_toggle_blocks_title_fallback():
    """test_disable_query_fallback ON: empty id-search stays empty, no query retry."""
    from unittest.mock import patch
    import xbmcaddon
    from resources.lib.subtitle_downloader import SubtitleDownloader

    addon = xbmcaddon.Addon()
    fallbacks = [{"query": "Nirvanna", "year": "2026", "imdb_id": None}]

    calls = []
    def fake_search(self, query):
        calls.append(dict(query))
        return [], True

    downloader = SubtitleDownloader.__new__(SubtitleDownloader)
    downloader.query = {"imdb_id": 35522483, "languages": "cs,sk"}

    addon.setSetting("test_disable_query_fallback", "true")
    with patch.object(SubtitleDownloader, "_search_subtitles", autospec=True, side_effect=fake_search):
        downloader._run_search_attempts(fallbacks)
    assert len(calls) == 1, f"fallback fired despite dev toggle: {calls}"

    calls.clear()
    addon.setSetting("test_disable_query_fallback", "false")
    with patch.object(SubtitleDownloader, "_search_subtitles", autospec=True, side_effect=fake_search):
        downloader._run_search_attempts(fallbacks)
    assert len(calls) == 2 and calls[1]["query"] == "Nirvanna"
    assert downloader.search_attempts == calls
