# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Official Kodi subtitle add-on (`service.subtitles.opensubtitles-com`) for OpenSubtitles.com, built on its REST API. Python 3 only, targets Kodi Matrix (19) through Piers (22). Licensed GPL-2.0.

Companion docs (keep in sync when workflows change): `DEV_WORKFLOW.md` (dev/release workflow), `KODI_STANDARDS.md` (Kodi repo compliance), `AGENT_INSTRUCTIONS.md` (AI agent rules), `HANDOVER.md` (current branch state and in-flight features), `TODO.md` (roadmap), `docs/kodi_api_internals.md` (Kodi Python API ground truth: subtitle plugin contract, Player/Monitor semantics, JSON-RPC, gotchas — read before touching service.py or service_monitor.py), `docs/kodi_ui_font_compatibility.md` (glyph/emoji rendering matrix).

## Commands

```bash
# Run full test suite — fully mocked, no network, no real credentials
python3 -m pytest

# Run a single test file / single test
python3 -m pytest tests/test_matcher.py
python3 -m pytest tests/test_matcher.py::test_name

# Live tests against real OpenSubtitles.com API (excluded by default via addopts -m "not live")
python3 -m pytest -m live

# Live end-to-end simulation (credentials via flags or gitignored .env with OPENSUBTITLES_USER/OPENSUBTITLES_PASS)
python3 scripts/live_test.py --query "The Matrix" --download

# Kodi repo compliance validation (run before any release; must pass with 0 problems)
kodi-addon-checker --branch omega .    # also: piers, nexus, matrix

# Build clean release ZIP (runs credential scan, bundles only production files,
# strips the Development settings tab via scripts/release_lib.py - end users never see it)
python3 scripts/build_release_zip.py

# Generate repository ZIPs + addons.xml + checksums (for the GitHub Pages repo)
python3 scripts/generate_repo.py

# Stream live Kodi logs while testing in Kodi (enable debug logging in Kodi first)
./scripts/stream_kodi_logs.sh
```

### Development in Kodi

Symlink the repo into Kodi's addons directory once — the subtitle plugin side (`service.py` and everything it imports) spawns a fresh process per search, so those edits are instantly active (no reinstall). **The background service (`service_monitor.py`) is one long-lived process started at Kodi launch — its edits require a Kodi restart** (or disabling and re-enabling the add-on) to take effect. macOS:

```bash
ln -s "$(pwd)" "$HOME/Library/Application Support/Kodi/addons/service.subtitles.opensubtitles-com"
```

Changes to `resources/settings.xml` or `addon.xml` require reopening the Kodi settings dialog or restarting Kodi.

## Architecture

Two Kodi extension points declared in `addon.xml`:

1. **`xbmc.subtitle.module`** (`service.py`) — on-demand entry point. Each subtitle search/download spawns a fresh Python process. Flow: `service.py` → `resources/lib/subtitle_downloader.py` (orchestrates search, result parsing, badge formatting, download dispatch) which uses:
   - `resources/lib/data_collector.py` — extracts video metadata, IMDb/TMDb IDs, filenames, and hashes from Kodi's player/library.
   - `resources/lib/osclient/` — REST API client (deliberately named `osclient`, never `os`). `provider.py` owns HTTP sessions, JWT auth, features lookup, search, download, and voting; `model/` holds request/response structures.
   - `resources/lib/matcher.py` — match scoring and display badge formatting (`get_match_display_tag`).
   - `resources/lib/cache.py` — Kodi window-property-based JSON cache (search results, guessit lookups).

2. **`xbmc.service`** (`service_monitor.py`) — background service running `OpenSubtitlesMonitor(xbmc.Monitor)` + `OpenSubtitlesPlayer(xbmc.Player)`. Handles background account/quota refresh (guarded by a non-blocking `threading.Lock`), silent auto-download on `onAVStarted`, and post-playback rating prompts. **Zero-hang shutdown**: main loop is `while not monitor.abortRequested(): monitor.waitForAbort(1)`, and background threads must check `monitor.abortRequested()` before network calls.

`test_connection.py` and `check_updates.py` are standalone scripts invoked from the settings UI (credential/VIP/quota verification, update check).

### Testing model

Kodi modules (`xbmc`, `xbmcgui`, `xbmcaddon`, `xbmcvfs`, `xbmcplugin`) exist only inside Kodi's C++ host — `tests/conftest.py` provides mocks for everything. Default pytest run is 100% offline; network tests are opt-in via the `live` marker.

## Critical Constraints (never break)

- **Never invent REST API endpoints.** Every method in `resources/lib/osclient/provider.py` must exist in the official OpenAPI spec: `https://stoplight.io/api/v1/projects/opensubtitles/opensubtitles-api/nodes/open_api.json`. Endpoints designed ahead of the spec (e.g. `rate_subtitle`) must be marked PROPOSED in their docstring with the agreed contract and handle 404 as "not deployed yet".

- **No `print()`** — use `xbmc.log()` via the logging helper in `resources/lib/utilities.py`. `print()` breaks Kodi.
- **No credential logging** — never log passwords, JWT bearer tokens, full login response bodies, or sensitive headers.
- **`addon.xml` `<news>` must stay under 1500 characters** (schema limit). Full history goes in `changelog.txt` only.
- **Never shadow stdlib module names** (that's why the API client is `osclient`).
- **Run `python3 -m pytest` before completing any task.**

## Kodi UI Gotchas

- `resources/settings.xml`: `<control type="label">` is invalid and breaks settings loading. For read-only display rows use `<control type="edit" format="string">` with a permanently-false enable dependency (pattern in `KODI_STANDARDS.md`).
- Emojis render as blank boxes in default Kodi fonts. Use `[COLOR ...]`, `[B]`, BMP glyphs (`★ • ✔`) instead — full compatibility matrix in `docs/kodi_ui_font_compatibility.md`.
- Don't duplicate native dialog icons in text: `sync="true"` already shows hash-match, `hearing_imp="true"` already shows SDH.
- Visual badges go at the **end** of the release title (label2): `[Release Title] [Trusted] [AI] [Machine] [Forced] (+MatchScore)`.
- Debug setting `test_flag_interceptor` makes every search return mock subtitles (from `_inject_test_flag_subtitles()`) for badge/glyph UI testing.

## Release Process

Full checklist in `DEV_WORKFLOW.md` §6. Summary: bump `version=` and `<news>` in `addon.xml` → update `changelog.txt` → `python3 -m pytest` + `kodi-addon-checker --branch omega .` → `python3 scripts/build_release_zip.py` → commit as `[service.subtitles.opensubtitles-com] x.y.z` → tag `vx.y.z` → push. Submissions to `xbmc/repo-plugins` require exactly one squashed commit with that title format.

Check `HANDOVER.md` before starting work — it records which branch is frozen (pending upstream PR) vs. active development.
