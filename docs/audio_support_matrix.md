# Audio extraction support matrix — per OS × container × codec

Goal: get a ≤100 MB audio file to the transcription server from the playing
video, **without installing anything** wherever possible. Install hints are
the LAST resort before giving up; the honest dialog is the true last step.

Legend: **VERIFIED** = ran on this exact setup with a real asset grid,
2026-08-29 · **EXPECTED** = same code path as a verified case, mechanism
identical · **UNTESTED** = plausible route, needs a run on real hardware ·
**IMPOSSIBLE** = platform rule forbids it · **—** = falls through to next rung.

Test grid: 60 s assets, every combination built with ffmpeg 8.1:
MKV × {AAC-LC, HE-AAC, AC3, EAC3, MP3, DTS, FLAC, Opus, PCM},
MP4/M4V × {AAC, AC3, ALAC, MP3}, TS × {AAC, AC3}, AVI × {MP3, PCM}.

## The rungs (what the ladder tries, in order)

| # | Rung | Needs | Verified on |
|---|------|-------|-------------|
| 1 | `ffmpeg` transcode → 24k mono AAC | an ffmpeg binary | macOS |
| 2 | `android_ndk` — AMediaExtractor/AMediaCodec via ctypes | nothing (system libs) | real Kodi 21.3, API 31 emulator |
| 3 | `afconvert` — macOS built-in converter | nothing | macOS 15 |
| 4 | `pydemux` — pure-Python track copy (audio_demux.py) | nothing, any OS | macOS (module identical everywhere) |
| 5 | whole-file upload | file ≤ 100 MB | trivial |
| 6 | per-OS install hint → honest give-up | user action | — |

## macOS (no install — the answer to "can we avoid ffmpeg?": mostly YES)

Chain: MP4-family → afconvert direct; anything else → pydemux extracts the
track (correct extension — **afconvert trusts extensions, measured**) →
afconvert converts. All VERIFIED end-to-end through `extract_afconvert()`:

| Container | AAC-LC | HE-AAC | AC3 | EAC3 | MP3 | FLAC | ALAC | DTS | Opus | PCM |
|---|---|---|---|---|---|---|---|---|---|---|
| **MP4/M4V/MOV** (direct) | VERIFIED | VERIFIED | VERIFIED | EXPECTED¹ | FAIL² | n/a³ | VERIFIED | n/a³ | n/a³ | n/a³ |
| **MKV** (via pydemux) | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | n/a³ | **FAIL⁴** | **FAIL⁵** | **FAIL⁵** |
| **TS / AVI** | — | — | — | — | — | — | — | — | — | — |

¹ EAC3-in-MP4 untested as a direct read (raw EAC3 verified); same decoder.
² MP3-in-MP4 rejected by afconvert even though raw MP3 works — quirk, falls
  to rung 4/5. ³ Combination not produced by real releases / not built.
⁴ DTS extracts cleanly (pydemux VERIFIED) but afconvert has **no DTS
  decoder** — falls to whole-file/hint. The one real macOS gap.
⁵ Opus needs Ogg re-encapsulation, PCM a WAV header — neither implemented
  (rare in film releases); falls through. Possible future work.
TS/AVI: pydemux rejects them (VERIFIED) → whole-file ≤100 MB → hint.

## Android (no install — full parity, zero binaries)

`android_audio.py` via `libmediandk.so` ctypes. Emulator = AOSP, which ships
**no Dolby/DTS decoders**, so codec coverage beyond AAC is honest-UNTESTED
until a real box run (real Android TV devices license AC3/EAC3/DTS).

| Path | AAC | HE-AAC | AC3 | EAC3 | DTS | MP3 | FLAC | Opus | PCM |
|---|---|---|---|---|---|---|---|---|---|
| NDK transcode (any container Android reads: MKV/MP4/TS/WebM) | **VERIFIED** (7.9× realtime, decodes clean) | EXPECTED | UNTESTED⁶ | UNTESTED⁶ | UNTESTED⁶ | EXPECTED⁷ | EXPECTED⁷ | EXPECTED⁷ | EXPECTED⁷ |
| NDK demux fallback (AAC only) | VERIFIED (MKV + MP4) | EXPECTED | — | — | — | — | — | — | — |
| pydemux fallback | VERIFIED (same module) | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | — | — |

⁶ Decoder presence is per-device (vendor Dolby/DTS licenses). The engine
  handles "no decoder" with a clean fall-through. **Needs one run on a
  physical Android TV box** — the open Android item.
⁷ MP3/FLAC/Opus/PCM decoders are mandatory AOSP components — same verified
  code path, different `createDecoderByType` argument.
exec() of downloaded ffmpeg: **IMPOSSIBLE on 10+** (verified PermissionError;
Kodi targets SDK 34). Android ≤9 could exec a fetched binary — not needed
now that the NDK route works, so never implemented.

## Windows (no install)

No built-in CLI transcoder exists. Today's no-install coverage = rungs 4+5:

| Route | Status |
|---|---|
| pydemux (MKV/MP4, all listed codecs) | VERIFIED (pure Python, module identical) |
| …then upload the raw track if ≤100 MB | AAC/HE-AAC/MP3 tracks usually fit; AC3/DTS usually don't. Server-side acceptance of raw .ac3/.mp3 uploads: **UNTESTED** (ask API team) |
| **Media Foundation via ctypes** (IMFSourceReader→IMFSinkWriter): MF reads MP4+AAC everywhere, MKV since Win10, AC3 decoder since Win8 | **UNIMPLEMENTED/UNTESTED** — the Windows analog of android_audio.py; genuinely feasible, biggest remaining win |
| install hint `winget install ffmpeg` | last resort, shipped |

## Linux desktop (no install)

| Route | Status |
|---|---|
| ffmpeg often already present | covered by rung 1 probe |
| pydemux + upload | VERIFIED (module) / same server question as Windows |
| **GStreamer `gst-launch-1.0`** — present on most desktop installs (GNOME/KDE pull it); `decodebin ! audioconvert ! avenc_aac` | **UNIMPLEMENTED/UNTESTED** — encoder element availability varies by distro plugin split; worth a probe-and-use rung |
| install hint (`apt install ffmpeg`) | last resort, shipped |

## LibreELEC / CoreELEC

| Route | Status |
|---|---|
| pydemux + upload | VERIFIED (module) |
| ffmpeg binary in the OS image | none on LibreELEC (researched); **CoreELEC some builds ship one — UNTESTED, probe covers it if present** |
| `tools.ffmpeg-tools` add-on (path already probed by rung 1) | softest possible "install": Kodi's own add-on browser — the hint names the exact menu path |

## iOS / tvOS

| Route | Status |
|---|---|
| pydemux + upload | EXPECTED (pure Python; no Kodi-iOS device to verify) |
| **AudioToolbox/ExtAudioFile via ctypes** — the same engine afconvert uses, system framework, dlopen-legal like Android's | **UNIMPLEMENTED/UNTESTED** — would give MP4-family + demuxed-track conversion, the iOS analog of the macOS chain |
| exec of anything | IMPOSSIBLE |

## Honest summary of gaps (ranked by user impact)

1. **Android AC3/EAC3/DTS decode** — engine ready, needs a real-box run.
2. **Windows Media Foundation ctypes engine** — feasible, unbuilt; until
   then Windows-without-ffmpeg only covers AAC/MP3-track sources.
3. **Server acceptance of raw .ac3/.mp3/.flac uploads** — one question to
   the API team; a "yes" widens every no-tool platform at zero client cost.
4. macOS DTS — no system decoder exists; unfixable without install.
5. Opus/PCM-in-MKV re-encapsulation — implementable, rare in the wild.
6. iOS AudioToolbox ctypes engine — feasible, unbuilt, smallest user base.
