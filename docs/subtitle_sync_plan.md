# Auto Subtitle Synchronization — design (v2.x)

Status: DESIGN — nothing implemented. Companion to `ai_transcription_plan.md`;
reuses its capability-ladder model and several existing mechanisms.

## Why this belongs in the add-on

Bad sync is the #1 subtitle complaint after "not found". The smart matcher
reduces it BEFORE download (release/hash matching); this feature repairs it
AFTER. Same product promise, and the building blocks already exist in 2.0:

- the background service samples `Player.SubtitleDelay` every second of
  playback (built for upload eligibility)
- sessions record which subtitle file played against which moviehash
- the transcription capability probe already finds and benchmarks ffmpeg
- the settle-window logic distinguishes our own subtitle switches from the
  user's

Guardrails (doctrine):
- NEVER touch a `moviehash_match=true` subtitle — it is already exact.
- Silent auto-correction only on HIGH confidence; otherwise notify and offer.
- Never fight the user: a manual delay in progress pauses all automation.
- Corrections are applied by REWRITING the subtitle file's timestamps, not by
  a delay API (JSON-RPC has no delay setter; a rewritten file persists for
  future plays and is what auto-upload would share).

## The ladder (mirror of the transcription rungs)

### Rung 1 — Crowdsourced delay memory (build FIRST)

The service already knows, per session: moviehash + subtitle file_id + the
delay the user ended at. Report that tuple; the server aggregates a median
per (file_id, moviehash) pair. The next user downloading that subtitle for
that release gets the correction applied before Kodi ever sees the file.

- Zero signal processing. Works on EVERY device (ffmpeg-less boxes included).
- Compounds with the user base — a correction one user makes fixes it for all.
- Client cost: ~50 lines (the sampling exists; add report + apply).

PROPOSED server contract (for the API team, same style as /subtitles/rate):

    POST /api/v1/subtitles/sync-report        (JWT bearer)
    { "file_id": <int>, "moviehash": "<16-hex>",
      "delay_ms": <int>,                      # + = subtitles were late
      "fps_scale": <float, optional> }        # 1.0 when untouched

    GET /api/v1/subtitles/sync-hint?file_id=..&moviehash=..   (Api-Key)
    -> { "data": { "delay_ms": <int>, "fps_scale": <float>,
                   "samples": <int>, "confidence": <0..1> } }

Client applies silently when `confidence` high and `samples >= 3`; otherwise
offers. Privacy: the tuple carries no titles/paths — ids and a hash only.

### Rung 2 — Reference alignment, subtitle vs subtitle (offline fallback)

If ANY language has a `moviehash_match` subtitle for the playing file, its cue
timings are ground truth for this exact release. Align the desynced
subtitle's inter-cue-gap sequence against the reference's (dynamic
programming / coarse-to-fine offset+scale search) and derive:

- constant offset (the common case), and
- linear scale (23.976 <-> 25 fps drift).

Pure Python, no audio, no ffmpeg, fully unit-testable. Uses the OpenSubtitles
catalog itself as the sync reference — a capability only we have. One extra
download burns quota: prefer a reference the user already downloaded, else ask
before spending.

### Rung 3 — Audio correlation (last, maybe never)

ffsubsync-style: extract audio via ffmpeg (reuse the transcription probe and
extraction code), compute a coarse speech on/off envelope, cross-correlate
with the subtitle's cue on/off signal. Heaviest rung; only worth it if rungs
1+2 leave a measurable gap. Same ffmpeg gating and benchmark as transcription.

## Placement

- `resources/lib/syncer.py` — pure module (no Kodi imports in the math),
  pattern of `matcher.py` / `upload_eligibility.py`:
  `parse_srt / shift(offset, scale) / align_to_reference / apply_hint`
- Download path hook (dialog download + service auto-download): apply rung-1
  hint before handing the file to Kodi; notify "subtitle retimed +1.2s".
- Session close: delay report to the server (consent follows the same setting
  as the correction feature itself).
- Setting: expert toggle `auto_sync` first (like transcription), promoted to
  a normal setting once proven.

## Invocation — how the user reaches it

Three tiers, by how the need arises:

1. **Subtitle-dialog row** (canonical in-plugin path). A subtitle SERVICE
   add-on only gets UI when Kodi opens the subtitle search dialog — so that
   dialog is our storefront. Inject a top row like the transcribe row:

       [SYNC] Fix timing of the current subtitle        action=sync

   Mid-playback route: pause -> subtitles button -> OpenSubtitles.com -> SYNC
   row. Two clicks more than a hotkey, available on every remote, zero setup.
   The handler runs the ladder against the ACTIVE subtitle and swaps in the
   corrected file via `setSubtitles()` (takes effect immediately, position
   untouched).

2. **The delay-nudge moment** (the assistive magic). The instant a user SEES
   bad sync, what they actually do is open Kodi's own subtitle-offset dialog
   and start nudging. Our service watches `Player.SubtitleDelay`: when the
   user nudges more than twice in one session (= struggling, not fine-tuning),
   offer ONCE via yes/no with autoclose: "Try automatic synchronization?"
   Yes -> same action=sync flow. This meets the user exactly at the moment of
   intent, with zero new UI to learn. Strict anti-annoyance rules: once per
   session, never while `moviehash_match`, silent if the nudge settles.

3. **Power path**: `RunScript(.../sync_now.py)` entry point so users can bind
   a remote key via keymap. Costs one thin script; documented, not promoted.

Implementation note for action=sync: Kodi does not expose the active EXTERNAL
subtitle's file path via JSON-RPC. Resolution order: (a) the service session
knows the path for anything we loaded; (b) otherwise probe video-folder
sidecars (the upload dry-run already does this); (c) otherwise the row falls
back to "download + sync" in one step using the best search result.

## Rollout order

1. Rung 1 client (apply + report) behind `auto_sync` expert toggle, with the
   server contract proposed to the API team (works locally without the server:
   apply-side no-ops until the hint endpoint exists).
2. Dialog SYNC row + delay-nudge offer, wired to rung 2 (offline aligner) so
   the feature is useful before any server work lands.
3. Evaluate rung 3 only after telemetry shows rungs 1+2 miss real cases.
