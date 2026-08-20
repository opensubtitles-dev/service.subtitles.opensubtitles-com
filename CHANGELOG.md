# Changelog

All notable changes to the **OpenSubtitles.com Kodi Add-on** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.16] - 2026-08-20

### Fixed
- **Settings scripts failing with `ModuleNotFoundError`**: Kodi runs `RunScript()` targets "without an addon", putting every installed add-on's library directory on `sys.path` ahead of ours — so another add-on's top-level `resources` package shadows ours and **Test Connection** dies with `No module named 'resources.lib.osclient'`. The import-path guard added in v1.0.11 was lost when `test_connection.py` was rewritten for v1.0.15. Restored, and extended to `clear_cache.py` and `check_updates.py` (issue #39, ticket #168978).
- **TV episode searches against a mis-scraped library**: Kodi's `imdbnumber` field holds whatever the scraper treats as the item's primary id, which for a TVDB-scraped show is *not* an IMDb id. It was sent as `parent_imdb_id` and matched nothing, while the episode's own id was discarded. `imdbnumber` is now only accepted with a `tt` prefix, `uniqueid["imdb"]` is preferred, and the episode id is retained as a fallback attempt.
- **One malformed API entry could hide every subtitle**: an unexpected field type raised out of `list_subtitles()`, losing all results *and* skipping `endOfDirectory()` — leaving Kodi's subtitle dialog open and empty. Ranking and rendering are now guarded per entry, and `sanitize_filename()` coerces non-string input.
- **`check_updates.py` missing from release zips**, leaving the settings "Check for updates" button inert.

### Added
- **Regression tests for the above** (`tests/test_runscript_entrypoints.py`, `tests/test_listing_resilience.py`): every `RunScript()` entry point must carry the import guard *above* its first `resources` import and appear in `INCLUDE_ENTRIES`; ranking must never drop a result. The v1.0.15 guard removal passed all 62 existing tests — which is precisely why these exist.

---

## [v1.0.15] - 2026-08-18

### Added
- **Smart Release & Subtitle Matcher Engine**: Multi-factor precision ranking engine comparing video filename and Guessit metadata against subtitle releases (exact hash, release group, source/cut alignment, resolution, codec).
- **Multi-Language Top-Picks & Grouped Ranking**: Displays #1 best match for 1st preferred language, #1 best match for 2nd language, followed by remaining results grouped by language.
- **Adaptive Language Memory**: Dynamically remembers the last downloaded subtitle language and automatically prioritizes it as #1 on subsequent searches.
- **Kodi Hearing Impaired (SDH) System Reflection**: Automatically reflects Kodi's native accessibility setting (`subtitles.hearingimpaired`) and boosts matching SDH subtitles (+350 pts).
- **Language Grouping (Smart Matching Off)**: When smart release matching is turned off, cleanly groups all results by language in user-preferred order and sorts by community popularity.
- **Gzip Cache Compression**: Integrates Gzip + Base64 compression on all cached API responses, reducing cache memory footprint by 70%–85%.
- **Selectable Version & Check for Updates**: Clickable version row in Settings to check against GitHub and official repository manifests for new releases.
- **Smart Account Status**: Split account verification details into 3 dedicated display lines in Settings (Status, Quota & Details, Last Checked) with 24-hour verification expiration.
- **Guessit Filename Analysis**: Added `/api/v1/utilities/guessit` integration with 30-day client-side caching to accurately parse raw video filenames.
- **Search Cache Statistics**: Added live cache metrics counter (`cache_stats`) and configurable cache duration (default 180 min, up to 24h).
- **Official OpenSubtitles Repository**: Added automated build and deployment of `repository.opensubtitles-com` to GitHub Pages for instant add-on updates.
- **Automated CI & Pytest Suite**: 62 unit, integration, and TV search tests running on GitHub Actions.

### Changed
- **Settings UI**: Decluttered and consolidated settings into a clean, modern interface.
- **Cache Clearing**: Extended `clear_cache.py` to purge all cache namespaces (`os_com`, `OpenSubtitles`, `os_library`) in memory and disk.

### Fixed
- Fixed Unicode normalization (NFC) for search queries with international diacritics.
- Optimized search parameters to omit redundant `query` and `year` filters when a specific IMDb or TMDb ID is provided.
- Fixed `CSetting` XML parsing warning by aligning control types with Kodi v1 schema.

---

## [v1.0.14] - 2026-08-14

### Security
- **Credential Privacy**: Stopped logging passwords, session tokens, and API keys to the Kodi debug log.

### Fixed
- **Session Auto-Refresh**: Expired login sessions now refresh automatically instead of failing downloads.
- **Rating Handling**: Fixed subtitle list generation failing when a subtitle has no rating.
- **Download Integrity**: Failed downloads no longer pass empty file paths to Kodi.
- **Timeout Protection**: Added timeout to filename analysis to prevent playback hangs.
- **Version Reporting**: User-Agent now reports dynamic add-on version.

---

## [v1.0.13] - 2026-08-10

### Fixed
- Fixed TV episode searches for video add-ons that pass show IDs instead of episode IDs by querying `/features`.

---

## [v1.0.12] - 2026-08-07

### Added
- Test Connection now automatically saves settings before executing the verification test.

---

## [v1.0.11] - 2026-08-06

### Fixed
- Fixed import conflicts when third-party add-ons ship a top-level `resources` package.
- Fixed connection and timeout errors crashing with `AttributeError`.

---

## [v1.0.10] - 2026-07-01

### Fixed
- Fixed `ModuleNotFoundError: No module named 'resources.lib.os'` by renaming internal package to `osclient`.
- Fixed TV show search in non-English libraries by querying original show titles.

---

## [v1.0.9] - 2026-03-01

### Added
- Added Test Connection button in Settings.
- Added search results caching with configurable duration.

---

## [v1.0.8] - 2025-10-07
- Queries Kodi library if IMDb or TMDb ID is missing.

## [v1.0.7] - 2025-08-26
- Added IMDb and TMDb ID collection for accurate API queries.

## [v1.0.6] - 2024-11-29
- Fixed handling of RAR archives and Chinese (`zh-cn`) language mappings.

## [v1.0.5] - 2024-07-30
- Fixed Portuguese filenames and added AI-translated subtitle filter.

## [v1.0.4] - 2024-01-17
- Sanitized language queries, improved moviehash usage and sorting.

## [v1.0.3] - 2023-12-18
- Fixed subdirectory folder paths.

## [v1.0.2] - 2023-08-28
- Updated User-Agent header.

## [v1.0.1] - 2023-07-28
- Removed 10-item limit for returned subtitles and fixed Portuguese/Brazilian flags.

## [v1.0.0] - 2023-07-01
- Initial release of OpenSubtitles.com Kodi add-on based on REST API v1.
