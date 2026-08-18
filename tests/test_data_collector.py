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
