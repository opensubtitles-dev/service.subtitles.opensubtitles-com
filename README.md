OpenSubtitles.com KODI add-on
=============================
Search and download subtitles for movies and TV-Series from OpenSubtitles.com. Search in 75 languages, 8.000.000+ subtitles, daily updates.

REST API implementation based on tomburke25 [python-opensubtitles-rest-api](https://github.com/tomburke25/python-opensubtitles-rest-api)

### Documentation
* [Developer Workflow & Fast Testing Guide](DEV_WORKFLOW.md)
* [Kodi Standards & Repo Submission Rules](KODI_STANDARDS.md)
* [AI Agent Architecture & Guidelines](AGENT_INSTRUCTIONS.md)
* [Project Roadmap & Feature TODO](TODO.md)

---

## 📥 Installation & Updates

You can install the **OpenSubtitles.com** add-on through the **Official OpenSubtitles Repository** (for instant updates) or via the built-in Kodi repository.

### Option A: Install via OpenSubtitles Repository (Recommended for Fast Updates)

Installing via our repository ensures you receive automatic updates, hotfixes, and new features immediately without waiting for official mirror review cycles.

#### Step 1: Enable Unknown Sources in Kodi
1. In Kodi, open **Settings (⚙️) ➔ System ➔ Add-ons**.
2. Toggle **Unknown sources** to **ON** (enabled).
3. Confirm the security prompt by clicking **Yes**.

#### Step 2: Install the Repository
1. Download **[`repository.opensubtitles-com.zip`](https://github.com/opensubtitles/service.subtitles.opensubtitles-com/releases/latest/download/repository.opensubtitles-com.zip)** to your device.
2. In Kodi, go to **Add-ons ➔ Add-on browser** (open package icon in top left).
3. Select **Install from zip file** and choose the downloaded `repository.opensubtitles-com.zip`.
4. Wait for the notification: *"OpenSubtitles.com Official Repository Add-on installed"*.

#### Step 3: Install & Configure the Subtitles Add-on
1. Select **Install from repository ➔ OpenSubtitles.com Official Repository ➔ Subtitles ➔ OpenSubtitles.com**.
2. Click **Install**.
3. Open add-on **Settings**:
   * Enter your OpenSubtitles.com **Username** and **Password**.
   * Click **Test Connection** to verify your VIP status and daily download quota.
4. In Kodi **Settings ➔ Player ➔ Language ➔ Subtitle Services**, set both *Default movie service* and *Default TV show service* to **OpenSubtitles.com**.

---

### Option B: Install via Official Kodi Repository
1. In Kodi, navigate to **Add-ons ➔ Add-on browser ➔ Install from repository**.
2. Select **Kodi Add-on repository ➔ Subtitles ➔ OpenSubtitles.com**.
3. Click **Install** and configure your login credentials in Settings.

---

## 📜 Changelog

v1.0.15 (2026-08-18)
- added Smart Account Status display in Settings with 24-hour verification expiration policy
- improved Test Connection dialog with comprehensive HTTP error handling (400, 401, 406, 429, 5xx)
- fixed Unicode normalization (NFC) for search queries with diacritics and international titles
- optimized ID search strategy: omits redundant query and year filters when unique IMDb/TMDb ID exists
- added informative on-screen search toast displaying active search criteria and languages
- implemented safe temp directory garbage collection and atomic subtitle download writes
- added clear cache utility for clearing memory properties and orphaned subtitle files
- added comprehensive pytest test suite (unit + live API tests) and GitHub Actions CI workflow

v1.0.14 (2026-08-14)
- security: stopped writing credentials, session tokens and API keys to the Kodi debug log
- expired login sessions now refresh automatically instead of failing the download with "login failed"
- fixed subtitle list failing to build when a subtitle has no rating
- failed downloads no longer hand Kodi a subtitle file that does not exist
- added a timeout to the filename-analysis request so playback can no longer hang on it

v1.0.13 (2026-08-10)
- TV episode searches now ask OpenSubtitles.com what the id supplied by the video add-on actually refers to, instead of assuming. One cached /features lookup says whether it is a show or an episode, and for an episode it also returns the show's id and the real season/episode numbers, so the search is built correctly whatever the add-on reported
- fixed TV episode searches for video add-ons that report the show's IMDb/TMDb id rather than the episode's (Umbrella, POV), which 1.0.11 broke by always treating the player's id as an episode id. Add-ons disagree about what they put in that field and nothing local tells the two apart, so the add-on no longer guesses: it tries the show reading first (id + season/episode), then the episode reading (id on its own), and only falls back to a title search if neither matches. That also stops the title fallback from surfacing subtitles for a different show with a similar name (thanks peno64)

v1.0.12 (2026-08-07)
- Test Connection now works with the credentials as typed: Kodi saves and closes the settings dialog before running the test, so you no longer have to press OK and reopen settings first. The settings reopen once you dismiss the result (thanks rosensama)

v1.0.11 (2026-08-06)
- fixed Test Connection failing with "ModuleNotFoundError: No module named 'resources.lib.osclient'" when another installed add-on ships its own top-level 'resources' package: the settings script now puts its own directory first on the import path (the v1.0.10 rename did not address this)
- fixed TV episode searches returning nothing when only the episode's own IMDb/TMDb id is known: the id is now sent on its own instead of alongside query/season/episode, with an automatic title fallback if it finds nothing (thanks peno64)
- fixed connection and timeout errors crashing with AttributeError instead of reporting the service as unavailable, during login, search and download

v1.0.10 (2026-07-01)
- fixed "ModuleNotFoundError: No module named 'resources.lib.os'" on some devices (notably Android): added package __init__.py files so imports no longer rely on implicit namespace packages, and renamed the internal 'os' package to 'osclient' to stop it shadowing Python's standard-library os module
- fixed subtitle search for TV shows in non-English (localized) libraries by querying the show's original title from the Kodi library instead of the translated on-screen title (thanks notoco)

v1.0.9 (2026-03-01)
- added Test Connection button in settings to verify credentials and view account info
- show specific error message when search or download fails
- added search results caching with configurable duration
- fixed trailing slash on subdirectory folder path

v1.0.8 (2025-10-07)
- performs a query to kodi library if imdb or tmdb ID is missing

v1.0.7 (2025-08-26)
- added IMDB and TMDB collection on files for more accurate search to the API

v1.0.6 (2024-11-29)
- fixed issue with RAR archives 
- handles default chinese language to zh-cn 

v1.0.5 (2024-07-30)
- fixed issue with portuguese file names
- added AI translated filter 

v1.0.4 (2024-01-15)
- Sanitize language query
- Improved sorting
- Improved error messages 
- Improved usage of moviehash 

v1.0.3 (2023-12-18)
- Fixed issue with file path

v1.0.2 (2023-08-28)
- Update user agent header

v1.0.1 (2023-07-28)
- Remove limit of 10 subtitles for the returned values
- Fix Portuguese and Brazilian flags

1.0.0
 Initial version, forked from https://github.com/juokelis/service.subtitles.opensubtitles
 Search fixed and improved