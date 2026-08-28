from resources.lib.utilities import normalize_string, get_params

def test_normalize_string():
    import unicodedata
    decomposed = unicodedata.normalize("NFD", "Gräns")
    assert len(decomposed) == 6  # 'a' + combining diaeresis
    normalized = normalize_string(decomposed)
    assert len(normalized) == 5  # 'ä' precomposed
    assert normalized == "Gräns"

def test_get_params_from_string():
    query_str = "action=search&languages=en,es&imdb_id=12345"
    params = get_params(query_str)
    assert params["action"] == "search"
    assert params["languages"] == "en,es"
    assert params["imdb_id"] == "12345"
import time
import xbmcaddon
from resources.lib.utilities import check_and_get_account_status

def test_account_status_24h_expiration_active():
    addon = xbmcaddon.Addon()
    # Verified 1 hour ago
    one_hour_ago = str(int(time.time() - 3600))
    addon.setSetting("account_verified_at", one_hour_ago)
    addon.setSetting("account_status", "OK: VIP | 993/1000 left | Checked: 2026-08-18 14:00")
    
    status = check_and_get_account_status()
    assert status.startswith("OK: VIP")

def test_account_status_24h_expiration_expired():
    addon = xbmcaddon.Addon()
    # Verified 25 hours ago (> 86400s)
    twenty_five_hours_ago = str(int(time.time() - 90000))
    addon.setSetting("account_verified_at", twenty_five_hours_ago)
    addon.setSetting("account_status", "OK: VIP | 993/1000 left")
    
    status = check_and_get_account_status()
    assert "Expired (>24h)" in status


def test_single_user_agent_policy():
    """One UA everywhere: 'Opensubtitles.com Kodi plugin v<version>'."""
    from resources.lib.utilities import get_user_agent

    ua = get_user_agent()
    assert ua.startswith("Opensubtitles.com Kodi plugin v")

    import pathlib
    offenders = []
    for path in pathlib.Path(".").rglob("*.py"):
        if "tests" in path.parts:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "User-Agent" in line and "get_user_agent()" not in line and '"""' not in line:
                offenders.append(f"{path}:{n}")
    assert not offenders, f"hardcoded User-Agent found: {offenders}"


def test_get_install_origin_unknown_when_db_unreadable():
    # Test environment has no Kodi addon database - helper must degrade to
    # 'unknown' instead of raising, and never break a search.
    import resources.lib.utilities as utilities
    utilities._install_origin = None
    assert utilities.get_install_origin() == "unknown"
    utilities._install_origin = None


def test_provider_sends_origin_header():
    from unittest.mock import patch
    with patch("resources.lib.osclient.provider.get_install_origin",
               return_value="repository.opensubtitles-com"):
        from resources.lib.osclient.provider import OpenSubtitlesProvider
        p = OpenSubtitlesProvider(api_key="k", username="u", password="p")
        assert p.request_headers["X-Kodi-Origin-Repo"] == "repository.opensubtitles-com"


def test_redact_path_strips_percent_encoded_tokens():
    """'%3Ftoken%3D...' hides a query inside the PATH component - decode and
    strip again, same trap safe_media_filename covers."""
    from resources.lib.utilities import redact_path
    out = redact_path("http://cdn.example/video%3Ftoken%3DSECRET-ENC-TOKEN.mkv")
    assert "SECRET-ENC-TOKEN" not in out
    assert "redacted" in out
    # plain paths and clean URLs unaffected
    assert redact_path("/movies/Title (2024).mkv") == "/movies/Title (2024).mkv"
    assert redact_path("http://cdn.example/video.mkv") == "http://cdn.example/video.mkv"


def test_redaction_helpers_decode_nested_encoding():
    """Double- and triple-encoded delimiters must surface and be stripped in
    BOTH helpers - one unquote pass left '%253F...' hiding a token."""
    from resources.lib.utilities import redact_path, safe_media_filename
    for url in ("http://cdn.example/video%253Ftoken%253DSECRET-N2.mkv",
                "http://cdn.example/video%25253Ftoken%25253DSECRET-N3.mkv"):
        assert "SECRET-N" not in redact_path(url)
        assert "SECRET-N" not in safe_media_filename(url)
    assert safe_media_filename("http://cdn.example/video%253Ftoken%253Dx.mkv") == "video"


def test_redaction_fails_closed_on_absurd_encoding_depth():
    """A delimiter encoded beyond the decode bound must never pass through as
    residue - both helpers fail closed."""
    from resources.lib.utilities import redact_path, safe_media_filename
    from urllib.parse import quote
    payload = "?token=SECRET-DEEP"
    for _ in range(25):
        payload = quote(payload, safe="")
    url = f"http://cdn.example/video{payload}.mkv"
    assert "SECRET-DEEP" not in redact_path(url)
    assert "%" not in redact_path(url).split("://", 1)[1].split("  ")[0].replace("[path redacted]", "")
    assert safe_media_filename(url) == ""


def test_get_params_always_returns_dict():
    """An empty query string used to return a LIST - params.get() then
    crashed with a type error."""
    from resources.lib.utilities import get_params
    import sys
    from unittest.mock import patch
    with patch.object(sys, "argv", ["plugin://x"]):     # short argv: RunScript-style
        assert get_params() == {}
    assert isinstance(get_params("x"), dict)
    assert get_params("action=search&languages=en") == {"action": "search", "languages": "en"}


def test_redact_path_strips_percent_encoded_userinfo():
    """'user%3Apass%40host' hides credentials in the AUTHORITY - decode the
    netloc to fixpoint before splitting them off."""
    from resources.lib.utilities import redact_path
    out = redact_path("http://user%3ASECRET-USERPASS%40cdn.example/video.mkv")
    assert "SECRET-USERPASS" not in out
    assert "cdn.example" in out and "redacted" in out
