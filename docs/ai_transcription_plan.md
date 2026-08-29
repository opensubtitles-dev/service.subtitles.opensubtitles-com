# AI Transcription — Design Plan (2.0.x)

Generate subtitles for media that has none, via the transcription service on
ai.opensubtitles.com. Status: **CLIENT PIPELINE IMPLEMENTED on develop (2026-08-26)** — expert
setting `ai_transcription_enabled` injects an "[AI] Generate by transcription"
row into every search; picking it runs `resources/lib/transcriber.py`
(capability probe + one-time benchmark cached in the profile, source-rung
selection, ffmpeg audio extraction, chunked upload, job polling). The real
endpoints stay PROPOSED (404 → friendly dialog); the Development-tab
`test_transcribe_mock` setting simulates the server for end-to-end testing
in Kodi. Server side + Android NDK rung still open.

---

## 1. The one constraint that shapes everything

**Kodi's Python API exposes no audio.** No PCM tap, no demux/decode surface
(`RenderCapture` is video-only), Kodi's internal ffmpeg is statically linked and
unreachable, and bundling an ffmpeg executable violates official-repo rules —
and cannot execute on Android at all (W^X: no exec from app-writable storage,
API 29+).

Consequence: the client either ships the *source bytes* (whole file or remuxed
audio track), hands the server a *URL*, or drives the *OS's own codecs*.

## 2. Capability ladder (best available wins)

| Rung | Mechanism | Upload size (2h movie) | Platforms |
|------|-----------|------------------------|-----------|
| 1 | Local ffmpeg → Opus 16kHz mono | ~15–40 MB | Desktop (download static build), LibreELEC/CoreELEC (often present) |
| 2 | **Android NDK media via ctypes** — `libmediandk.so` (`AMediaExtractor`/`AMediaCodec`/`AMediaMuxer`) is a public NDK lib, loadable in-process; W^X does not apply to system libs | ~20–40 MB (AAC mono) | Android (must pass probe first) |
| 3 | URL mode — send the resolved stream manifest (`getPlayingFile()` → `.m3u8`/`.mpd`/http), server fetches | ~0 | any platform, non-DRM streams |
| 4 | Pure-Python audio-track remux (MP4 sample tables / MKV EBML parsing, byte copy, no codec) | ~115–560 MB (AAC/AC3 track) | universal fallback, incl. Android local files |
| 5 | Chunked whole-file upload via `xbmcvfs.File` | 2–8 GB | last resort, with explicit size warning |

Out of reach forever: DRM content, `pvr://` live TV.

## 3. Architecture

- **Official add-on stays clean.** It only *detects* the companion
  (`Addons.GetAddonDetails`) and offers: "AI transcription available — install
  the OpenSubtitles AI helper from our repository" (reuses the fast-track
  onboarding instructions flow from `check_updates.py`).
- **Companion add-on** (proposed id: `script.opensubtitles.aihelper`) lives ONLY
  in kodi.opensubtitles.com: platform detection, ffmpeg fetch where legal,
  NDK-media path on Android, remux fallback, upload, job polling.
- **Server** (ai.opensubtitles.com): accepts audio/video/URL, ffmpeg demux +
  transcription, **stores the result as a public subtitle keyed by
  moviehash/feature id** — first transcriber feeds every later user; the
  expensive paths run once per release globally. Requests must check the cache
  by moviehash BEFORE offering paid transcription.
- **Async job flow**: transcription takes minutes → `service_monitor.py` polls
  the job and toasts "AI subtitle ready" / it is simply present on next play.
  Mirrors the existing on-demand AI translation + credits UX.

## 4. API contract (SPEC-VERIFIED — docs/opensubtitles_api_reference.html, 2026-08-26)

```
GET  /api/v1/ai/info/transcription    Api-Key only
  -> { data: [ { name, display_name, description, pricing, reliability,
                 price (per second), languages_supported: [{language_code
                 (incl "auto"), language_name}] } ] }        # e.g. "aws"
POST /api/v1/ai/transcribe            Api-Key + Bearer
  query: api (engine name), language (media language)  +  multipart file
  HARD CAP: 100 MB per file  ->  { status: "CREATED", correlation_id }
GET  /api/v1/ai/transcribe/{correlation_id}
  -> status: CREATED | PENDING | COMPLETED | ERROR | TIMEOUT
     (COMPLETED payload shape loose - client accepts url or inline text)
```

Consequences vs the earlier proposal: NO URL mode and NO chunked upload -
the 100 MB cap makes local audio extraction the REQUIRED path for movies
(2h @ 48k mono AAC ~= 42 MB fits); no moviehash cache-hit response yet
(server-side dedup remains a wishlist item). X-Kodi-Origin-Repo rides along
as everywhere.

## 5. Consent, cost, limits

- Explicit opt-in dialog before ANY byte of user media leaves the device
  (privacy/GDPR); paid AI-credits action, priced per media minute.
- Server-side caps: max duration, max upload size, rate limit per account.
- Cache-hit path is free and instant — the dialog must say which case applies.

## 6. Phases

1. **Probe** (`tests/probe/service.opensubtitles.transcriptionprobe/`) — verify
   platform capabilities on real devices; fills the ladder table with facts.
   Desktop/containers via the existing smoke harness; Android via sideload zip.
2. **Server contract** — finalize the PROPOSED endpoints with the API team,
   moviehash cache included.
3. **Companion add-on MVP** — desktop ffmpeg rung + URL rung + upload rung;
   published to the fast-track repo only.
4. **Android rung** — NDK-media ctypes implementation (hardest code: AMediaCodec
   dequeue loop through ctypes; only if the probe passed on real boxes).
5. **Official add-on integration** — detection + offer dialog + job UX via the
   background service.

## 7. Probe results so far (ground truth)

| Device | Verdict | Detail |
|--------|---------|--------|
| Headless Kodi 21.3, Linux aarch64 container (2026-08-26) | `rung1-FFMPEG-OK` | ctypes ✓, exec-from-app-storage ✓ (a downloaded static ffmpeg would run), xbmcvfs ✓ |
| Android box | *pending* | sideload `dist/service.opensubtitles.transcriptionprobe.zip`, then `adb logcat -d \| grep TRANSCRIPTION-PROBE-RESULT` |
| macOS / Windows desktop | *pending* | install the same zip, result also lands in kodi.log + the add-on profile dir |

## 8. Open questions

- Companion addon id and repo listing name.
- Credit pricing per minute; who eats the cost of cache-miss failures.
- AMediaDataSource callback shim for SMB/NFS on Android (rung 2 currently
  assumes fd-able local/mounted files) — or fall through to rung 4.
- Whether the probe's findings justify skipping rung 4 entirely.


## LIVE API measurements (2026-08-29, real jobs run)

The endpoint is DEPLOYED and works end-to-end (12 s speech -> accurate SRT in
~20 s, 1 credit billed). Contract corrections vs the draft, all measured:

1. `api` and `language` are multipart FORM FIELDS - as query params the server
   answers "language parameter missing" (POST body only).
2. **The server content-sniffs uploads and accepts ONLY MPEG Audio (MP3).**
   m4a/AAC and WAV -> "media format not valid"; raw ADTS passes the sniff but
   fails the duration probe. Extensions are ignored (a lying .m4a with MP3
   payload is accepted). CONSEQUENCE: the AAC-producing rungs (android_ndk,
   afconvert, windows_mf) and whole-file video upload are gated OFF in
   choose_source (SERVER_ACCEPTS_AAC = False) until the API adds AAC.
   ffmpeg and GStreamer rungs emit 32k mono MP3 (~28 MB / 2h).
3. Engines really offered: aws 0.132, openai 0.033, assemblyAI 0.0225,
   nano 0.0075 (per second; minimum charge observed: 1 credit). "nano" was
   routed to assemblyAI server-side.
4. COMPLETED payload: {"correlation_id", "status", "data": {"id",
   "file_name", "url", "seconds_count", "unit_price", "total_price",
   "credits_left", "task": {...}}} - the url is under data (handled).
5. The result URL (/ai/files/...) requires Api-Key + Bearer (401 bare).
6. ERROR payload: "data" is a LIST of message strings (incl. a PHP trace) -
   the client joins the first non-trace messages for the user dialog.

### Requests for the API team (restores the verified no-install matrix)

- Accept AAC (ADTS + M4A): re-enables Android (NDK encoder has no MP3),
  macOS afconvert and Windows MF rungs - all client code is done and
  device-verified, one server change flips them on.
- Accept video containers <= 100 MB (server-side demux): restores the
  whole-file rung for ffmpeg-less platforms.
- ADTS duration probe: decode-based duration instead of header-based.
