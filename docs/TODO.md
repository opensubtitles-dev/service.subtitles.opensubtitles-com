# OpenSubtitles.com Kodi Add-on — Project TODO & Roadmap

---

## ✅ Shipped in 2.0 (was roadmap)

* **Silent auto-download on playback** - background service downloads the top pick per preferred language, stores beside the video with Kodi naming, notifies honestly. (former item 1)
* **Post-playback rating dialog** - 5-star select + sync yes/no, sent to the PROPOSED /subtitles/rate endpoint. (former item 4)
* **AI transcription pipeline** - expert toggle, capability probe, 6-rung no-install audio extraction ladder verified on Android/Windows/Linux/macOS/LibreELEC (docs/audio_support_matrix.md).
* **Subtitle-sync plumbing** - [SYNC] dialog row + delay-nudge offer behind subtitle_sync_enabled; engine arrives from project subsync (docs/subtitle_sync_plan.md).

## 🚀 Future Roadmap & Planned Enhancements

### 1. (shipped - see above)
* **Description**: Optional background service running via Kodi's `xbmc.service` extension point that detects when video playback begins and automatically searches for subtitles.
* **Key Behaviors**:
  * If enabled, automatically downloads and applies the #1 ranked subtitle without requiring user interaction.
  * Can be toggled on/off in Add-on Settings (`Auto-Search on Playback`, `Silent Auto-Download`).
  * Displays a clean on-screen toast when loaded (e.g., *"OpenSubtitles.com: Auto-loaded English BluRay-FLUX"*).

---

### 2. 🎧 Smart Audio Stream Sync & Language Awareness
* **Description**: Automatically inspect active audio stream language (e.g., Japanese, Spanish, German) during playback:
  * Non-native or foreign audio $\rightarrow$ Automatically prioritize full translation subtitles in user's native language.
  * Native audio $\rightarrow$ Automatically prioritize Forced / Foreign-parts subtitles.

---

### 3. 🧠 Smart Embedded Subtitle Stream Auto-Detection
* **Description**: Before triggering API searches or downloads, check if the playing video file already contains embedded subtitle streams (`Player().getAvailableSubtitleStreams()`) matching the user's preferred language.
* **Benefit**: If embedded subtitles already exist in the container (MKV/MP4), automatically select that stream (`Player().setSubtitleStream()`) and skip making external API requests, saving API quota and network bandwidth.

---

### 4. ⭐ Post-Playback Subtitle Rating & Voting Dialog
* **Description**: Prompt users optionally when playback ends (or via player context menu) to rate subtitle synchronization and translation quality (1–10 / Good / Bad).
* **Benefit**: Submits ratings directly back to OpenSubtitles.com API (`/api/v1/subtitles/vote`), crowdsourcing accurate release synchronization data from Kodi users.

---

### 5. 🔀 Subtitle Format Auto-Converter (ASS / SSA ➔ Clean SRT)
* **Description**: If a downloaded subtitle is in `.ass` / `.ssa` format with incompatible styling, positioning overrides, or bloated font attachments, automatically strip formatting tags into standard clean UTF-8 `.srt` text for optimal TV skin rendering.

---

### 6. ⌨️ Manual Search Enhancements
* **Description**: Extend manual keyboard search dialog to parse custom season/episode tokens directly from user input strings when searching for obscure TV episodes.

---

## ✅ Completed Enhancements (v1.0.15)

* [x] **Smart Release & Subtitle Matcher Engine**: Multi-factor precision ranking engine comparing video filenames and Guessit metadata against subtitle releases (exact hash, release group, source/cut alignment, resolution, codec).
* [x] **Multi-Language Top-Picks & Grouped Ranking**: Displays #1 best match for 1st preferred language, #1 best match for 2nd language, followed by remaining results grouped by language from best to worst.
* [x] **Adaptive Language Memory**: Dynamically remembers the last downloaded subtitle language per video/session and automatically prioritizes it as #1 on subsequent searches.
* [x] **Kodi Hearing Impaired (SDH) System Reflection**: Automatically reflects Kodi's native accessibility setting (`subtitles.hearingimpaired`) and boosts matching SDH subtitles (+350 pts).
* [x] **Language Grouping when Smart Matching is OFF**: When smart release matching is disabled, cleanly groups all results by language in user-preferred order and sorts by community popularity.
* [x] **Gzip Cache Compression**: Integrates Gzip + Base64 compression on all cached API responses, reducing cache memory footprint by 70%–85%.
* [x] **Interactive Version Check & Update Action**: Unified selectable version row in settings allowing one-click check against GitHub/repository manifests.
* [x] **Decluttered Settings Interface**: Consolidated master toggles and removed bloated nested menus.
* [x] **On-Screen Yellow Match Badges**: Displays match ratings (e.g. `[COLOR yellow](+95)[/COLOR]`, `[COLOR yellow](Hash)[/COLOR]`) after subtitle release names in Kodi subtitle dialog.
* [x] **Kodi Built-in Sync Flag Precision**: Strictly reserved `sync="true"` for 100% bit-exact moviehash matches.
* [x] **Guessit Video Filename Analysis**: Added `/api/v1/utilities/guessit` integration with 30-day client-side caching.
* [x] **Search Cache Duration & Live Metrics**: Configurable cache duration (up to 24h) and live stats indicator (`cache_stats`).
* [x] **Smart Account Status & Age Indicator**: 3 dedicated read-only status lines (Status, Quota & Details, Last Checked) with 24-hour verification expiration.
* [x] **Comprehensive HTTP Error Mapping**: Clean user-facing error dialogs for 400, 401, 406, 429, and 5xx server issues.
* [x] **NFC Unicode Normalization**: Eliminates macOS decomposed diacritic search failures.
* [x] **Optimized ID Search Strategy**: Clean separation of parent show IDs vs episode-specific IDs, resolving search failures on Seren/TMDB Helper (Issues #39, #40).
* [x] **Official OpenSubtitles Kodi Repository Portal**: Automated build and deployment of `repository.opensubtitles-com` to GitHub Pages.
* [x] **Automated CI & Pytest Suite**: 62 unit, integration, and TV search tests running on GitHub Actions.
