# ⚡ Rapid Kodi Add-on Development Workflow

This guide details the fastest setup for developing, testing, and debugging `service.subtitles.opensubtitles-com` without repetitive re-installations.

---

## 1. Live Symlink Setup (One-Time)

Subtitle add-ons in Kodi run on-demand (`extension point="xbmc.subtitle.module"`). Every subtitle search or download spawns a new Python execution. Symlinking the repository directly into Kodi means **every code edit is instantly active**.

### macOS:
```bash
ln -s "/data/www/opensubtitles.org/public_html/github/service.subtitles.opensubtitles-com" \
      "$HOME/Library/Application Support/Kodi/addons/service.subtitles.opensubtitles-com"
```

### Linux:
```bash
ln -s "/path/to/service.subtitles.opensubtitles-com" "$HOME/.kodi/addons/service.subtitles.opensubtitles-com"
```

### Windows (cmd as Administrator):
```cmd
mklink /D "%APPDATA%\Kodi\addons\service.subtitles.opensubtitles-com" "C:\path\to\service.subtitles.opensubtitles-com"
```

*(Note: If you edit `resources/settings.xml` or `addon.xml`, close and reopen the Kodi settings dialog or restart Kodi).*

---

## 2. Live Log Streaming

Keep a terminal open to monitor live logs and debug output while testing inside Kodi:

```bash
# Run the included helper script:
./scripts/stream_kodi_logs.sh
```

Or manually:
```bash
tail -f "$HOME/Library/Application Support/Kodi/temp/kodi.log" | grep --line-buffered -E "service\.subtitles\.opensubtitles-com|OpenSubtitles"
```

> **Enable Debug Logging in Kodi**: Go to `Settings -> System -> Logging -> Enable debug logging`.

---

## 3. Local Testing & Live Simulation (Outside Kodi)

### Fast Offline Mock Tests (< 0.1s):
```bash
python3 -m pytest
```

### Live Real-World Network Tests & User Simulation:
You can simulate real user interactions (search, metadata feature lookups, and subtitle downloads) against the live OpenSubtitles.com API:

```bash
# 1. Run full live simulation in terminal
python3 scripts/live_test.py --query "The Matrix" --download

# 2. Test authenticated flow - put credentials in the gitignored .env, never
#    on the command line or in echo (both land in shell history and `ps`).
#    Create .env in your editor with:
#      OPENSUBTITLES_USER=myuser
#      OPENSUBTITLES_PASS=mypass
python3 scripts/live_test.py --download

# 4. Run live pytest suite
python3 -m pytest -m live
```


---

## 4. Kodi Repo Compliance & Schema Validation

Verify that your changes satisfy all official Kodi repository standards:

```bash
# Run kodi-addon-checker across Kodi branches
kodi-addon-checker --branch omega .
kodi-addon-checker --branch piers .
kodi-addon-checker --branch nexus .
kodi-addon-checker --branch matrix .
```

---

## 5. Development Cycle Summary

```
Edit Python Code  ──▶  Click "Search Subtitles" in Kodi  ──▶  View Live Log Output
       ▲                                                              │
       └──────────────────────── Fix / Iterate ───────────────────────┘
```

---

## 6. 🚀 Step-by-Step Release Flow

When releasing a new version, follow this checklist in order:

### Step 1: Bump Version & Update Changelogs
1. **`addon.xml`**: Update `version="x.y.z"` attribute on `<addon>` tag.
2. **`addon.xml` `<news>`**: Add short release summary (keep total `<news>` length **under 1500 chars**).
3. **`changelog.txt`**: Add full, unconstrained release notes at the top.
4. **`README.md`**: Add the release summary under the documentation links.

### Step 2: Run Tests & Verification
```bash
# 1. Run local mock test suite
python3 -m pytest

# 2. Run Kodi schema & compatibility checker
kodi-addon-checker --branch omega .
```

### Step 3: Package Clean Release ZIP
```bash
python3 scripts/build_release_zip.py
```
* Automatically performs a security scan for credentials and builds `dist/service.subtitles.opensubtitles-com-x.y.z.zip`.

### Step 4: Commit & Tag in Git
```bash
git add addon.xml changelog.txt README.md
git commit -m "[service.subtitles.opensubtitles-com] x.y.z"
git tag -a vx.y.z -m "Release vx.y.z"
```

### Step 5: Push to Remotes
```bash
# Push branch and tags to fork (opensubtitles) and origin (opensubtitles-dev)
git push fork v1.0.14-hygiene --tags
git push origin master --tags
```

### Step 6: Submit to Official Kodi Repository (`xbmc/repo-plugins`)
1. Create a PR to [`xbmc/repo-plugins`](https://github.com/xbmc/repo-plugins) targeting the appropriate branch (`omega`, `piers`, etc.).
2. PR title must be: `[service.subtitles.opensubtitles-com] x.y.z`.
3. Must contain **exactly 1 commit** with the clean changes.

