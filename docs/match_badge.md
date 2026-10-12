# The `(+NN)` match badge

Every subtitle row in the Kodi subtitle list can end with a yellow number in
brackets — `(+30)`, `(+17)`, `(+99)`. This document explains what it is, how it
is computed, and what it is *not*. It is written so it can be pasted into a
support answer.

## Short answer

`(+NN)` is a **match confidence score**: how well that subtitle's release
matches the exact video file you are playing, on a 1–99 scale. Higher = more
likely to be in sync out of the box. The list is sorted by it, best first.

It is **not** a count of files, versions, downloads, votes, or alternative
subtitles. It is not a rating by other users.

Introduced with the smart release matcher in the 1.0.x line; the setting is
**Smart Release & Subtitle Matching** (`smart_ranking`, default on).

## Where it comes from

`resources/lib/matcher.py`:

- `calculate_match_score()` produces a raw internal score (0 – 15000+).
- `get_match_display_tag()` compresses that raw score into the displayed
  `(+1)`–`(+99)` badge.

The badge is appended at the end of the release title (label2), after any other
badges: `[Release Title] [Trusted] [AI] [Machine] [Forced] (+NN)`.

## What raises or lowers the raw score

| Signal | Effect |
|---|---|
| Exact moviehash match (bit-exact file) | +10000 — and **no badge is shown**, Kodi draws its own sync icon instead |
| Subtitle release name identical to the video filename | +5000 |
| One filename contained in the other | +3000 |
| Same release group (strongest timing predictor) | +1500 (different group: −100) |
| Same cut/edition (Extended, Director's, Theatrical…) | +1000 (different cut: −2000; only one side declares a cut: −500) |
| Same source (BluRay/WEB/DVD…) | +800 (WEB↔BluRay cross: +300; CAM vs digital: −3000) |
| Same streaming service | +500 |
| Same resolution | +300 |
| Same video codec / audio codec | +150 / +100 |
| Fuzzy filename similarity | up to +500 |
| Hearing-impaired preference match | ±350/−150 when SDH is preferred |
| TV-episode release offered for a movie (catalog mislink) | −1500 |
| AI translated / machine translated | −3500 / −5000 |
| Trusted uploader, user rating, download count | up to +100 / +50 / +50 |

Guessit data from the OpenSubtitles `utilities/guessit` service fills in release
group, source, resolution and codec when the raw filename does not expose them.

## Raw score → badge

| Raw score | Badge |
|---|---|
| ≥ 5000 | `(+99)` |
| 2000 – 4999 | `(+80)` … `(+95)` |
| 1000 – 1999 | `(+60)` … `(+79)` |
| 500 – 999 | `(+40)` … `(+59)` |
| 100 – 499 | `(+15)` … `(+39)` |
| 1 – 99 | `(+1)` … `(+14)` |
| ≤ 0 | no badge |

So the scale is relative, not a percentage: `(+99)` means "release string
matches your file", `(+30)` means "some tokens line up — same title, little
else", `(+17)` means "barely anything in common beyond the title match".

## Why a hash match shows no number

A moviehash match is a bit-exact match against your exact file — Kodi renders
its own native sync icon for it, so the add-on deliberately returns an empty
badge to avoid duplicating that signal (see the Kodi UI gotchas in
`CLAUDE.md`).

## Turning it off

Settings → **Smart Release & Subtitle Matching** (`smart_ranking`). Off = the
list falls back to API order (downloads/rating) and no badges are drawn.
Smart matching only **reorders and labels** results — it never hides a subtitle.

## Support answer template

> The number in brackets is a match-confidence score, not a file count. The
> add-on compares each subtitle's release name with your video file — release
> group, source, cut, resolution, codec — and scores how likely that subtitle is
> to be in sync with your copy, from +1 to +99. The list is sorted so the best
> match is at the top. `(+30)` and `(+17)` mean neither release is a close match
> for your file, so the top one is the safer bet. When a subtitle matches your
> file bit-exactly (by file hash), no number is shown — Kodi marks it with its
> own sync icon instead. You can switch the whole thing off with Smart Release &
> Subtitle Matching in the add-on settings.
