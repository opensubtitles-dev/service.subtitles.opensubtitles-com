# Low-bitrate audio for transcription — platform availability matrix

Question: how does the add-on get a small audio file (the server accepts one
multipart file, max 100 MB) out of the playing video, on every Kodi platform?
Measured 2026-08-29 (macOS, ffmpeg 8.1, 10-minute assets, sizes extrapolated
linearly to a 2-hour film). Companion to `ai_transcription_plan.md`.

## Measurements — what strategy wins

Source: MKV with AC3 5.1 @ 448 kbps (the common TV-rip case):

| Strategy | 10-min time | 2h size | Verdict |
|---|---|---|---|
| demux only (`-c:a copy`) | 0.16 s | **385 MB** | over cap — demux alone is NOT enough |
| AAC 48k mono 16 kHz | 1.3 s | 42 MB | fine, previous default |
| **AAC 24k mono 16 kHz** | 1.2 s | **21 MB** | **new default** — universal encoder, 4× faster than opus |
| Opus 16k mono voip | 4.7 s | 11 MB | smallest, but libopus missing from some minimal ffmpeg builds |
| MP3 32k mono | 1.1 s | 28 MB | fallback if AAC encoder absent (never seen) |

Source: MP4 with AAC stereo @ 128 kbps (the common web-rip case):

| Strategy | 10-min time | 2h size |
|---|---|---|
| demux only | 0.09 s | 111 MB — just OVER the cap at 128k; HE-AAC 32–64k sources fit easily |
| reencode 24k mono | ~1.2 s | 21 MB |

Conclusions:
- **Reencode is the general answer** (any source codec → 21 MB, ~15 s of CPU
  per 2h film on a laptop; slower boxes covered by the existing benchmark
  gate `encode_x_realtime >= 2`).
- **Demux-only is a real rung** for low-bitrate AAC sources (≤ ~110 kbps for
  2h) — and it needs no decoder, which matters exactly where ffmpeg is
  unavailable (below).

## Platform matrix

| Platform | ffmpeg CLI | Route | Notes |
|---|---|---|---|
| **Linux desktop** | usually installed / 1 pkg away | reencode rung | `/usr/bin/ffmpeg` probed |
| **macOS** | NOT system; brew common | reencode rung after `brew install ffmpeg` | `/opt/homebrew/bin`, `/usr/local/bin` probed. `afconvert` is built-in but cannot demux MKV — useless here |
| **Windows** | NOT system; `winget install ffmpeg` | reencode rung | probed via PATH; capability dialog should show the one-line install command per OS |
| **LibreELEC / CoreELEC** | via the official **`tools.ffmpeg-tools`** add-on | reencode rung | binary at `/storage/.kodi/addons/tools.ffmpeg-tools/bin/ffmpeg` (now in `FFMPEG_EXTRA_PATHS`); some builds symlink `/usr/bin/ffmpeg`. UX: offer "install ffmpeg-tools from the LibreELEC repo" instead of a generic failure |
| **Android ≤ 9** | can `exec()` a downloaded static binary from the add-on profile | reencode rung after one-time binary fetch | large share of TV boxes still run 7–9; the probe suite's exec test is the gate |
| **Android 10+** | **blocked**: Kodi Omega targets SDK 34 (`TARGET_SDK 34`, minSdk 21 in xbmc source), so W^X denies both `exec()` and `dlopen()` of anything downloaded; only APK-bundled libs are executable and we cannot add to Kodi's APK | fallback ladder below | this kills the "download ffmpeg" and the ctypes-libffmpeg routes on modern Android |
| **iOS / tvOS** | never | fallback ladder below | no exec, no sideloaded binaries |

## Fallback ladder for exec-less platforms (Android 10+, iOS/tvOS)

1. **Whole-file upload** when the video itself is ≤ 100 MB (episodes, low-res).
2. **Pure-Python audio demux** — extract the AAC track without decoding and
   wrap it in ADTS. **Spike proven** (`scripts/spike_pydemux_mp4.py`): MP4
   `moov` parsing (stsd/esds/stsz/stsc/stco), 10 min extracted in **0.8 s**
   stdlib-only, output decodes clean. Fits the cap whenever the audio track
   is ≤ ~110 kbps for 2h (HE-AAC web sources typically 32–64k). MKV needs an
   EBML block reader — same principle, follow-up spike.
3. Not available — honest dialog. (A future server-side URL/chunked mode
   would close this; out of scope for the current API contract.)

## What changed in code (this round)

- `FFMPEG_EXTRA_PATHS` += the LibreELEC/CoreELEC ffmpeg-tools location.
- Extraction target dropped 48k → **24k mono AAC** (half the upload, same
  ASR-grade signal at 16 kHz mono, encoder universal).
- Spike stored at `scripts/spike_pydemux_mp4.py` (dev tooling, not shipped);
  promote into `resources/lib/` once the Android probe verdict confirms the
  exec()-blocked population needs it.

## Open items

- MKV pure-Python demux spike (EBML SimpleBlock reader → ADTS).
- Android probe run on a real box: exec test + `tools.ffmpeg-tools`-style
  path availability (`adb logcat -d | grep TRANSCRIPTION-PROBE-RESULT`).
- Capability dialog per-OS install hints (brew/winget/ffmpeg-tools add-on).
