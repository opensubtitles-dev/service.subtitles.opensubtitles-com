<div align="center">
  <img src="icon.png" width="128" height="128" alt="OpenSubtitles.com Logo" />
  <h1>OpenSubtitles.com for Kodi</h1>
  <p><strong>Official subtitle add-on for Kodi media center powered by the OpenSubtitles.com REST API.</strong></p>

  <p>
    <a href="https://kodi.tv"><img src="https://img.shields.io/badge/Kodi-19%20%7C%2020%20%7C%2021%20%7C%2022-blue.svg?logo=kodi&logoColor=white" alt="Kodi Versions" /></a>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.x-3776AB.svg?logo=python&logoColor=white" alt="Python 3" /></a>
    <a href="https://github.com/opensubtitles/service.subtitles.opensubtitles-com/releases/latest"><img src="https://img.shields.io/badge/Release-v1.0.15-0284c7.svg" alt="Latest Release" /></a>
    <a href="https://github.com/opensubtitles/service.subtitles.opensubtitles-com/actions"><img src="https://img.github.com/github/actions/workflow/status/opensubtitles/service.subtitles.opensubtitles-com/addon-check.yml?branch=v1.0.15&label=Kodi%20Validation" alt="Validation Status" /></a>
    <a href="LICENSE.txt"><img src="https://img.shields.io/badge/License-GPL--2.0-green.svg" alt="License" /></a>
  </p>

  <p>Search and download subtitles for movies and TV shows from <a href="https://www.opensubtitles.com">OpenSubtitles.com</a>. Access over <strong>8,000,000+ subtitles</strong> across <strong>75+ languages</strong> with daily updates.</p>
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
   https://opensubtitles.github.io/service.subtitles.opensubtitles-com/
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

## 📄 License

This project is licensed under the GNU General Public License v2.0 — see the [LICENSE.txt](LICENSE.txt) file for details.
OpenSubtitles REST API client originally based on [python-opensubtitles-rest-api](https://github.com/tomburke25/python-opensubtitles-rest-api) by tomburke25.