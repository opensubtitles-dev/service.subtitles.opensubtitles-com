# 🤖 AI Agent Guidelines & Project Memory

This document provides critical context, architectural rules, and constraints for any AI coding assistant modifying this repository.

---

## 🏛 Project Architecture

- **Add-on ID**: `service.subtitles.opensubtitles-com`
- **Target Platform**: Kodi Matrix (v19), Nexus (v20), Omega (v21), Piers (v22)+ (Python 3 only).
- **Core Components**:
  - `service.py`: Entry point for Kodi subtitle module (`xbmc.subtitle.module`).
  - `test_connection.py`: Standalone script invoked from settings to verify user credentials and API connectivity.
  - `resources/lib/subtitle_downloader.py`: Coordinates subtitle search queries, parsing results, and download dispatching.
  - `resources/lib/data_collector.py`: Extracts video metadata, IMDb/TMDb IDs, filenames, and video hashes from Kodi's player and library.
  - `resources/lib/osclient/`: OpenSubtitles.com REST API client library.
    - `provider.py`: Handles HTTP sessions, authentication JWTs, features lookups, search requests, and downloads.
    - `model/`: Request and response data structures.
  - `resources/lib/cache.py`: Window-property-based caching layer for JSON data.
  - `resources/settings.xml`: User settings definition in Kodi XML format.
  - `resources/language/`: Localization PO translation files.

---

## 🚫 Critical Constraints & Rules (NEVER BREAK)

1. **NO `print()` Statements**: Kodi crashes or logs warnings if `print()` is used in add-ons. ALWAYS use `xbmc.log(msg, level=...)` via `resources.lib.utilities.log`.
2. **NO Credential Logging**: Never log raw passwords, full login response bodies (which contain JWT bearer tokens), or sensitive user headers in debug logs.
3. **`addon.xml` `<news>` Character Limit**: The `<news>` tag in `addon.xml` MUST be strictly under **1500 characters** (`xs:maxLength="1500"`). Full changelog history belongs exclusively in `changelog.txt`.
4. **No Standard Library Shadowing**: Never create packages or files named `os`, `sys`, `json`, etc. (e.g., the API client package is named `osclient`).
5. **Kodi Module Imports**: Kodi extensions (`xbmc`, `xbmcgui`, `xbmcaddon`, `xbmcvfs`, `xbmcplugin`) are provided at runtime by Kodi C++ host. For tests outside Kodi, mocks are defined in `tests/conftest.py`.
6. **Testing Verification**: Always run `python3 -m pytest` before completing tasks to verify no regressions were introduced.

---

## 🛠 Local Tools & Commands

- **Run Unit Tests**: `python3 -m pytest`
- **Stream Kodi Logs**: `./scripts/stream_kodi_logs.sh`
- **Build Clean Release ZIP**: `python3 scripts/build_release_zip.py`
- **Kodi Addon Checker**: `kodi-addon-checker --branch omega .`

---

## 🧪 Testing & Mocking Policy

- **ZERO Real Credentials**: `python3 -m pytest` is 100% isolated and mocked. It NEVER makes real HTTP requests or uses real accounts/passwords. All API responses and Kodi window properties are simulated in `tests/`.
- **Pre-commit Scan**: Before creating any release, `scripts/build_release_zip.py` runs a scan for credentials and bundles only production files.

---

## 🚀 Release Protocol

1. Update version and `<news>` in `addon.xml` (keep `<news>` < 1500 chars).
2. Update `changelog.txt` with complete release notes.
3. Run `python3 -m pytest` and `kodi-addon-checker --branch omega .`.
4. Build clean ZIP via `python3 scripts/build_release_zip.py`.
5. Commit with message: `[service.subtitles.opensubtitles-com] <version>`.
6. Tag with `v<version>` and push branch & tags to GitHub.

