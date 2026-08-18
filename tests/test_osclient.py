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
