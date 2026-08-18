# Kodi Add-on Standards & Submission Rules

This document outlines the official standards, repository rules, and validation guidelines for `service.subtitles.opensubtitles-com` to ensure full compliance with the official Kodi repository ([`xbmc/repo-plugins`](https://github.com/xbmc/repo-plugins)).

---

## 1. `addon.xml` Guidelines & Schema Validation

- **News Tag Limit**: The `<news>` tag in `addon.xml` has a strict schema limit of **1500 characters** (`xs:maxLength="1500"`).
  - Only include recent release highlights (last 1–3 versions).
  - Full release history must be recorded in [`changelog.txt`](changelog.txt).
- **URLs & Redirections**: All metadata URLs (`<forum>`, `<website>`, `<source>`) must be valid, active HTTPS links without redirections.
  - Forum: `https://forum.opensubtitles.com/t/new-opensubtitles-com-kodi-subtitles-addon/1673`
  - Website: `https://www.opensubtitles.com`
  - Source: `https://github.com/opensubtitles-dev/service.subtitles.opensubtitles-com`
- **Dependencies**: Target Python 3 (`xbmc.python >= 3.0.0`) and only declare required official modules.
- **Provider Names & IDs**: The `id` attribute must match the folder/package name (`service.subtitles.opensubtitles-com`).

---

## 2. Artwork & Media Asset Specifications

All artwork must adhere to Kodi's dimension and size constraints:

| Asset | Format | Size / Resolution | Transparency | Max File Size |
|---|---|---|---|---|
| **Icon** (`icon`) | PNG | 512×512 or 256×256 | Solid (No transparency) | — |
| **Fanart** (`fanart`) | JPG / PNG | 1920×1080 or 1280×720 | — | 1,000 KB |
| **Screenshots** (`screenshot`) | JPG / PNG | 1280×720 or 1920×1080 | Solid | 750 KB |

Assets must be explicitly declared in `<assets>` in `addon.xml`.

---

## 3. Python & Coding Rules

- **No `print()` Calls**: Never use `print()`. Use `xbmc.log(msg, level=xbmc.LOGINFO/LOGDEBUG/LOGERROR)`.
- **Privacy & Security**: Never log user credentials, API keys, or session tokens to the Kodi debug log.
- **Python 3 Compatibility**: Code must be 100% compatible with Python 3 (Kodi 19 Matrix, 20 Nexus, 21 Omega, 22 Piers).
- **Package Names**: Avoid naming internal modules with names that shadow Python standard library modules (e.g., use `osclient`, never `os`).

---

## 4. Local Validation with `kodi-addon-checker`

Run the validator across all supported branches before submitting:

```bash
# Install validator in Python venv
pip install kodi-addon-checker

# Run check for Kodi Omega (21)
kodi-addon-checker --branch omega .

# Run check for Kodi Piers (22), Nexus (20), Matrix (19)
kodi-addon-checker --branch piers .
kodi-addon-checker --branch nexus .
kodi-addon-checker --branch matrix .
```

All checks should pass with **0 problems**.

---

## 5. Submitting Updates to Official Kodi Repositories

When submitting updates to [`xbmc/repo-plugins`](https://github.com/xbmc/repo-plugins):
1. **Branch**: Create PR against the appropriate Kodi branch (e.g., `matrix`, `nexus`, `omega`, `piers`).
2. **One Commit Only**: Squash all changes into a single commit.
3. **Commit Title Format**: `[service.subtitles.opensubtitles-com] <version>` (e.g., `[service.subtitles.opensubtitles-com] 1.0.15`).
4. **Clean Workspace**: Ensure no `__pycache__`, `.pyc`, or temporary files are present.
