# OpenSubtitles.com Kodi Add-on — Project TODO & Roadmap

---

## 🚀 Future Roadmap & Planned Enhancements

### 1. ⚡ Silent Auto-Download & Auto-Search on Playback (`xbmc.service`)
* **Description**: Optional background service running via Kodi's `xbmc.service` extension point that detects when video playback begins and automatically searches for subtitles.
* **Key Behaviors**:
  * If enabled, automatically downloads and applies the #1 ranked subtitle without requiring user interaction.
  * Can be toggled on/off in Add-on Settings (`Auto-Search on Playback`, `Silent Auto-Download`).
  * Displays a clean on-screen toast when loaded (e.g., *"OpenSubtitles.com: Auto-loaded English BluRay-FLUX"*).

---

### 2. 🧠 Smart Embedded Subtitle Stream Auto-Detection
* **Description**: Before triggering API searches or downloads, check if the playing video file already contains embedded subtitle streams (`Player().getAvailableSubtitleStreams()`) matching the user's preferred language.
* **Benefit**: If embedded subtitles already exist in the container (MKV/MP4), automatically select that stream (`Player().setSubtitleStream()`) and skip making external API requests, saving API quota and network bandwidth.

---

### 3. ⭐ Post-Playback Subtitle Rating & Voting Dialog
* **Description**: Prompt users optionally when playback ends (or via player context menu) to rate subtitle synchronization and translation quality (1–10 / Good / Bad).
* **Benefit**: Submits ratings directly back to OpenSubtitles.com API (`/api/v1/subtitles/vote`), crowdsourcing accurate release synchronization data from Kodi users.

---

### 4. 🔀 Subtitle Format Auto-Converter (ASS / SSA ➔ Clean SRT)
* **Description**: If a downloaded subtitle is in `.ass` / `.ssa` format with incompatible styling, positioning overrides, or bloated font attachments, automatically strip formatting tags into standard clean UTF-8 `.srt` text for optimal TV skin rendering.

---

### 5. 🎯 SDH & Forced Subtitle Preference Modes
* **Description**: Add user preferences in Settings to prioritize or deprioritize specific subtitle types:
  * **Prefer SDH**: Prioritize Subtitles for Deaf & Hard of Hearing / Hearing Impaired.
  * **Prefer Forced**: Prioritize foreign-speech-only / forced subtitle tracks.

---

## ✅ Completed Enhancements (v1.0.15)

* [x] **Smart Release & Subtitle Matcher Engine**: Multi-factor precision ranking engine comparing video filenames and Guessit metadata against subtitle releases (exact hash, release group, source/cut alignment, resolution, codec).
* [x] **Multi-Language Top-Picks & Grouped Ranking**: Displays #1 best match for 1st preferred language, #1 best match for 2nd language, followed by remaining results grouped by language from best to worst.
* [x] **On-Screen Yellow Match Badges**: Displays match ratings (e.g. `[COLOR yellow](+95)[/COLOR]`, `[COLOR yellow](Hash)[/COLOR]`) after subtitle release names in Kodi subtitle dialog.
* [x] **Kodi Built-in Sync Flag Precision**: Strictly reserved `sync="true"` for 100% bit-exact moviehash matches.
* [x] **Guessit Video Filename Analysis**: Added `/api/v1/utilities/guessit` integration with 30-day client-side caching.
* [x] **Search Cache Duration & Live Metrics**: Configurable cache duration (up to 24h) and live stats indicator (`cache_stats`).
* [x] **Smart Account Status & Age Indicator**: 3 dedicated read-only status lines (Status, Quota & Details, Last Checked) with 24-hour verification expiration.
* [x] **Comprehensive HTTP Error Mapping**: Clean user-facing error dialogs for 400, 401, 406, 429, and 5xx server issues.
* [x] **NFC Unicode Normalization**: Eliminates macOS decomposed diacritic search failures.
* [x] **Optimized ID Search Strategy**: Clean separation of parent show IDs vs episode-specific IDs, resolving search failures on Seren/TMDB Helper (Issues #39, #40).
* [x] **Official OpenSubtitles Kodi Repository Portal**: Automated build and deployment of `repository.opensubtitles-com` to GitHub Pages.
* [x] **Automated CI & Pytest Suite**: 47 unit & API tests running on GitHub Actions across Kodi matrix, nexus, omega, piers.
