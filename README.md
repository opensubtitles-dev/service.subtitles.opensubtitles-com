<div align="center">
  <img src="icon.png" width="128" height="128" alt="OpenSubtitles.com Logo" />
  <h1>OpenSubtitles.com for Kodi</h1>
  <p><strong>Official subtitle add-on for Kodi media center powered by the OpenSubtitles.com REST API.</strong></p>

  <p>
    <a href="https://kodi.tv"><img src="https://img.shields.io/badge/Kodi-19%20%7C%2020%20%7C%2021%20%7C%2022-blue.svg?logo=kodi&logoColor=white" alt="Kodi Versions" /></a>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.x-3776AB.svg?logo=python&logoColor=white" alt="Python 3" /></a>
    <a href="https://github.com/opensubtitles/service.subtitles.opensubtitles-com/releases/latest"><img src="https://img.shields.io/badge/Release-v1.0.16-0284c7.svg" alt="Latest Release" /></a>
    <a href="https://github.com/opensubtitles-dev/service.subtitles.opensubtitles-com/actions/workflows/addon-check.yml"><img src="https://img.shields.io/github/actions/workflow/status/opensubtitles-dev/service.subtitles.opensubtitles-com/addon-check.yml?branch=master&label=Kodi%20Validation" alt="Validation Status" /></a>
    <a href="LICENSE.txt"><img src="https://img.shields.io/badge/License-GPL--2.0-green.svg" alt="License" /></a>
  </p>

  <p>Search and download subtitles for movies and TV shows from <a href="https://www.opensubtitles.com">OpenSubtitles.com</a>. Access over <strong>10,000,000+ subtitles</strong> across <strong>100+ languages</strong> with daily updates.</p>
</div>

---

## ✨ Features

- 🔍 **Smart Multi-Identifier Search**: Automatically searches via IMDb ID, TMDb ID, or TV show/episode metadata.
- ⚡ **Guessit Filename Analysis**: Integrates `/api/v1/utilities/guessit` with 30-day client-side caching for precise release matching.
- 👑 **VIP & Quota Management**: Built-in **Test Connection** with live VIP badge, remaining daily downloads quota counter, and 24-hour verification.
- ⏱️ **Fast Search Caching**: Configurable search cache duration (default 180 minutes) to eliminate duplicate network calls and speed up browsing.
- 🛡️ **Advanced Filters**: Customizable settings to include/exclude Hearing Impaired (HI), Foreign Parts Only, Machine Translated, and AI Translated subtitles.
- 🔒 **Security & Privacy**: Zero logging of user credentials, session tokens, or API keys in the Kodi debug log.
- 🌐 **Full UTF-8 Diacritics Support**: Unicode normalization (NFC) ensures international film and TV show titles match seamlessly.

---

## 📥 Installation

### Option A: Install via OpenSubtitles Repository (Recommended for Fast Updates)

> [!TIP]
> Installing via our official repository ensures you automatically receive instant updates, new features, and bug fixes without waiting for upstream Kodi mirror approval cycles.

1. In Kodi, enable **Unknown sources** under **Settings (⚙️) ➔ System ➔ Add-ons**.
2. Go to **Settings (⚙️) ➔ File manager**.
3. Click **Add source**.
4. Set the path to:
   ```
   https://kodi.opensubtitles.com
   ```
5. Name the source **`OpenSubtitles-repo`** and click **OK**.
6. Navigate to **Add-ons** (box icon at top left).
7. Select **Install from zip file ➔ OpenSubtitles-repo**.
8. Select **`repository.opensubtitles-com.zip`** and wait for the installation notification.
9. Go to **Install from repository ➔ OpenSubtitles.com Official Repository ➔ Subtitles ➔ OpenSubtitles.com**.
10. Click **Install**.

---

### Option B: Install via Official Kodi Repository

1. In Kodi, go to **Add-ons ➔ Install from repository**.
2. Select **Kodi Add-on repository ➔ Subtitles ➔ OpenSubtitles.com**.
3. Click **Install**.

---

## ⚙️ Configuration & Setup

1. Open add-on **Settings (Login Details)**:
   * Enter your OpenSubtitles.com **Username** and **Password** (or API Key if applicable).
   * Click **Test Connection** to verify your account credentials, VIP status, and daily download quota.
2. In Kodi, navigate to **Settings ➔ Player ➔ Language ➔ Subtitle Services**:
   * Set **Default movie service** to **OpenSubtitles.com**.
   * Set **Default TV show service** to **OpenSubtitles.com**.

---

## 📚 Developer & Contributor Documentation

- 🛠️ [Developer Workflow & Fast Testing Guide](DEV_WORKFLOW.md)
- 📋 [Kodi Standards & Repo Submission Rules](KODI_STANDARDS.md)
- 🤖 [AI Agent Architecture & Guidelines](AGENT_INSTRUCTIONS.md)
- 🗺️ [Project Roadmap & Feature Backlog](TODO.md)
- 📜 [Full Release Changelog](CHANGELOG.md)

---

## 🆕 What's New

### v1.0.16 — reliability fixes

- **Settings buttons work alongside other add-ons again.** Kodi runs the settings scripts "without an add-on", which lets another add-on's `resources` folder shadow ours — **Test Connection** then failed with `ModuleNotFoundError`. The guard that prevents this was lost during the v1.0.15 rewrite; it is restored and now also covers **Clear Cache** and **Check for Updates** (issue #39).
- **TV episodes are found even when the library's id is wrong.** Kodi's `imdbnumber` field holds whatever the scraper used as the primary id — for a TVDB-scraped show that is *not* an IMDb id, and searching with it returned nothing. The add-on now only trusts an explicit `tt` id, and keeps the episode's own id as a second attempt.
- **One odd result no longer hides all the others.** An unexpected field in the API response used to empty the whole subtitle list and leave the dialog hanging.
- **Check for Updates** is now actually included in release zips.

### v1.0.15 — matching, ranking and account visibility

- **Smart release matching.** Subtitles are scored against your video's filename — exact file hash first, then release group, source/cut, resolution and codec — and the best match is listed first, with a yellow badge showing the score. Purely reordering: nothing is filtered out or hidden.
- **Multi-language top picks.** The best match for each of your preferred languages is promoted to the top, then the rest follow grouped by language in your preferred order.
- **Language memory.** The language you last downloaded is promoted to first place on later searches. Note this lasts for the current Kodi session only, and it only reorders languages you already have configured — it never adds or removes any.
- **Hearing-impaired sync.** If Kodi's own accessibility setting asks for SDH subtitles, matching ones are boosted. Your explicit add-on setting still wins: set it to `exclude` and SDH is not preferred regardless.
- **Faster repeat searches.** Cached API responses are gzip-compressed, and the cache duration is configurable (now 180 minutes by default, up to 24 hours). Settings show live cache statistics and a **Clear Cache** button.
- **Account status at a glance.** Settings display your account status, remaining quota and when it was last checked, refreshed by **Test Connection** and re-verified every 24 hours.
- **Check for updates.** The version row in Settings is clickable and compares against the published manifests. It only tells you an update exists and asks Kodi to refresh its repositories — it never downloads or runs code itself.
- **Better filename parsing** via the OpenSubtitles `guessit` service, cached for 30 days.
- **Automated tests and CI**, plus an official add-on repository published to GitHub Pages for faster updates than the Kodi mirror.

See the [full changelog](CHANGELOG.md) for the complete history.

---

## 📄 License

This project is licensed under the GNU General Public License v2.0 — see the [LICENSE.txt](LICENSE.txt) file for details.
OpenSubtitles REST API client originally based on [python-opensubtitles-rest-api](https://github.com/tomburke25/python-opensubtitles-rest-api) by tomburke25.