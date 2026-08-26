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

## 4. API contract (PROPOSED — spec-first per project rules; handle 404 as "not deployed")

```
POST /api/v1/ai/transcribe            multipart or JSON
  { moviehash, file_size, duration, imdb_id/tmdb_id?, language_hint?,
    source: {type: "upload"|"url", url?}, credits_ack: true }
  -> 202 { job_id, credits_charged }   | 409 { subtitle_id }  (cache hit - free)
PUT  /api/v1/ai/transcribe/{job_id}/audio     chunked upload (when type=upload)
GET  /api/v1/ai/transcribe/{job_id}   -> { status: queued|processing|done|failed,
                                           subtitle_id?, error? }
```

Every endpoint: Api-Key + Bearer, X-Kodi-Origin-Repo rides along as everywhere.

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
