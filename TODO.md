# OpenSubtitles.com Kodi Add-on — Project TODO & Roadmap

---

## 🚀 Future Roadmap & Planned Enhancements

### 1. Smart Release Token Sorter & Multi-Factor Matching
* **Description**: Implement an intelligent subtitle release ranking algorithm that analyzes both the playing video filename and subtitle release titles to rank the most compatible releases at the top of Kodi's search results.
* **Semantic Token Groups to Match**:
  * **Source**: `BluRay`, `BD`, `BDRip`, `BRRip`, `Remux`, `WEB-DL`, `WEBRip`, `HDTV`, `DVDRip`
  * **Quality**: `2160p (4K)`, `1080p`, `720p`, `480p`
  * **Streaming Service**: `Netflix (NF)`, `Amazon Prime (AMZN)`, `Disney+ (DSNP)`, `HBO Max (HMAX)`, `Apple TV+ (ATVP)`, `Peacock (PCOK)`, `Hulu`
  * **Codec**: `x264`, `h264`, `AVC`, `x265`, `h265`, `HEVC`, `AV1`
  * **Audio**: `Atmos`, `DTS-HD`, `DTS`, `TrueHD`, `DDP5.1`, `DD5.1`, `AAC`
  * **Release Groups**: `YTS`, `YIFY`, `RARBG`, `SPARKS`, `FLUX`, `NTb`, `GGEZ`, `CMRG`, etc.
* **Sorting Hierarchy**:
  1. Preferred audio/subtitle language match
  2. Selected language order
  3. Exact filehash sync (`sync == 'true'`)
  4. Token overlap score (video source & quality similarity bonus)
  5. User rating score
  6. Hearing impaired flags

---

### 2. OpenSubtitles `/api/v1/utilities/guessit` Filename Parser Fallback
* **Description**: Integrate the official OpenSubtitles.com `/api/v1/utilities/guessit` API endpoint as an intelligent fallback parser for unindexed or non-library video files.
* **Capabilities**:
  * Clean extraction of `title`, `year`, `season`, `episode`, `screen_size`, `source`, `video_codec`, `audio_codec`, and `release_group` from raw filenames.
  * Server-side execution without requiring heavy local Python regex packages or C-extensions.

---

### 3. Rich Color-Coded Search Result Formatting
* **Description**: Enhance search result list items (`xbmcgui.ListItem`) in `DialogSubtitles.xml` using Kodi's color formatting tags `[COLOR <color>]...[/COLOR]`.
* **Visual Elements**:
  * `[COLOR green][SYNC][/COLOR]` for exact moviehash matches.
  * `[COLOR yellow]★ 4.5[/COLOR]` for rating scores.
  * `[COLOR lightblue]OpenSubtitles.com[/COLOR]` or release group tags.
  * `[COLOR orange][CC][/COLOR]` for Hearing Impaired / SDH subtitles.

---

### 4. Auto-Search & Silent Auto-Download Service (`xbmc.service`)
* **Description**: Optional background service running via Kodi's `xbmc.service` extension point that detects when video playback begins and automatically searches for subtitles.
* **Key Behaviors**:
  * If enabled, automatically downloads and applies the #1 ranked subtitle without requiring user interaction.
  * Can be toggled on/off in Add-on Settings (`Auto-Search on Playback`, `Silent Auto-Download`).

---

### 5. Smart Embedded Subtitle Stream Auto-Selection
* **Description**: Before triggering API searches or downloads, check if the playing video file already contains embedded subtitle streams (`Player().getAvailableSubtitleStreams()`) matching the user's preferred language.
* **Benefit**: If embedded subtitles already exist in the file, automatically select that stream (`Player().setSubtitleStream()`) and skip making external API requests, saving API quota and network bandwidth.

---

### 6. SDH & Forced Subtitle Preference Modes
* **Description**: Add user preferences in Settings to prioritize or deprioritize specific subtitle types:
  * **Prefer SDH**: Prioritize Subtitles for Deaf & Hard of Hearing / Hearing Impaired.
  * **Prefer Forced**: Prioritize foreign-speech-only / forced subtitle tracks.

---

## ✅ Completed Enhancements (v1.0.15)
* [x] **Smart Account Status & Age Indicator**: Real-time quota and verification timestamp in Settings under Login Details.
* [x] **24-Hour Expiration Policy**: Auto-expires stale status (> 24h) and prompts for re-verification.
* [x] **Comprehensive HTTP Error Mapping**: Clean user-facing error dialogs for 400, 401, 406, 429, and 5xx server issues.
* [x] **NFC Unicode Normalization**: Eliminates macOS decomposed diacritic search failures.
* [x] **Clean ID Search Strategy**: Omits redundant `query` and `year` parameters when unique `imdb_id` / `tmdb_id` is known.
* [x] **Informative Real-Time Search Toasts**: Shows exact search criteria (IMDb ID, S/E, languages) on search launch.
* [x] **Clean Temp Management & Garbage Collection**: Automated stale file cleaner and atomic file downloads.
