"""Subtitle synchronization via the subsync service (docs/subtitle_sync_plan.md).

STATUS: LIVE. The alignment engine is the subsync HTTP service, production
at https://sync.opensubtitles.com (default of the sync_service_url setting;
discovery: /llms.txt, /v1/meta, /v1/openapi.json). Anonymous access works
with per-IP limits; a Bearer key raises them (auth optional). Measured
contract (2026-08-29/30, all verified against the live service):

    POST {url}/v1/jobs      multipart audio=<file> subtitle=<file>  -> 202
         {"job_id": "j_...", "status_url": "/v1/jobs/j_..."}
    GET  {url}/v1/jobs/{id} -> {"status": "processing"|"done"|"error",
         "stage": "vad"|"correlate"|..., "progress": 0..1, "error": ...,
         "result": {"transform": {"type", "offset_ms", "scale", "confidence"},
                    "engine_used", "subtitle_url", "warnings": [{code,message}]}}
    GET  {url}{subtitle_url} -> the corrected subtitle file

    Plus the moviehash ladder (measured on production): GET
    /v1/fingerprints/{osdb-moviehash} -> {"known": bool}; when known, a job
    with moviehash + subtitle alone syncs in 0.6 s with ZERO media
    processing; attaching moviehash to fingerprint/audio jobs makes the
    server remember the release for everyone. 422 moviehash_unknown on a
    cache race falls through to the next rung. Errors arrive as
    {"error": {"code", "message"}}; 429 carries Retry-After.

    Verified: real sub +130ms conf 0.99; +5s-shifted sub -> -4870ms conf
    0.99; wrong-movie sub -> conf 0.19 + different_cut_suspected (honest
    rejection). Audio accepted as opus AND mp3 - the whole transcriber
    extraction ladder feeds it.

No player state, no dialogs - the callers (subtitle dialog row, background
service nudge offer) own all UI; a progress dialog may be passed in.
"""

import os
import subprocess
import time
import uuid

import xbmcaddon
import xbmcvfs

from resources.lib.utilities import log as _log

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")


def log(msg):
    _log(__name__, msg)


class SyncError(Exception):
    """A synchronization attempt failed in a way worth telling the user."""


class EngineNotAvailable(SyncError):
    """The alignment engine is not bundled yet (project subsync pending)."""


def is_enabled():
    """The expert toggle gating BOTH invocation paths (row + nudge offer)."""
    val = __addon__.getSetting("subtitle_sync_enabled")
    return bool(val) and val.lower() in ("true", "1")


def _service_url():
    return (__addon__.getSetting("sync_service_url") or "").strip().rstrip("/")


def _read_env_auth(env_path):
    """(user, pass) from a KEY=VALUE file, or None. Never logged anywhere."""
    try:
        vals = {}
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
        if vals.get("SUBSYNC_USER"):
            return (vals["SUBSYNC_USER"], vals.get("SUBSYNC_PASS", ""))
    except Exception:
        pass
    return None


def _service_auth():
    """Settings first; else the gitignored .env at the addon root (dev-box
    convenience while the service runs behind Basic auth - the real auth
    scheme replaces this whole function later)."""
    user = (__addon__.getSetting("sync_service_user") or "").strip()
    if user:
        return (user, __addon__.getSetting("sync_service_pass") or "")
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return _read_env_auth(os.path.join(root, ".env"))


def engine_available():
    """True when a subsync service URL is configured. Kept as a function so
    the callers needed no change on the day the engine landed."""
    return bool(_service_url())


# below this confidence the service itself flags the transform as unreliable
# (measured: wrong-movie subs score ~0.2, correct ones 0.95+)
MIN_CONFIDENCE = 0.6
# fingerprint fast path keeps a result only above this; below it we redo the
# job with real audio so the server's silero VAD replaces our energy mask
FP_MIN_CONFIDENCE = 0.75
POLL_SECONDS = 2
POLL_TIMEOUT = 600


def _profile_dir():
    path = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
    os.makedirs(path, exist_ok=True)
    return path


def _extract_audio(video_path, progress=None):
    """Audio for the sync job, smallest first: ffmpeg -> 16 kHz mono opus
    (~4 MB / 20 min, the service's preferred diet), else the transcriber
    ladder (NDK/afconvert/GStreamer/MF/pydemux - service accepts mp3/aac
    too, measured), else the video itself when small enough."""
    from resources.lib import transcriber
    caps = transcriber.get_capabilities()
    if caps.get("ffmpeg"):
        out = os.path.join(_profile_dir(), "sync_audio.ogg")
        try:
            os.unlink(out)
        except Exception:
            pass
        cmd = [caps["ffmpeg"], "-nostdin", "-v", "error", "-i", video_path,
               "-map", "0:a:0", "-vn", "-sn", "-ac", "1", "-ar", "16000",
               "-c:a", "libopus", "-b:a", "24k", out]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while proc.poll() is None:
            if progress and progress.iscanceled():
                proc.kill()
                raise UserCancelled()
            time.sleep(0.5)
        if proc.returncode == 0 and os.path.exists(out):
            return out
        log(f"ffmpeg opus extraction failed (exit {proc.returncode}) - trying the ladder")
    source = transcriber.choose_source(caps, video_path)
    try:
        if source == "android_ndk":
            return transcriber.extract_android(video_path, progress)
        if source == "afconvert":
            return transcriber.extract_afconvert(video_path, progress)
        if source == "gstreamer":
            return transcriber.extract_gstreamer(video_path, progress)
        if source == "pydemux":
            return transcriber.extract_pydemux(video_path)
    except Exception as e:
        log(f"audio extraction rung {source} failed ({type(e).__name__})")
    try:
        if os.path.getsize(video_path) <= transcriber.MAX_UPLOAD_BYTES:
            return video_path       # service accepts video files, discouraged
    except Exception:
        pass
    raise SyncError("No way to extract the audio track on this platform.\n"
                    + transcriber.ffmpeg_install_hint())


class UserCancelled(SyncError):
    """The user cancelled from the progress dialog."""


# --------------------------------------------------------------------------
# Energy-mask fingerprint fast path (SPEC.md §2 of the subsync project).
#
# The server's fingerprint tier skips its VAD entirely and correlates a
# client-supplied 10 ms speech mask in ~1 s. A real silero mask needs an ONNX
# runtime Kodi doesn't have - but MEASURED 2026-08-29: a plain loudness mask
# (per-frame energy, 60th-percentile threshold) synced the reference film at
# confidence 0.99 / +90 ms vs silero's +130 ms, total round-trip ~4 s against
# ~35 s for the audio tier. Music-heavy tracks can defeat loudness (that is
# why the server's own VAD stays as fallback below FP_MIN_CONFIDENCE).
# Sparse windows + energy were measured too and FAIL (conf 0.25) - windowed
# loudness has too little signal; do not resurrect that combination.
# --------------------------------------------------------------------------

_FP_FRAME = 160          # samples per 10 ms frame at 16 kHz


def _frame_energies(ffmpeg, video_path, progress=None):
    """Stream-decode the first audio track to 16 kHz mono s16le and return
    per-10ms-frame mean-abs energies. audioop when the interpreter still has
    it (Kodi's 3.11/3.12), pure array fallback otherwise (3.13+)."""
    try:
        import audioop
    except ImportError:
        audioop = None
    import array as _array
    cmd = [ffmpeg, "-nostdin", "-v", "error", "-i", video_path,
           "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    energies = []
    leftover = b""
    frame_bytes = _FP_FRAME * 2
    try:
        while True:
            if progress and progress.iscanceled():
                proc.kill()
                raise UserCancelled()
            chunk = proc.stdout.read(1 << 18)
            if not chunk:
                break
            buf = leftover + chunk
            usable = len(buf) - len(buf) % frame_bytes
            leftover = buf[usable:]
            if audioop is not None:
                for off in range(0, usable, frame_bytes):
                    energies.append(audioop.rms(buf[off:off + frame_bytes], 2))
            else:
                arr = _array.array("h")
                arr.frombytes(buf[:usable])
                for off in range(0, len(arr), _FP_FRAME):
                    acc = 0
                    for v in arr[off:off + _FP_FRAME]:
                        acc += v if v >= 0 else -v
                    energies.append(acc // _FP_FRAME)
    finally:
        try:
            proc.stdout.close()
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
    return energies


def _energy_fingerprint(ffmpeg, video_path, progress=None):
    """Fingerprint JSON (SPEC §2.1/2.2) from a loudness mask, or None when
    the track cannot be decoded / is degenerate."""
    import base64
    import json as _json
    try:
        energies = _frame_energies(ffmpeg, video_path, progress)
    except UserCancelled:
        raise
    except Exception as e:
        log(f"energy decode failed ({type(e).__name__})")
        return None
    n = len(energies)
    if n < 6000:               # SPEC floor: at least 1 minute of media
        return None
    threshold = sorted(energies)[int(n * 0.60)]
    mask = bytearray((n + 7) // 8)
    speech = 0
    for i, e in enumerate(energies):
        if e > threshold:
            mask[i >> 3] |= 1 << (7 - (i & 7))
            speech += 1
    ratio = speech / n
    if not 0.005 <= ratio <= 0.95:      # SPEC: degenerate mask is unusable
        return None
    return _json.dumps({"v": 1, "frame_ms": 10, "duration_ms": n * 10,
                        "vad": "energy-1", "sample_rate": 16000,
                        "threshold": 0.5,
                        "mask_b64": base64.b64encode(bytes(mask)).decode()})


def sync_subtitle(sub_path, video_path=None, session=None, progress=None):
    """Synchronize the subtitle at `sub_path` against its video via the
    subsync service.

      - the corrected subtitle is written to a NEW file (never in place -
        the original stays untouched for a retry) and its path returned
      - returns {"path": <corrected file>, "offset_ms": <int>,
                 "fps_scale": <float>, "method": <engine name>,
                 "confidence": <float>}
      - raises SyncError with a user-presentable, viewing-history-free
        message on failure; EngineNotAvailable when no service configured
      - honors progress.iscanceled() when a progress dialog is passed
      - NEVER touches a moviehash_match subtitle (caller enforces too)
    """
    import requests

    url = _service_url()
    if not url:
        log("sync requested but no service URL configured")
        raise EngineNotAvailable()
    if not sub_path or not os.path.exists(sub_path):
        raise SyncError("The active subtitle file could not be located.")
    if not video_path or not os.path.exists(video_path):
        raise SyncError("The video file could not be located "
                        "(network sources are not supported yet).")
    auth = _service_auth()

    # constant upload names on purpose throughout: the real filenames are
    # viewing history and belong neither in logs nor on the wire
    sub_ext = os.path.splitext(sub_path)[1] or ".srt"

    def _server_error(r):
        """The service's stable error shape: {"error": {"code", "message"}}."""
        try:
            err = (r.json() or {}).get("error") or {}
            return str(err.get("code") or ""), str(err.get("message") or "")
        except Exception:
            return "", ""

    def _run_job(files, data=None):
        r = requests.post(url + "/v1/jobs", files=files, data=data or {},
                          auth=auth, timeout=600)
        if r.status_code == 429:
            retry = r.headers.get("Retry-After", "a few")
            raise SyncError(f"The sync service is rate-limiting this device - "
                            f"try again in {retry} seconds.")
        if r.status_code not in (200, 201, 202):
            code, message = _server_error(r)
            log(f"sync job creation failed: HTTP {r.status_code} {code}")
            raise SyncError(message or
                            f"The sync service refused the job (HTTP {r.status_code}).")
        job_id = (r.json() or {}).get("job_id")
        if not job_id:
            raise SyncError("The sync service answered without a job id.")
        deadline = time.time() + POLL_TIMEOUT
        state = {}
        while time.time() < deadline:
            if progress and progress.iscanceled():
                raise UserCancelled()
            pr = requests.get(f"{url}/v1/jobs/{job_id}", auth=auth, timeout=30)
            state = pr.json() if pr.status_code == 200 else {}
            if state.get("status") in ("done", "error", "failed"):
                return state
            if progress:
                try:
                    pct = 25 + int(70 * float(state.get("progress") or 0))
                except (TypeError, ValueError):
                    pct = 25
                stage = state.get("stage") or "aligning"
                progress.update(min(pct, 95), f"Synchronizing ({stage})...")
            time.sleep(POLL_SECONDS)
        raise SyncError("The sync service did not finish in time.")

    # moviehash: attached to every job so the server caches the fingerprint
    # per release - the second sync of the same file (any user, any subtitle)
    # takes the instant path below
    moviehash = ""
    try:
        from resources.lib.file_operations import hash_file
        _size, moviehash = hash_file(video_path, video_path.endswith(".rar"))
    except Exception:
        moviehash = ""

    # INSTANT PATH (measured 0.6 s end-to-end): the server already holds a
    # speech fingerprint for this exact release - job needs moviehash +
    # subtitle only, nothing is scanned or uploaded
    state = None
    if moviehash:
        try:
            kr = requests.get(f"{url}/v1/fingerprints/{moviehash}",
                              auth=auth, timeout=15)
            known = kr.status_code == 200 and (kr.json() or {}).get("known")
        except Exception:
            known = False
        if known:
            if progress:
                progress.update(10, "File already known - synchronizing...")
            try:
                with open(sub_path, "rb") as s:
                    state = _run_job({"subtitle": ("sub" + sub_ext, s)},
                                     data={"moviehash": moviehash})
            except SyncError:
                # e.g. 422 moviehash_unknown on a cache race - fall through
                state = None

    # FAST PATH (measured ~4 s round trip): loudness fingerprint, no server
    # VAD. Kept only above FP_MIN_CONFIDENCE - music-heavy tracks defeat a
    # loudness mask, and then the audio tier below redoes the job properly.
    from resources.lib import transcriber
    ffmpeg = transcriber.get_capabilities().get("ffmpeg")
    if state is None and ffmpeg:
        if progress:
            progress.update(5, "Fingerprinting audio...")
        fp = _energy_fingerprint(ffmpeg, video_path, progress)
        if fp:
            with open(sub_path, "rb") as s:
                fp_state = _run_job({"subtitle": ("sub" + sub_ext, s),
                                     "fingerprint": ("fp.json", fp, "application/json")},
                                    data={"moviehash": moviehash} if moviehash else None)
            fp_result = (fp_state.get("result") or {}) if fp_state.get("status") == "done" else {}
            fp_transform = fp_result.get("transform") or {}
            try:
                fp_conf = float(fp_transform.get("confidence") or 0)
            except (TypeError, ValueError):
                fp_conf = 0.0
            if fp_conf >= FP_MIN_CONFIDENCE:
                state = fp_state
            else:
                log(f"fingerprint fast path inconclusive (confidence {fp_conf:.2f}) "
                    "- retrying with real audio")

    if state is None:
        if progress:
            progress.update(5, "Extracting audio track...")
        audio_path = _extract_audio(video_path, progress)
        if progress:
            progress.update(25, "Uploading to the sync service...")
        ext = os.path.splitext(audio_path)[1] or ".bin"
        with open(audio_path, "rb") as a, open(sub_path, "rb") as s:
            state = _run_job({"audio": ("audio" + ext, a),
                              "subtitle": ("sub" + sub_ext, s)},
                             data={"moviehash": moviehash} if moviehash else None)

    if state.get("status") != "done":
        raise SyncError(f"Synchronization failed on the server: "
                        f"{str(state.get('error'))[:120]}")
    result = state.get("result") or {}
    transform = result.get("transform") or {}
    try:
        confidence = float(transform.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence < MIN_CONFIDENCE:
        codes = ", ".join(w.get("code", "") for w in (result.get("warnings") or []))
        log(f"sync rejected: confidence {confidence:.2f} ({codes})")
        raise SyncError(
            f"The engine is not confident this subtitle matches the video "
            f"(confidence {confidence:.0%}). It may be made for a different "
            f"cut or a different film - no changes were applied.")

    sr = requests.get(url + result.get("subtitle_url", ""), auth=auth, timeout=60)
    if sr.status_code != 200 or not sr.content:
        raise SyncError("The corrected subtitle could not be fetched.")
    out_path = os.path.join(
        _profile_dir(), f"synced.{uuid.uuid4().hex[:8]}"
                        f"{os.path.splitext(sub_path)[1] or '.srt'}")
    with open(out_path, "wb") as f:
        f.write(sr.content)
    log(f"sync done: {transform.get('type')} offset={transform.get('offset_ms')}ms "
        f"scale={transform.get('scale')} confidence={confidence:.2f} "
        f"engine={result.get('engine_used')}")
    try:
        offset_ms = int(transform.get("offset_ms") or 0)
        fps_scale = float(transform.get("scale") or 1.0)
    except (TypeError, ValueError):
        offset_ms, fps_scale = 0, 1.0
    return {"path": out_path,
            "offset_ms": offset_ms,
            "fps_scale": fps_scale,
            "method": str(result.get("engine_used") or "audio"),
            "confidence": confidence}


# ---------------------------------------------------------------------------
# Delay-nudge detection (used by the background service).
#
# The moment a user SEES bad sync they open Kodi's own subtitle-offset dialog
# and start nudging Player.SubtitleDelay. More than NUDGE_THRESHOLD distinct
# values in one session means "struggling, not fine-tuning" - the one moment
# an automatic-sync offer is welcome instead of annoying.
# ---------------------------------------------------------------------------

NUDGE_THRESHOLD = 2


def register_delay_sample(session, delay):
    """Feeds one sampled Player.SubtitleDelay value into the session.

    Returns True exactly ONCE per session: at the moment the nudge count
    crosses the threshold and the sync offer should be made. The caller
    decides whether the offer is allowed at all (toggle, moviehash, engine).
    """
    if not isinstance(session, dict):
        return False
    delay = str(delay or "").strip()
    if not delay:
        return False
    seen = session.setdefault("_delay_values", [])
    if delay in seen:
        return False
    seen.append(delay)
    # first value is the baseline (usually "0.000 s"), not a nudge
    nudges = len(seen) - 1
    if nudges > NUDGE_THRESHOLD and not session.get("_sync_offered"):
        session["_sync_offered"] = True
        return True
    return False
