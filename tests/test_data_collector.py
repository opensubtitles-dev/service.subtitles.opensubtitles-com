from resources.lib.data_collector import (
    _strip_imdb_tt,
    _extract_basic_tv_info,
    _get_cache_key,
    _is_cache_valid
)

def test_strip_imdb_tt():
    assert _strip_imdb_tt("tt0133093") == "0133093"
    assert _strip_imdb_tt("0133093") == "0133093"
    assert _strip_imdb_tt("ttabc") is None
    assert _strip_imdb_tt("") is None
    assert _strip_imdb_tt(None) is None

def test_extract_basic_tv_info_s01e02():
    show, season, episode = _extract_basic_tv_info("Breaking.Bad.S02E05.720p.mkv")
    assert show == "Breaking Bad"
    assert season == "02"
    assert episode == "05"

def test_extract_basic_tv_info_1x01():
    show, season, episode = _extract_basic_tv_info("The.Wire.1x03.avi")
    assert show == "The Wire"
    assert season == "1"
    assert episode == "03"

def test_cache_key_generation():
    key1 = _get_cache_key("test_method", {"param": 1})
    key2 = _get_cache_key("test_method", {"param": 1})
    key3 = _get_cache_key("test_method", {"param": 2})
    assert key1 == key2
    assert key1 != key3

def test_call_guessit_api_caching():
    from unittest.mock import patch, MagicMock
    import json
    from resources.lib.data_collector import _call_guessit_api

    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = json.dumps({"title": "Parasite", "year": 2019, "type": "movie"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        # First call hits API
        res1 = _call_guessit_api("Parasite.2019.1080p.BluRay.mkv")
        assert res1["title"] == "Parasite"
        assert mock_urlopen.call_count == 1

        # Second call hits cache
        res2 = _call_guessit_api("Parasite.2019.1080p.BluRay.mkv")
        assert res2["title"] == "Parasite"
        assert mock_urlopen.call_count == 1


def test_language_override_forces_single_language():
    import xbmcaddon
    from resources.lib.data_collector import get_language_data

    addon = xbmcaddon.Addon()
    addon.setSetting("test_override_language", "sk")
    try:
        data = get_language_data({"languages": "English,Czech", "preferredlanguage": "German"})
        assert data["languages"] == "sk"
    finally:
        addon.setSetting("test_override_language", "")


def test_override_rejects_unknown_codes():
    import xbmcaddon
    from resources.lib.utilities import get_language_override

    addon = xbmcaddon.Addon()
    addon.setSetting("test_override_language", "xx")
    try:
        assert get_language_override() == ""
    finally:
        addon.setSetting("test_override_language", "")


def test_preferred_language_is_converted_not_seeded_raw():
    """Regression: wire carried ',English,cs,sk' - leading comma + raw English name."""
    from resources.lib.data_collector import get_language_data

    data = get_language_data({"languages": "Czech,Slovak", "preferredlanguage": "English"})

    assert not data["languages"].startswith(","), "leading comma leaked again"
    assert "English" not in data["languages"], "raw language name leaked again"
    parts = data["languages"].split(",")
    assert "en" in parts and "cs" in parts and "sk" in parts


def test_specials_detection_only_matches_bare_s_labels():
    """'S01E05'-style compound labels must pass through untouched; only a bare
    'sN' label marks a special (season 0)."""
    from unittest.mock import patch
    import xbmc
    from resources.lib import data_collector

    def run(label):
        labels = {"VideoPlayer.Year": "", "VideoPlayer.Season": "2",
                  "VideoPlayer.Episode": label, "VideoPlayer.TVshowtitle": "Show",
                  "VideoPlayer.OriginalTitle": "", "VideoPlayer.TvShowDBID": "",
                  "VideoPlayer.Title": "Show"}
        with patch.object(xbmc, "getInfoLabel", side_effect=lambda k: labels.get(k, "")), \
             patch.object(data_collector, "get_file_path", return_value="/tv/x.mkv"), \
             patch.object(data_collector, "_jsonrpc", return_value=None):
            return data_collector.get_media_data()

    special = run("s3")
    assert special["season_number"] == "0" and special["episode_number"] == "3"

    compound = run("S01E05")
    assert compound["season_number"] != "0"
    assert compound["episode_number"] == "S01E05"


def test_infolabel_log_redacts_url_values():
    """An InfoLabel carrying a tokened URL must be redacted in the initial
    media-data log line."""
    import xbmc
    from unittest.mock import patch
    from resources.lib import data_collector

    labels = {"VideoPlayer.Year": "", "VideoPlayer.Season": "",
              "VideoPlayer.Episode": "", "VideoPlayer.TVshowtitle": "",
              "VideoPlayer.OriginalTitle": "http://cdn.example/t.mkv?token=SECRET-IL-TOKEN",
              "VideoPlayer.TvShowDBID": "", "VideoPlayer.Title": ""}
    logged = []
    with patch.object(xbmc, "getInfoLabel", side_effect=lambda k: labels.get(k, "")), \
         patch.object(data_collector, "get_file_path", return_value="/m/x.mkv"), \
         patch.object(data_collector, "_jsonrpc", return_value=None), \
         patch.object(xbmc, "log", side_effect=lambda msg, level=0: logged.append(str(msg))):
        data_collector.get_media_data()
    assert "SECRET-IL-TOKEN" not in "\n".join(l for l in logged if "Initial media data" in l)


def test_clean_feature_release_name_tolerates_none_fields():
    from resources.lib.data_collector import clean_feature_release_name, get_flag
    assert clean_feature_release_name("Title", None) .startswith("Title")
    assert clean_feature_release_name(None, "Rel.2024") == "Rel.2024"
    assert get_flag(None) == ""


def test_movie_title_attempt_validates_year():
    """A pre-1927 or garbage InfoLabel year must not enter the title retry."""
    from resources.lib.data_collector import _valid_year
    assert _valid_year("1900") == ""
    assert _valid_year("2024") == "2024"
    assert _valid_year("soon") == ""
