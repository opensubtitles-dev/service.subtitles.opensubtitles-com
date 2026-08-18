# Changelog

All notable changes to the **OpenSubtitles.com Kodi Add-on** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.15] - 2026-08-18

### Added
- **Smart Release & Subtitle Matcher**: Added multi-factor precision ranking engine comparing video filename and Guessit metadata against subtitle releases:
  - Exact moviehash match (+10,000 pts)
  - Release Group matching (FLUX, Framestor, SPARKS, NTb, etc. +1,500 pts)
  - Quality & Source alignment (BluRay vs WEB-DL vs CAM penalties)
  - Edition matching (Extended / Director's Cut vs Theatrical cut timing shift prevention)
  - Automated `sync="true"` property highlighting in Kodi for high-confidence matches.
- **Smart Account Status**: Split account verification details into 3 dedicated display lines in Settings:
  - Account Status (`OK (VIP)` / `OK (Free User)` / `Error 401`)
  - Quota & Details (Remaining daily downloads quota and VIP badge)
  - Last Checked (Timestamp with 24-hour verification expiration policy)
- **Guessit Filename Analysis**: Added `/api/v1/utilities/guessit` integration with 30-day client-side caching to accurately parse raw video filenames.
- **Search Cache Statistics**: Added live cache metrics counter (`cache_stats`) and configurable cache duration (default 180 min, up to 24h).
- **Official OpenSubtitles Repository**: Added automated build and deployment of `repository.opensubtitles-com` to GitHub Pages for instant add-on updates.
- **Test Suite**: Added 45 pytest tests covering units, caching, XML schema, settings behavior, smart matcher, and live REST API endpoints.

### Changed
- **Settings UI**: Switched informational status rows to pure read-only edit controls with permanent disabled dependencies, preventing accidental keyboard popups.
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
