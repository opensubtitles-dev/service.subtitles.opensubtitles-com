# OpenSubtitles.com Kodi Add-on - Development Handover

This file provides a complete technical handover for Claude / next AI agent taking over the codebase.

---

## 1. 📍 Repository & Branch Overview

* **Repository Directory**: `/data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com`
* **Upstream**: `opensubtitles-dev/service.subtitles.opensubtitles-com`
* **Fork Remote**: `fork` (`https://github.com/opensubtitles/service.subtitles.opensubtitles-com.git`)
* **Branch Strategy**:
  * **`v1.0.15`**: **FROZEN**. Pull Request [#42](https://github.com/opensubtitles-dev/service.subtitles.opensubtitles-com/pull/42) submitted upstream. Do not modify.
  * **`develop`**: **ACTIVE**. Current version is bumped to `1.0.16`. All new features (service monitor, badges, interceptor, auto-download, rating) are developed here.

---

## 2. 🧪 Testing & Validation Commands

```bash
# Run complete test suite (71 passing tests)
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
* **Background Account & Quota Refresh**:
  * Runs on startup and periodically to fetch VIP status and remaining quota from `/api/v1/infos/user`.
  * Protected by `_refresh_lock = threading.Lock()` with non-blocking acquire to prevent multiple simultaneous requests on rapid setting changes.
  * Currently in dev mode (refreshes immediately on startup so UI changes can be verified; restore 12h age check before final release).
* **Silent Auto-Download on Video Playback**:
  * In `OpenSubtitlesPlayer.onAVStarted()`, auto-downloads matching subtitles if enabled in settings (`auto_download`).
* **Post-Playback Rating Prompt**:
  * In `OpenSubtitlesPlayer.onPlayBackEnded()` / `onPlayBackStopped()`, prompts user to rate/vote downloaded subtitles via `/api/v1/subtitles/vote`.

### B. Kodi UI Font & Glyph Compatibility (`docs/kodi_ui_font_compatibility.md`)
* **Supported & Verified in Kodi Skins**:
  * Formatting: `[COLOR green]`, `[COLOR cyan]`, `[COLOR orange]`, `[COLOR yellow]`, `[COLOR gold]`, `[COLOR red]`, Hex ARGB, `[B]` Bold, `[I]` Italic.
  * Diacritics: Slovak/Czech (`ľščťžýáíéôäň`), Cyrillic (`Русский перевод`), Western European.
  * BMP Glyphs: Stars (`★`, `☆`), bullets (`•`), pipes (`│`), check marks (`✔`, `✓`).
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
* Toggle setting `test_flag_interceptor` in Debug settings.
* When `ON`, any search returns pure mock test subtitles (defined in `_inject_test_flag_subtitles()`) showcasing various glyphs, check marks, crosses, stars, and language characters.

---

## 4. 📂 Key Files

* [`addon.xml`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/addon.xml) - Extension points and addon metadata (v1.0.16).
* [`service_monitor.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/service_monitor.py) - Kodi background service (monitor + player).
* [`resources/lib/subtitle_downloader.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/resources/lib/subtitle_downloader.py) - Search execution, badge formatting at line end, and mock interceptor.
* [`resources/lib/matcher.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/resources/lib/matcher.py) - Match scoring and display badge formatter (`get_match_display_tag`).
* [`resources/lib/osclient/provider.py`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/resources/lib/osclient/provider.py) - API client methods including `vote_subtitle` and user info.
* [`docs/kodi_ui_font_compatibility.md`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/docs/kodi_ui_font_compatibility.md) - UI font rendering reference.
* [`tests/`](file:///data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com/tests/) - Complete pytest suite (71 tests).

---

## 5. 🎯 Next Roadmap Items
1. Finalize desired check mark (`✔` vs `✓` vs `[Trusted]`) based on user UI testing.
2. Smart audio stream detection and language awareness during playback in `service_monitor.py`.
3. Re-enable the 12-hour age check for account status background refresh before production release.
