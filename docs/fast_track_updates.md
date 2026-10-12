# The fast-track update notification

Users see a yes/no dialog like:

> Fast-track repo: **v1.0.91** | Official Kodi repo: not yet available (installed: v1.0.90).
> Show how to enable fast-track updates?

This document explains what it does, when it fires, and how to answer support
questions about it.

## What it is

Two distribution channels exist for this add-on:

| Channel | Source | Pace |
|---|---|---|
| Official Kodi repository | `xbmc/repo-scripts`, branch per Kodi version | slow — every release is human-reviewed and merged by Kodi team volunteers; weeks to months |
| Fast-track repository | `https://kodi.opensubtitles.com` (`repository.opensubtitles-com`) | immediate — new builds land the day they ship |

Kodi 19+ **pins an add-on to the repository it was installed from** ("origin").
An add-on installed from the official Kodi repo will never receive an update
from our repository, even if ours is installed and enabled. That pinning is the
whole reason for the dialog: the add-on knows a newer build exists but also
knows Kodi cannot deliver it to this install.

## When it fires

Only from **Settings → Check for updates** (`check_updates.py`, run by the
settings action at `resources/settings.xml:314`). It is user-initiated — it does
not appear on its own, at startup, or during playback.

The background service (`check_for_update_silently()` in
`resources/lib/background_service.py`) runs at most **once per 24 hours** and
only ever shows a passive 6-second toast when a newer version exists. It asks
nothing and shows no yes/no dialog.

Dialog branches in `check_updates()`:

- newer version + fast-track repo not usable → the yes/no above
- newer version + fast-track repo enabled and origin compatible → "Check Kodi
  repository for updates now?" with a progress dialog and a definitive
  "Updated to vX.Y.Z"
- up to date + fast-track repo not usable → "Up to date … future updates will
  NOT arrive automatically. Show how to enable fast-track updates?"

`fast_track_repo_state()` returns `enabled` / `disabled` / `missing` via
JSON-RPC (`System.HasAddon` stays true for disabled add-ons, so it is not used),
and an install origin that is some other repository is reported as
`foreign-origin`.

## What "Yes" does

Nothing is installed, enabled, or changed. **Yes only shows instructions** — a
text viewer with the 5-step install walkthrough, or a short one-step hint when
the repository is merely disabled or when the install origin points elsewhere.

Acting on those instructions (install the repository ZIP, then reinstall the
add-on from it) is what re-points the origin and makes future updates arrive
through Kodi's normal auto-update.

## Answering "is it risky / should I bother?"

- Same code, same GPL-2.0 source, same GitHub project — fast-track is just
  earlier. It carries the usual earlier-build trade-off: fixes sooner, less
  soak time before release.
- One-time install requires **Unknown sources** to be enabled for the ZIP step;
  the instructions explicitly say to turn it back off afterwards (repository
  updates work without it).
- Staying on the official repo is a perfectly valid choice — updates simply
  arrive whenever Kodi's reviewers merge them.

## Known defect fixed (2026-10-12)

`fetch_official_kodi_version()` queried `xbmc/repo-plugins`. Subtitle add-ons
live in `xbmc/repo-scripts`, so that URL **always 404'd** and the dialog said
"Official Kodi repo: not yet available" for every user — while the official repo
(matrix branch) really served v1.0.90. The lookup now tries `repo-scripts`
first and keeps `repo-plugins` as a fallback.

## Support answer template

> The dialog is only shown when you press "Check for updates" yourself — it never
> appears on its own, so selecting No does not schedule it to come back. The
> add-on has two release channels: the official Kodi repository, which updates
> whenever Kodi's reviewers merge a new version, and our own fast-track
> repository, which gets releases the day they ship. Kodi pins every add-on to
> the repository it was installed from, so if you installed from the official
> Kodi repository, the newer fast-track build cannot reach you — that is what
> the message reports. Answering Yes only displays setup instructions; it
> installs nothing and changes nothing. The only difference is timing: the same
> code, just earlier, with the usual trade-off that an earlier build has had
> less time in the wild. If you are happy getting updates whenever they land in
> the official repository, you can safely ignore the message.
