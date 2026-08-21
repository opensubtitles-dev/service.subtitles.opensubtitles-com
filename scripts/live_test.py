#!/usr/bin/env python3
"""
Live Integration & User Simulation Tool for OpenSubtitles.com Kodi Add-on
Simulates real search, feature lookup, and subtitle download over live network.
"""

import os
import sys
import argparse
import requests

# Ensure repository root is at the very top of sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Setup mock Kodi environment for standalone execution
from unittest.mock import MagicMock
if "xbmc" not in sys.modules:
    xbmc_mock = MagicMock()
    xbmc_mock.LOGDEBUG = 0
    xbmc_mock.log = MagicMock()
    sys.modules["xbmc"] = xbmc_mock
if "xbmcaddon" not in sys.modules:
    addon_mock = MagicMock()
    addon_mock.Addon.return_value.getSetting.return_value = "5"
    addon_mock.Addon.return_value.getAddonInfo.return_value = "service.subtitles.opensubtitles-com"
    sys.modules["xbmcaddon"] = addon_mock
if "xbmcgui" not in sys.modules:
    class MockWindow:
        _store = {}
        def __init__(self, *args): pass
        def getProperty(self, k): return self._store.get(k, "")
        def setProperty(self, k, v): self._store[k] = str(v)
    sys.modules["xbmcgui"] = MagicMock(Window=MockWindow)


from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
from resources.lib.osclient.model.request.download import OpenSubtitlesDownloadRequest

DEFAULT_API_KEY = "qo2wQs1PXwIHJsXvIiWXu1ZbVjaboPh6"

def load_env_file():
    """Load credentials from .env if present"""
    env_path = os.path.join(REPO_ROOT, ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))

def main():
    load_env_file()

    parser = argparse.ArgumentParser(description="Live OpenSubtitles.com API Tester & Simulator")
    parser.add_argument("--user", default=os.getenv("OPENSUBTITLES_USER"), help="OpenSubtitles.com Username")
    parser.add_argument("--pass", dest="password", default=os.getenv("OPENSUBTITLES_PASS"), help="OpenSubtitles.com Password")
    parser.add_argument("--api-key", default=os.getenv("OPENSUBTITLES_API_KEY", DEFAULT_API_KEY), help="API Key")
    parser.add_argument("--query", default="The Matrix", help="Movie or Show search query")
    parser.add_argument("--imdb-id", default="0133093", help="IMDb ID to search (e.g. 0133093 for The Matrix)")
    parser.add_argument("--languages", default="en", help="Comma-separated language codes (e.g. en,es,fr)")
    parser.add_argument("--download", action="store_true", help="Download the first matching subtitle file")
    args = parser.parse_args()

    print("========================================================")
    print(" 🎬 OpenSubtitles.com Live User Simulator")
    print("========================================================")

    provider = OpenSubtitlesProvider(
        api_key=args.api_key,
        username=args.user or "",
        password=args.password or ""
    )

    # 1. Authentication Check
    if args.user and args.password:
        print(f"\n🔐 [1/5] Authenticating as '{args.user}'...")
        try:
            provider.login()
            print(" Login successful! Session token acquired.")
            
            user_info = provider.get_user_info()
            print(f"    - Level: {user_info.get('level', 'User')}")
            print(f"    - VIP Status: {'Yes' if user_info.get('vip') else 'No'}")
            print(f"    - Downloads Today: {user_info.get('downloads_count', 0)} / {user_info.get('allowed_downloads', 'N/A')}")
            print(f"    - Remaining Downloads: {user_info.get('remaining_downloads', 'N/A')}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            sys.exit(1)
    else:
        print("\nℹ️ [1/5] No credentials provided; proceeding in anonymous/public mode.")

    # 2. Text Search Simulation
    print(f"\n🔎 [2/5] Simulating movie title search: query='{args.query}', languages='{args.languages}'...")
    try:
        search_req = OpenSubtitlesSubtitlesRequest(query=args.query, languages=args.languages)
        results = provider.search_subtitles(search_req)
        if results:
            print(f" Found {len(results)} subtitle results!")
            first_match = results[0]
            attrs = first_match.get("attributes", {})
            files = attrs.get("files", [{}])
            print(f"    Top result: {attrs.get('release', 'Unknown')}")
            print(f"    Language: {attrs.get('language')} | Downloads: {attrs.get('download_count')} | Rating: {attrs.get('ratings')}")
            file_id = files[0].get("file_id") if files else None
        else:
            print("⚠️ No subtitles found for query.")
            first_match = None
            file_id = None
    except Exception as e:
        print(f"❌ Search error: {e}")
        first_match = None
        file_id = None

    # 3. IMDb Search Simulation
    if args.imdb_id:
        print(f"\n🎯 [3/5] Simulating IMDb ID search: imdb_id={args.imdb_id}, languages='{args.languages}'...")
        try:
            imdb_req = OpenSubtitlesSubtitlesRequest(imdb_id=int(args.imdb_id), languages=args.languages)
            imdb_results = provider.search_subtitles(imdb_req)
            print(f" IMDb search returned {len(imdb_results) if imdb_results else 0} results.")
        except Exception as e:
            print(f"❌ IMDb search error: {e}")

    # 4. Features API Lookup
    print(f"\n📺 [4/5] Testing /features API for episode/show identification...")
    try:
        feature_info = provider.get_feature_info(imdb_id=args.imdb_id)
        if feature_info:
            print(f" Feature type: {feature_info.get('feature_type')} - Title: {feature_info.get('title')} ({feature_info.get('year')})")
        else:
            print(" Feature lookup returned no details (or not in cache).")
    except Exception as e:
        print(f"❌ Feature lookup error: {e}")

    # 5. Download Simulation
    if args.download and file_id:
        print(f"\n⬇️ [5/5] Simulating Subtitle Download for file_id={file_id}...")
        try:
            dl_req = OpenSubtitlesDownloadRequest(file_id=file_id)
            dl_res = provider.download_subtitle(dl_req)
            download_link = dl_res.get("link")
            print(f" Download URL received: {download_link[:60]}...")
            
            # Fetch actual subtitle stream
            resp = requests.get(download_link, timeout=15)
            resp.raise_for_status()
            content_preview = resp.text[:200]
            print(" Subtitle file downloaded successfully!")
            print(f"    Size: {len(resp.content)} bytes")
            print(f"    Preview:\n---\n{content_preview}\n---")
        except Exception as e:
            print(f"❌ Download error: {e}")
    elif not args.download:
        print("\n💡 [5/5] Download simulation skipped (pass --download to test downloading).")

    print("\n========================================================")
    print(" Live simulation completed!")
    print("========================================================")

if __name__ == "__main__":
    main()
