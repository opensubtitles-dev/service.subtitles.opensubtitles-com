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
