# Greptile Findings Catalog — every issue from 37 review rounds

Source: internal review rig (opensubtitles-dev PRs #45–#82 mirror rounds + #44
full-repo passes), Aug 2026. Every finding below was raised by Greptile, fixed,
and covered by a regression test. This document distills them into **classes**
so future code is written to pass review the first time.

Enforcement:
- **`scripts/greptile_gate.py`** — static AST gate for the mechanically
  detectable classes (rules G01–G11). Runs in the test suite
  (`tests/test_greptile_gate.py`), so pytest / preflight / CI all fail on a hit.
  Deliberate exceptions carry an inline `# greptile-ok: <reason>` pragma.
- **The review checklist** (bottom) — the judgment-call classes the gate cannot
  see; walk it before every release.

---

## Class 1 — Secrets and playback data in the debug log (14 findings)

Kodi debug logs are pasted on public forums. Anything derived from playback can
carry a stream token, credential or private metadata.

| # | Finding | Fixed |
|---|---------|-------|
| 1 | Raw playback URL logged in search flow | 1.0.35–1.0.37 |
| 2 | Percent-encoded token re-entered decoded basename | 1.0.42 |
| 3 | Raw `sys.argv` logged at invocation (caller add-ons embed tokens) | 1.0.52 |
| 4 | Query mappings (`query`, request vars, params) logged unredacted | 1.0.53 |
| 5 | rar-branch basename bypassed the safe deriver | 1.0.49 |
| 6 | stack:// member basename kept its query string | 1.0.57 |
| 7 | Hashing-failure log carried the raw exception (vfs errors embed the path) | 1.0.59 |
| 8 | Guessit payload + urllib exception logged (echoes filename/request URL) | 1.0.68 |
| 9 | Prepared request URLs (`r.url`) logged at 3 sites | 1.0.70 |
| 10 | `media_data` dict logged whole (library file URL inside) | 1.0.75 |
| 11 | InfoLabel mapping logged whole (integration can plant a URL) | 1.0.76 |
| 12 | `redact_path` kept percent-encoded token in the PATH component | 1.0.72 |
| 13 | …and single-decode missed double-encoded tokens | 1.0.73 |
| 14 | …bounded decode passed residue through → now fails closed | 1.0.74 |

**Conditions (gate: G03, G04, G05, G06, G07):**
- Never log a raw exception object — log `type(e).__name__`. Exception
  messages embed paths, URLs and payloads.
- Never log `sys.argv`, a prepared `r.url`, or a whole dict that can carry a
  path/URL. Redact per value: `redact_path(v) if "://" in v else v`.
- Every filename derived from a playback path goes through
  `safe_media_filename`; every path that reaches a log goes through
  `redact_path`. Both decode percent-encoding **to fixpoint** and **fail
  closed** on undecodable residue.

## Class 2 — Malformed external data aborts instead of degrading (13 findings)

Doctrine: **no malformed API/scraper/player data may abort a search.** Shape-
check every layer; one bad entry degrades, the rest continue.

| # | Finding | Fixed |
|---|---------|-------|
| 1 | Malformed `/features` `data[0]` aborted search | 1.0.34 |
| 2 | `attributes` non-dict crashed enrichment | 1.0.43 |
| 3 | `episodeguide` non-object crashed | 1.0.44 |
| 4 | TypeError escaped login/download excepts | 1.0.45 |
| 5 | `data: null` hit `len()` | 1.0.47 |
| 6 | Non-object JSON bodies at all `.json()` sites | 1.0.48 |
| 7 | One bad entry disabled smart ranking | 1.0.49 |
| 8 | Missing `languages` param → `unquote(None)` TypeError | 1.0.50 |
| 9 | Guessit non-object body dereferenced in success log | 1.0.50 |
| 10 | Malformed `videoinfo.current_size` property → ValueError | 1.0.69 |
| 11 | Invalid download `file_id` → KeyError out of the handler | 1.0.69 |
| 12 | Non-object entry re-raised inside the score-failure handler | 1.0.75 |
| 13 | Out-of-range guessit year/episode failed the request and stopped fallbacks | 1.0.77 |

**Conditions (gate: G08, G11):**
- `isinstance()` check every `.json()` body and every nested field before use.
- `int()`/`float()` of any external value goes inside try/except or a coercion
  helper (`_to_int`, `_valid_coordinate`, `_valid_year`).
- `x.get(k)` returns None — never feed it to `unquote`/`len`/arithmetic bare.
- Per-entry try/except in loops over API results: one entry fails, the loop
  continues; and the handler itself must not assume the entry's shape.

## Class 3 — Concurrency across Kodi sub-interpreter invocations (8 findings)

Kodi runs each invocation as a fresh sub-interpreter in ONE process. Module
state doesn't span invocations; window properties do — with atomic single
reads/writes but **no compare-and-swap**.

| # | Finding | Fixed |
|---|---------|-------|
| 1 | Temp-file races between overlapping invocations | 1.0.31 |
| 2 | PID-based temp names identical across invocations → uuid | 1.0.32 |
| 3 | Clear Cache raced active downloads (60s vs 3600s windows) | 1.0.56 |
| 4 | Cache index RMW lost concurrent writers' keys | 1.0.54→1.0.63 (token spinlock) |
| 5 | Blind index clear orphaned mid-clear writes | 1.0.55→1.0.65 (single lock hold) |
| 6 | Livelock fallback did a blind write | 1.0.64 (verified merge) |
| 7 | Stalled holder released a stolen lock | 1.0.67 (token-checked release) |
| 8 | Long clear outlived the stale window | 1.0.77 (heartbeat lease) |
| — | Non-atomic publication (property vs index) | 1.0.66 (one lock hold) |

**Conditions (checklist — not mechanically detectable):**
- Any read-modify-write on shared state (window properties, files) needs the
  token-spinlock pattern (`cache.Cache._with_index_lock`): write token+time,
  read back, only the surviving token proceeds; heartbeat during long holds;
  release only your own token; verified-merge fallback, never a blind write.
- Multi-step operations on shared state happen in ONE lock hold.
- Shared timing constants live in one place (`utilities.TEMP_MAX_AGE_SECONDS`).

## Class 4 — Search correctness (10 findings)

| # | Finding | Fixed |
|---|---------|-------|
| 1 | `[6:]` slice mangled every non-rar basename | 1.0.29 |
| 2 | tvshowid clobbered by empty InfoLabel | 1.0.31 |
| 3 | Non-numeric `parent_imdb` int() crash | 1.0.40 |
| 4 | Numeric fields sent as strings; inverted season validator | 1.0.56 |
| 5 | Season 0 (specials) dropped by truthiness — request layer | 1.0.57 |
| 6 | Season 0 dropped — /features resolver | 1.0.58 |
| 7 | Compound "S01E05" labels mangled by specials substring test | 1.0.59 |
| 8 | Fallback retries over-constrained by leftover ids | 1.0.57 |
| 9 | Look-alike gate: per-attempt title + short-title guard + malformed-entry skip | 1.0.61/62 |
| 10 | Malformed /features coordinates silently widened to show-wide search | 1.0.59 |

**Conditions (gate: G10; rest checklist):**
- **0 is a value.** Truthiness on season/episode/year drops season 0 —
  compare against `None`/`""` explicitly, everywhere.
- Every id/coordinate is validated/coerced at the boundary it enters
  (`_to_int`, `_valid_coordinate`, `_strip_imdb_tt`), not deep inside.
- A fallback attempt is self-contained: null out id fields it doesn't name.
- Fuzzy-match acceptance needs a relevance gate; the gate judges each
  attempt against ITS OWN query, is stricter for one-word titles, and holds
  results back rather than discarding them.

## Class 5 — Python 3 / API-contract landmines (6 findings)

| # | Finding | Fixed |
|---|---------|-------|
| 1 | `x is str` type-identity comparisons in setters | 1.0.65 |
| 2 | `.length()` nonexistent method | 1.0.65 |
| 3 | Inverted comparisons rejecting ALL valid values (`id`, `season`, `parent_feature_id`) | 1.0.56/65/66 |
| 4 | `/` true division fed `%d` (multipart RAR) | 1.0.71 |
| 5 | Settings offered "only" where the API accepts include/exclude | 1.0.68 |
| 6 | Unquoted `msgstr` broke the zh_CN catalog | 1.0.56 |

**Conditions (gate: G01, G02, G09; tests):**
- Dead code isn't dead to a reviewer: setters nobody calls still must be
  correct — fix or delete.
- Settings option lists mirror the API contract exactly (test:
  `test_settings_xml_offers_no_only_for_translation_filters`).
- Every shipped `strings.po` is syntax-validated (`test_language_files.py`).
- XML `<news>` ≤1500 chars and XML-safe; entry points ≤15 code lines;
  Python 3.6 floor for shipped code (kodiai_gate + vermin).

## Class 6 — UX honesty and docs (5 findings)

| # | Finding | Fixed |
|---|---------|-------|
| 1 | Update flow gave no feedback / stale info dialog | 1.0.2x series |
| 2 | XML entity expansion in remote manifest (DOCTYPE bomb) + size cap | 1.0.41 |
| 3 | README linked docs/ files absent from the shipped zip | 1.0.51 |
| 4 | Walkthrough never said to disable Unknown sources again | 1.0.60 |
| 5 | "Still installing" claimed when origin was unreadable | 1.0.60 |

**Conditions (checklist):**
- Every user-facing claim must be TRUE in the failure path too — if you can't
  verify an outcome, say so, and say why it may not happen.
- Docs shipped in the zip may only reference things that exist in the zip
  (or absolute URLs).
- Anything fetched remotely gets a size cap and an entity-expansion check.

---

## Self-audit round (v1.0.78) — found by simulating the reviewer, not by it

A manual deep pass over every shipped file, hunting the same classes harder
than the gate could, produced 13 more fixes before any reviewer saw them:

| # | Finding | Class |
|---|---------|-------|
| 1 | Update check took the FIRST manifest answer; a lagging feed advertised an older version than GitHub carried → max across sources | 4 (first-non-empty-wins) |
| 2 | Clear Cache hardcoded "0 items" although concurrent writes legitimately survive → recount | 6 (honest UX) |
| 3 | `get_params()` returned a LIST for empty query strings; callers `.get()` crashed | 2 |
| 4 | `sys.argv[2]` IndexError on RunScript-style short argv | 2 |
| 5 | Malformed `videoinfo.current_oshash` went out as moviehash and failed the request | 2 |
| 6 | Failed download continued into file-path logic; `params["language"]` could KeyError | 2 |
| 7 | Whole `attributes` payload dumped per row in the render loop | 1 (bare-arg log, gate blind spot) |
| 8 | Bad `ratings` value cost the entire row over a cosmetic icon | 2 |
| 9 | `error(module, id, e)` call sites routed the raw exception into `log()` | 1 (call-shape blind spot) |
| 10 | `ServiceUnavailable("Connection error: {e!r}")` embedded request URLs into dialogs | 1 |
| 11 | Non-smart sort crashed on mixed str/int votes/ratings | 2 |
| 12 | `clean_feature_release_name`/`get_flag` crashed on null API fields | 2 |
| 13 | `_attrs()` helper: matcher dereferenced non-dict `attributes` in language grouping | 2 |

Gate upgrades from this round: log-call checks now cover **bare Name
arguments, %-formatting and the `error(…, e)` call shape**, not just
f-strings. Lesson: whenever a finding is fixed, grep for the PATTERN, not the
instance — 9 of these 13 were siblings of already-fixed findings.

---

## Pre-ship procedure

1. `python3 -m pytest` — includes the greptile gate, PO validation,
   settings-contract, packaging-secret and all regression tests.
2. `python3 scripts/preflight.py` — versions, news cap, built-zip inspection,
   kodi-addon-checker.
3. `python3 scripts/kodiai_gate.py` — entry points, dependency floors.
4. Walk the checklist conditions above for any NEW code touching:
   logging (Class 1), external data intake (Class 2), shared state (Class 3),
   search parameters (Class 4).
5. Only then roll a mirror PR for a real Greptile pass.
