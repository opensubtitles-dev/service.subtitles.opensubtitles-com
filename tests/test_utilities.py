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
    """One UA everywhere: 'Opensubtitles.com Kodi plugin v<version>' (v2.0.0 policy)."""
    from resources.lib.utilities import get_user_agent

    ua = get_user_agent()
    assert ua.startswith("Opensubtitles.com Kodi plugin v")

    # No file may define its own User-Agent string anymore
    import pathlib
    offenders = []
    for path in pathlib.Path(".").rglob("*.py"):
        if "tests" in path.parts or "scratchpad" in str(path):
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
