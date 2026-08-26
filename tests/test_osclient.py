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


def test_nocache_toggle_adds_param_and_bypasses_local_cache():
    """Dev toggle: nocache=1 goes to the API and the local search cache is skipped."""
    from unittest.mock import MagicMock, patch
    import xbmcaddon
    from resources.lib.osclient.provider import OpenSubtitlesProvider

    addon = xbmcaddon.Addon()
    addon.setSetting("test_nocache", "true")
    addon.setSetting("search_cache_duration", "180")

    provider = OpenSubtitlesProvider("key", "user", "pass")
    provider.cache = MagicMock()
    response = MagicMock()
    response.json.return_value = {"data": [], "total_pages": 1}
    response.status_code = 200

    with patch.object(provider.session, "get", return_value=response) as http_get:
        provider.search_subtitles({"query": "The Matrix", "languages": "sk"})

    sent = http_get.call_args.kwargs.get("params") or http_get.call_args[0][1] if http_get.call_args else {}
    assert sent.get("nocache") == 1
    # Local SEARCH cache bypassed (the only cache.get allowed is the JWT lookup)
    for call in provider.cache.get.call_args_list:
        assert call.kwargs.get("key") == "user_token", f"search cache consulted: {call}"
    provider.cache.set.assert_not_called()   # and nothing gets stored either
    addon.setSetting("test_nocache", "")     # don't leak into other tests


def test_download_retries_through_ai_translation_timeout():
    """Read timeout on /download = translation still running server-side; the
    client waits and re-POSTs instead of failing the first click (live bug)."""
    from unittest.mock import MagicMock, patch
    from requests import ReadTimeout
    from resources.lib.osclient.provider import OpenSubtitlesProvider

    provider = OpenSubtitlesProvider("key", "user", "pass")
    provider.cache = MagicMock()
    provider.cache.get.return_value = "jwt-token"

    ok = MagicMock()
    ok.url = "https://api.opensubtitles.com/api/v1/download"
    ok.status_code = 200
    ok.json.return_value = {"link": "https://dl.opensubtitles.com/file.srt"}
    content = MagicMock(); content.content = b"1\n00:00:01,000 --> 00:00:02,000\nAhoj\n"
    content.raise_for_status = MagicMock()

    calls = {"n": 0}
    def post(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ReadTimeout("read timeout=30")
        return ok

    with patch.object(provider.session, "post", side_effect=post), \
         patch.object(provider.session, "get", return_value=content), \
         patch("resources.lib.osclient.provider.time.sleep") as sleep:
        result = provider.download_subtitle({"file_id": 1246448409911500000000000000000000})

    assert calls["n"] == 2          # timed out once, succeeded on retry
    sleep.assert_called_once_with(5)
    assert result["content"].startswith(b"1\n")


def test_feature_info_tolerates_malformed_data_shapes():
    # /features returning valid JSON with a malformed non-empty data payload
    # must yield None (id/title fallbacks run), never raise out of the search.
    from unittest.mock import patch, MagicMock
    from resources.lib.osclient.provider import OpenSubtitlesProvider
    p = OpenSubtitlesProvider(api_key="k", username="u", password="w")
    for bad in ({"data": "oops"}, {"data": [None]}, {"data": ["str"]}, {"data": {}}):
        resp = MagicMock(status_code=200)
        resp.json.return_value = bad
        with patch.object(p, "cache") as cache, patch.object(p.session, "get", return_value=resp):
            cache.get.return_value = None
            assert p.get_feature_info(imdb_id=123) is None
