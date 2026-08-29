# OpenSubtitles.com Kodi Add-on - Development Handover

This file provides a complete technical handover for Claude / next AI agent taking over the codebase.

---

## 1. 📍 Repository & Branch Overview

* **Repository Directory**: `/data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com`
* **Remote naming wrinkle (memorize)**: local names are inverted from intuition.
  * `fork` = `opensubtitles/service.subtitles.opensubtitles-com` - the WORKBENCH. `develop` tracks `fork/develop`; all routine pushes land here (pre-push preflight gate). Users never see it.
  * `origin` = `opensubtitles-dev/service.subtitles.opensubtitles-com` - the MAIN repo (issues, CI, releases). Its master is a LIVE TRIGGER: every push auto-rebuilds gh-pages via `deploy-repository.yml` and publishes to `https://kodi.opensubtitles.com` (the URL baked into every installed repository add-on). Push `origin` master only as a deliberate release act.
* **Branch Strategy**:
  * **`fix-kodi-http-browse` (= both masters)**: the COMPLETED 1.x line, ended at v1.0.91. The official submission is **xbmc/repo-scripts PR #2888** (v1.0.90, Greptile 5/5, awaiting human Team Kodi review). HARD RULE: no xbmc/* PR action without Brano's approval given TWICE, and no further 1.x work unless explicitly asked.
  * **`develop`**: **THE ONLY ACTIVE LINE** (v2.0.0). Everything happens here: background service (auto-download, rating prompts, account alerts, update checks), AI transcription with the 6-rung audio extraction ladder (ffmpeg / Android-NDK-ctypes / afconvert / GStreamer / Windows-MF-ctypes / pure-Python demux - see docs/audio_support_matrix.md, all device/CI-verified), subtitle-sync plumbing awaiting the external `subsync` engine (resources/lib/syncer.py socket), upload dry-run, QR/credits flows, Retry-After rate-limit courtesy.

---

## 2. 🧪 Testing & Validation Commands

```bash
# Run complete test suite (307 passing tests)
python3 -m pytest

# Run repository packager and generate ZIPs + addons.xml + checksums
python3 scripts/generate_repo.py
```

---

## 3. 🏗️ Key Architecture & Features on `develop`

### A. Kodi Background Service (`service_monitor.py`)
* Declared in `addon.xml`: `<extension point="xbmc.service" library="service_monitor.py" />`.
* Implements `OpenSubtitlesMonitor(xbmc.Monitor)` and `OpenSubtitlesPlayer(xbmc.Player)`.
* **Zero-Hang Shutdown Guarantee**:
  * The main loop uses `while not monitor.abortRequested(): monitor.waitForAbort(1)`.
  * Background threads check `monitor.abortRequested()` before network calls to prevent Kodi exit delays.
* **Account state: SINGLE WRITER architecture (v2.0.0 decision, 2026-08-20)**:
  * The service does NOT validate credentials or write account settings. `test_connection.py`
    ("TEST CONNECTION" button) is the only writer of `account_*` / `ai_credits` settings and
    of the authoritative `account_state.json` (addon profile). Rationale: the settings dialog
    saves a full snapshot on close (also across RunScript), the plugin runs in a separate
    process, and concurrent writers tore each other's values live. Never reintroduce a
    service-side account refresh.
  * The service's only account job is `_reconcile_account_display()`: on every
    `onSettingsChanged`, wait for the dialog to close, then restore any settings fields a
    dialog snapshot reverted, from `account_state.json`. Read-only against the API.
* **Daily update check** (`check_for_update_silently`): hourly probe, 24h spacing persisted
  in `update_check.json` (own file - settings snapshots cannot clobber it); result shown in
  the read-only "Update last checked" row (Expert level).
* **Multi-language Auto-Download on Video Playback**:
  * `OpenSubtitlesPlayer.onAVStarted()` → background thread: JSON-RPC probe for an actively
    displayed subtitle, standdown when Kodi's own `subtitles.downloadfirst` is enabled, one
    search across all of Kodi's preferred subtitle languages, best pick per language
    (max 5), primary applied via `setSubtitles()`, others added via JSON-RPC
    `Player.AddSubtitle`. Files stored per Kodi's `subtitles.storagemode` with Kodi naming
    (`<video>.<lang>.srt`). On-demand AI entries are always skipped (they cost credits).
* **Post-Playback Rating Prompt**:
  * `_prompt_rating()`: 1-5 star `select()` + in-sync `yesnocustom()` (autoclose, dismiss
    sends nothing), submitted via `provider.rate_subtitle(subtitle_id, rating, sync=)` to
    the PROPOSED `POST /subtitles/rate` endpoint (404-tolerant until the API ships it).
* **Auto-Upload dry run** (dev toggle `auto_upload_subtitles`): per-session eligibility
  resume logged via `resources/lib/upload_eligibility.py` - nothing uploads yet.
* **API ground truth**: every REST call must exist in the official OpenAPI spec (see
  CLAUDE.md critical constraints). `rate_subtitle` and the upload flow are PROPOSED and
  documented as such in their docstrings.

### B. Kodi UI Font & Glyph Compatibility (`docs/kodi_ui_font_compatibility.md`)
* **Supported & Verified in Kodi Skins**:
  * Formatting: `[COLOR green]`, `[COLOR cyan]`, `[COLOR orange]`, `[COLOR yellow]`, `[COLOR gold]`, `[COLOR red]`, Hex ARGB, `[B]` Bold, `[I]` Italic.
  * Diacritics: Slovak/Czech (`ľščťžýáíéôäň`), Cyrillic (`Русский перевод`), Western European.
  * BMP Glyphs: Stars (`★`, `☆`), bullets (`•`), pipes (`│`), square root as check (`√`). Real check marks (`✔`, `✓`) are Dingbats = tofu; see the matrix.
* **Unsupported / Avoid**:
  * Emojis (🤖, ⚙️, 🔒, 👂) render as blank spaces / empty boxes in default Kodi TTF fonts (Roboto/Arial).
  * Arabic RTL script lacks bi-directional text shaping in Kodi list items.
  * `[HD]` badge removed (obsolete noise).
* **Native Dialog Icons (Do NOT duplicate in filename text)**:
  * `moviehash_match` $\rightarrow$ Kodi native **SYNC** icon (`sync="true"`). Redundant `(Hash)` text tag removed.
  * `hearing_impaired` $\rightarrow$ Kodi native **Ear/CC** icon (`hearing_imp="true"`). Redundant `[SDH]` text badge removed.

### C. Visual Badge Placement
* All badges are appended strictly at the **END** of the release title (`label2`):
  ```text
  [Release Title] [Trusted] [AI] [Machine] [Forced] (+MatchScore)
  ```

### D. Test Flag Interceptor
* Toggle setting `test_flag_interceptor` in the Development settings tab (Expert-only; stripped from release builds by scripts/release_lib.py).
* When `ON`, any search returns pure mock test subtitles (defined in `_inject_test_flag_subtitles()`) showcasing various glyphs, check marks, crosses, stars, and language characters.

---

## 4. 📂 Key Files

* [`addon.xml`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/addon.xml) - Extension points and addon metadata (v2.0.0).
* [`service_monitor.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/service_monitor.py) - Kodi background service (monitor + player).
* [`resources/lib/subtitle_downloader.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/resources/lib/subtitle_downloader.py) - Search execution, badge formatting at line end, and mock interceptor.
* [`resources/lib/matcher.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/resources/lib/matcher.py) - Match scoring and display badge formatter (`get_match_display_tag`).
* [`resources/lib/osclient/provider.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/resources/lib/osclient/provider.py) - API client methods including `vote_subtitle` and user info.
* [`docs/kodi_ui_font_compatibility.md`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/docs/kodi_ui_font_compatibility.md) - UI font rendering reference.
* [`tests/`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/tests/) - Complete pytest suite (167 tests).

---

## 5. 🎯 Next Roadmap Items
1. `POST /subtitles/rate` server-side deployment (client ships 404-tolerant).
2. Auto-upload phase 2: wire `/subtitles/upload/check` once dry-run verdicts look good.
3. addon.xml translations (~40 languages) still carry old .org-era descriptions - needs human translators.
4. Submit 2.0.0 to official `xbmc/repo-plugins` after soak time in the kodi.opensubtitles.com feed.
5. Optional: capture glyph matrix TRY rows 12-20 results; test Estuary "Arial based" font round.
