import pytest
import os
import requests
from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
from resources.lib.osclient.model.request.download import OpenSubtitlesDownloadRequest

DEFAULT_API_KEY = "qo2wQs1PXwIHJsXvIiWXu1ZbVjaboPh6"

def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

_load_env()

@pytest.mark.live
def test_live_authentication():
    user = os.getenv("OPENSUBTITLES_USER")
    pwd = os.getenv("OPENSUBTITLES_PASS")
    if not user or not pwd:
        pytest.skip("No credentials provided in .env")

    provider = OpenSubtitlesProvider(
        api_key=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY),
        username=user,
        password=pwd
    )
    provider.login()
    assert provider.user_token is not None
    user_info = provider.get_user_info()
    assert "level" in user_info
    assert "remaining_downloads" in user_info

@pytest.mark.live
def test_live_search_subtitles():
    provider = OpenSubtitlesProvider(
        api_key=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY),
        username=os.getenv("OPENSUBTITLES_USER", ""),
        password=os.getenv("OPENSUBTITLES_PASS", "")
    )
    req = OpenSubtitlesSubtitlesRequest(query="The Matrix", languages="en")
    results = provider.search_subtitles(req)
    assert results is not None
    assert len(results) > 0
    assert "attributes" in results[0]

@pytest.mark.live
def test_live_tv_show_search():
    provider = OpenSubtitlesProvider(
        api_key=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY),
        username=os.getenv("OPENSUBTITLES_USER", ""),
        password=os.getenv("OPENSUBTITLES_PASS", "")
    )
    req = OpenSubtitlesSubtitlesRequest(query="Breaking Bad", season_number=1, episode_number=1, languages="en")
    results = provider.search_subtitles(req)
    assert results is not None
    assert len(results) > 0

@pytest.mark.live
def test_live_features_lookup():
    provider = OpenSubtitlesProvider(
        api_key=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY),
        username="",
        password=""
    )
    features = provider.get_feature_info(imdb_id="0133093")
    assert features is not None
    assert features.get("feature_type") == "Movie"

@pytest.mark.live
def test_live_download_subtitle():
    provider = OpenSubtitlesProvider(
        api_key=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY),
        username=os.getenv("OPENSUBTITLES_USER", ""),
        password=os.getenv("OPENSUBTITLES_PASS", "")
    )
    req = OpenSubtitlesSubtitlesRequest(query="The Matrix", languages="en")
    results = provider.search_subtitles(req)
    assert results and len(results) > 0
    file_id = results[0]["attributes"]["files"][0]["file_id"]
    
    dl_res = provider.download_subtitle(OpenSubtitlesDownloadRequest(file_id=file_id))
    assert "link" in dl_res
    
    resp = requests.get(dl_res["link"], timeout=15)
    assert resp.status_code == 200
from resources.lib.exceptions import AuthenticationError, BadUsernameError, TooManyRequests

@pytest.mark.live
def test_live_401_invalid_credentials():
    """Verify live API returns 401 AuthenticationError when credentials are fake."""
    provider = OpenSubtitlesProvider(
        api_key=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY),
        username="totally_fake_nonexistent_user_99999",
        password="wrong_password_12345"
    )
    with pytest.raises(AuthenticationError) as exc_info:
        provider.login()
    assert "401" in str(exc_info.value) or "Login failed" in str(exc_info.value)

@pytest.mark.live
def test_live_400_email_in_username():
    """Verify live API handles email in username or rate limiting gracefully."""
    import time
    time.sleep(1)
    provider = OpenSubtitlesProvider(
        api_key=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY),
        username="test_user@example.com",
        password="some_password_123"
    )
    with pytest.raises((BadUsernameError, TooManyRequests, AuthenticationError)):
        provider.login()
