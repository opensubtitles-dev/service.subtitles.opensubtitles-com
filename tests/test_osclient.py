import pytest
from unittest.mock import patch, MagicMock
from requests import HTTPError
from resources.lib.osclient.provider import OpenSubtitlesProvider, query_to_params
from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
from resources.lib.exceptions import AuthenticationError

def test_subtitles_request_params():
    req = OpenSubtitlesSubtitlesRequest(query="Inception", languages="en", year=2010)
    params = req.request_params()
    assert params["query"] == "Inception"
    assert params["languages"] == "en"
    assert params["year"] == 2010

def test_query_to_params_dict():
    params = query_to_params({"query": "The Matrix", "languages": "en"}, "OpenSubtitlesSubtitlesRequest")
    assert params["query"] == "The Matrix"
    assert params["languages"] == "en"

def test_provider_init():
    provider = OpenSubtitlesProvider(api_key="test_api_key", username="user", password="pwd")
    assert provider.api_key == "test_api_key"
    assert provider.username == "user"
    assert provider.password == "pwd"

@patch("resources.lib.osclient.provider.Session")
def test_provider_login_success(mock_session_cls):
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"token": "fake_jwt_token", "status": 200}
    mock_resp.raise_for_status.return_value = None
    mock_session.post.return_value = mock_resp

    provider = OpenSubtitlesProvider(api_key="key", username="user", password="pwd")
    provider.login()
    assert provider.user_token == "fake_jwt_token"

@patch("resources.lib.osclient.provider.Session")
def test_provider_login_failure(mock_session_cls):
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    http_error = HTTPError("401 Client Error")
    http_error.response = mock_resp
    mock_resp.raise_for_status.side_effect = http_error
    mock_session.post.return_value = mock_resp

    provider = OpenSubtitlesProvider(api_key="key", username="user", password="wrong_pwd")
    with pytest.raises(AuthenticationError):
        provider.login()

@patch("resources.lib.osclient.provider.Session")
def test_provider_guessit_success_and_caching(mock_session_cls):
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "title": "Border",
        "year": 2018,
        "screen_size": "1080p",
        "type": "movie"
    }
    mock_resp.raise_for_status.return_value = None
    mock_session.get.return_value = mock_resp

    provider = OpenSubtitlesProvider(api_key="key", username="user", password="pwd")
    # First call: hits API and caches
    result1 = provider.guessit("Border.2018.1080p.NF.WEB-DL.mkv")
    assert result1["title"] == "Border"
    assert result1["year"] == 2018
    assert mock_session.get.call_count == 1

    # Second call with same filename: should hit cache and NOT call API again
    result2 = provider.guessit("Border.2018.1080p.NF.WEB-DL.mkv")
    assert result2["title"] == "Border"
    assert mock_session.get.call_count == 1


def test_feature_info_tolerates_malformed_data_shapes():
    # /features returning valid JSON with a malformed non-empty data payload
    # must yield None (id/title fallbacks run), never raise out of the search.
    from unittest.mock import patch, MagicMock
    from resources.lib.osclient.provider import OpenSubtitlesProvider
    p = OpenSubtitlesProvider(api_key="k", username="u", password="w")
    for bad in ({"data": "oops"}, {"data": [None]}, {"data": ["str"]}, {"data": {}},
                {"data": [{"attributes": "not-a-dict"}]}, {"data": [{"attributes": 7}]},
                {"data": [{"attributes": ["list"]}]}):
        resp = MagicMock(status_code=200)
        resp.json.return_value = bad
        with patch.object(p, "cache") as cache, patch.object(p.session, "get", return_value=resp):
            cache.get.return_value = None
            assert p.get_feature_info(imdb_id=123) is None


def test_search_response_with_null_data_raises_provider_error():
    # {"data": null} is valid JSON; it must become ProviderError, not a
    # TypeError from len(None) (mirror-review finding, internal PR #52).
    from unittest.mock import patch, MagicMock
    from resources.lib.osclient.provider import OpenSubtitlesProvider, ProviderError
    import pytest as _pytest
    p = OpenSubtitlesProvider(api_key="k", username="u", password="w")
    for bad in ({"data": None}, {"data": "x"}, {"data": 3}, {}):
        resp = MagicMock(status_code=200)
        resp.json.return_value = bad
        resp.raise_for_status.return_value = None
        with patch.object(p, "cache") as cache, patch.object(p.session, "get", return_value=resp):
            cache.get.return_value = None
            with _pytest.raises(ProviderError):
                p.search_subtitles({"imdb_id": 123, "languages": "en"})


def test_non_object_response_bodies_never_raise_type_errors():
    # Every .json() consumer must survive a top-level non-object body
    # (mirror-review finding, internal PR #53).
    from unittest.mock import patch, MagicMock
    from resources.lib.osclient.provider import OpenSubtitlesProvider, ProviderError
    import pytest as _pytest
    p = OpenSubtitlesProvider(api_key="k", username="u", password="w")
    for body in (None, [], "x", 3):
        resp = MagicMock(status_code=200)
        resp.json.return_value = body
        resp.raise_for_status.return_value = None
        with patch.object(p, "cache") as cache, patch.object(p.session, "get", return_value=resp):
            cache.get.return_value = None
            assert p.get_feature_info(imdb_id=1) is None          # features degrades
            with _pytest.raises(ProviderError):
                p.search_subtitles({"imdb_id": 1, "languages": "en"})  # search -> handled error


@patch("resources.lib.osclient.provider.Session")
def test_provider_guessit_non_object_body(mock_session_cls):
    # Valid JSON that is not an object (list/string/number) must yield None
    # without raising - the success-path log line dereferenced the normalized
    # None with .get() before this guard existed.
    mock_session = MagicMock()
    mock_session_cls.return_value = mock_session
    provider = OpenSubtitlesProvider(api_key="key", username="user", password="pwd")
    for bad in (["list"], "string", 42, None):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = bad
        mock_resp.raise_for_status.return_value = None
        mock_session.get.return_value = mock_resp
        assert provider.guessit(f"NonObject.{bad.__class__.__name__}.mkv") is None


def test_query_to_params_redacts_stream_urls_in_logs():
    # The search query dict carries file_original_path verbatim; when playback
    # is a stream URL its query string can hold an access token. query_to_params
    # logged the raw mapping before request-model filtering.
    import xbmc
    from resources.lib.osclient.provider import query_to_params
    secret = "token=SECRET-STREAM-TOKEN"
    logged = []
    with patch.object(xbmc, "log", side_effect=lambda msg, level=0: logged.append(str(msg))):
        params = query_to_params({"query": "Test Movie", "languages": "en",
                                  "file_original_path": f"http://cdn.example/v.mkv?{secret}"},
                                 "OpenSubtitlesSubtitlesRequest")
    assert "SECRET-STREAM-TOKEN" not in "\n".join(logged)
    assert params.get("query") == "test movie" or "query" in params


def test_subtitles_request_coerces_numeric_strings():
    # Kodi InfoLabels deliver season/episode/year as strings; the request
    # model must coerce them so integer comparisons and the wire format are
    # correct, and reject garbage to None instead of raising.
    from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
    req = OpenSubtitlesSubtitlesRequest(query="Succession", languages="en",
                                        season_number="3", episode_number="4", year="2021",
                                        imdb_id="7660850", parent_imdb_id=" 7660850 ")
    params = req.request_params()
    assert params["season_number"] == 3
    assert params["episode_number"] == 4
    assert params["year"] == 2021
    assert params["imdb_id"] == 7660850
    assert params["parent_imdb_id"] == 7660850

    junk = OpenSubtitlesSubtitlesRequest(query="X", languages="en",
                                         season_number="", episode_number="abc", year=None)
    p2 = junk.request_params()
    assert "season_number" not in p2 and "episode_number" not in p2 and "year" not in p2

    # setters must accept valid values (the old season setter raised on ANY
    # positive season) and still reject true garbage ranges
    req.season_number = "0"          # specials
    assert req.season_number == 0
    req.episode_number = 12
    assert req.episode_number == 12


def test_request_params_keeps_season_zero():
    # Season 0 = specials. Truthiness filtering silently dropped it from the
    # request, searching the whole show instead of the specials season.
    from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
    req = OpenSubtitlesSubtitlesRequest(query="Doctor Who", languages="en",
                                        season_number=0, episode_number=1)
    params = req.request_params()
    assert params["season_number"] == 0
    assert params["episode_number"] == 1


def test_request_setters_accept_valid_values():
    # Three setters were broken since the original module: id raised on every
    # positive value, languages compared instances to class objects with `is`,
    # moviehash called a nonexistent .length(). All valid inputs must work.
    from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
    import pytest as _pytest

    req = OpenSubtitlesSubtitlesRequest(query="X", languages="en")
    req.id = 42
    assert req.id == 42
    with _pytest.raises(ValueError):
        req.id = -1

    req.languages = "sk,cs,en"
    assert req.languages == "sk,cs,en", "value order is preference order - never sorted"
    req.languages = ["en", "fr"]
    assert req.languages == "en,fr"
    with _pytest.raises(ValueError):
        req.languages = "nonsense-lang"
    with _pytest.raises(ValueError):
        req.languages = 42

    req.moviehash = "0123456789abcdef"
    assert req.moviehash == "0123456789abcdef"
    req.moviehash = ""
    assert req.moviehash == ""
    with _pytest.raises(ValueError):
        req.moviehash = "short"


def test_all_numeric_setters_polarity():
    # Every numeric setter accepts valid positive ids (two had inverted
    # comparisons that rejected ALL valid values) and rejects non-positives.
    from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
    import pytest as _pytest
    req = OpenSubtitlesSubtitlesRequest(query="X", languages="en")
    for field in ("id", "imdb_id", "tmdb_id", "user_id", "parent_feature_id",
                  "parent_imdb_id", "parent_tmdb_id", "page"):
        setattr(req, field, 7)
        assert getattr(req, field) == 7, field
        setattr(req, field, "12")
        assert getattr(req, field) == 12, field
        with _pytest.raises(ValueError):
            setattr(req, field, -3)
