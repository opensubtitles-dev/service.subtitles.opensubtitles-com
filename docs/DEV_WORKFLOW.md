# ⚡ Rapid Kodi Add-on Development Workflow

This guide details the fastest setup for developing, testing, and debugging `service.subtitles.opensubtitles-com` without repetitive re-installations.

---

## 1. Instance Setup (One-Time) — and the symlink rule

Subtitle add-ons in Kodi run on-demand (`extension point="xbmc.subtitle.module"`). Every subtitle search or download spawns a new Python execution, so a symlinked checkout means **every code edit is instantly active**. That convenience is also the single most destructive trap in this project.

> ### 🔴 HARD RULE — never symlink a checkout into a Kodi instance that can install this add-on
>
> Kodi's installer **deletes the existing add-on directory before moving the new files into place, and that delete follows symlinks**. If `addons/service.subtitles.opensubtitles-com` is a symlink to your git checkout, an install or auto-update of the same add-on id **recursively wipes the checkout**. The install then fails too, because the now-dangling symlink still occupies the path:
>
> ```
> CAddonInstaller: installing 'service.subtitles.opensubtitles-com' version '1.0.90' from repository 'repository.xbmc.org'
> error: Failed to move new addon files from '.../addons/temp/97118e9b-...' to '.../addons/service.subtitles.opensubtitles-com'
> ```
>
> This destroyed the working copy on 2026-09-15, the day 1.0.90 landed in the official Kodi repository. Uncommitted work was unrecoverable.
>
> **Therefore:**
> 1. A symlinked checkout is allowed **only** in a dedicated dev instance that has **no repository serving this add-on id** (`repository.opensubtitles-com` not installed, add-on never installed from a repository, auto-update off).
> 2. Your normal Kodi profile — the one with the OpenSubtitles.com repository — gets a **copy**, never a link. Kodi may delete a copy freely; nothing of yours lives inside it.
> 3. Run `scripts/kodi_dev.sh guard` before installing anything from a repository. It fails on exactly this configuration.
> 4. If an install ever fails with *"Failed to move new addon files"*, check for a leftover symlink at that path first — that is the signature.

Everything below is handled by `scripts/kodi_dev.sh`, which keeps the lines and instances separate by construction:

```bash
scripts/kodi_dev.sh setup 2x      # create the dev instance (and, for 1x, the worktree)
scripts/kodi_dev.sh deploy 2x     # rsync a COPY of the checkout into that instance
scripts/kodi_dev.sh run 2x        # launch Kodi against it (isolated HOME)
scripts/kodi_dev.sh log 2x        # stream that instance's add-on log lines
scripts/kodi_dev.sh guard         # fail on any unsafe symlink, anywhere
scripts/kodi_dev.sh status        # what is wired where
```

Instant-edit symlinking is still available where it is safe — inside a dev instance with no repository installed:

```bash
# macOS, dev instance only (never the default profile):
ln -s "$(pwd)" "$HOME/.kodi-dev/2x/Library/Application Support/Kodi/addons/service.subtitles.opensubtitles-com"
```

*(If you edit `resources/settings.xml` or `addon.xml`, close and reopen the Kodi settings dialog or restart Kodi.)*

---

## 1b. Developing 1.x and 2.x in parallel

Both lines ship under the **same add-on id**, so they can never coexist in one Kodi profile. Kodi derives its entire profile from `HOME` (verified in xbmc `SettingsComponent.cpp`, `InitDirectoriesOSX`), which is what gives each line its own instance:

| Line | Branch | Checkout | Kodi instance |
|------|--------|----------|---------------|
| 1.x maintenance (released, in the official Kodi repo) | `master` | `../service.subtitles.opensubtitles-com-1x` (git worktree) | `~/.kodi-dev/1x` |
| 2.x development | `develop` | this checkout | `~/.kodi-dev/2x` |

```bash
scripts/kodi_dev.sh setup 1x      # creates the worktree on master + its instance
scripts/kodi_dev.sh deploy 1x && scripts/kodi_dev.sh run 1x
```

Rules for the parallel setup:

- **One line per instance.** Never deploy both lines into the same `HOME`; the second install overwrites the first and you lose track of which code you are testing.
- **No OpenSubtitles repository inside a dev instance.** Without it Kodi cannot auto-update over your work, which is what makes a symlink safe there.
- **Leave add-on auto-update off** in dev instances (`Add-ons > My add-ons > OpenSubtitles.com > Auto-update: No`).
- **Keep the default profile as the user-realistic one:** add-on installed from the repository, a plain copy, used to verify what real users actually receive.
- **Never use a worktree path as an rsync `--delete` target**, and never point `deploy` at a checkout — deploy writes only into `~/.kodi-dev/<line>/…/addons/`.
- Commit or push before any repo-install test. Committed work survived 2026-09-15; uncommitted work did not.

---

## 2. Live Log Streaming

Keep a terminal open to monitor live logs and debug output while testing inside Kodi:

```bash
# Run the included helper script:
bash scripts/stream_kodi_logs.sh
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

### Step 6: Submit to Official Kodi Repository (`xbmc/repo-scripts`)
1. Create a PR to [`xbmc/repo-scripts`](https://github.com/xbmc/repo-scripts) targeting branch **`matrix`**. Subtitle add-ons live in `repo-scripts`, never `repo-plugins` (the add-on has never existed there; the 2026-08 repo-plugins PRs all stalled for that reason). `matrix` is the only branch this add-on is merged into — the `nexus`/`omega`/`piers` mirrors inherit that same build, so one PR covers every Kodi version. Verified 2026-10-12: all four feeds on `mirrors.kodi.tv` serve 1.0.90.
2. PR title must be: `[service.subtitles.opensubtitles-com] x.y.z`.
3. Must contain **exactly 1 commit** with the clean changes.

