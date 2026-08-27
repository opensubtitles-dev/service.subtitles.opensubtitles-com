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
