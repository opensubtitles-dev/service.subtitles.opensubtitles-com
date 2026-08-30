"""Subtitle synchronization via the subsync service (docs/subtitle_sync_plan.md).

STATUS: LIVE. The alignment engine is the subsync HTTP service (project
subsync, deployed at the URL in the sync_service_url setting). Measured
contract (2026-08-29, all three verified against the live service):

    POST {url}/v1/jobs      multipart audio=<file> subtitle=<file>  -> 202
         {"job_id": "j_...", "status_url": "/v1/jobs/j_..."}
    GET  {url}/v1/jobs/{id} -> {"status": "processing"|"done"|"error",
         "stage": "vad"|"correlate"|..., "progress": 0..1, "error": ...,
         "result": {"transform": {"type", "offset_ms", "scale", "confidence"},
                    "engine_used", "subtitle_url", "warnings": [{code,message}]}}
    GET  {url}{subtitle_url} -> the corrected subtitle file

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


def _service_auth():
    user = (__addon__.getSetting("sync_service_user") or "").strip()
    pw = __addon__.getSetting("sync_service_pass") or ""
    return (user, pw) if user else None


def engine_available():
    """True when a subsync service URL is configured. Kept as a function so
    the callers needed no change on the day the engine landed."""
    return bool(_service_url())


# below this confidence the service itself flags the transform as unreliable
# (measured: wrong-movie subs score ~0.2, correct ones 0.95+)
MIN_CONFIDENCE = 0.6
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

    if progress:
        progress.update(5, "Extracting audio track...")
    audio_path = _extract_audio(video_path, progress)

    if progress:
        progress.update(25, "Uploading to the sync service...")
    ext = os.path.splitext(audio_path)[1] or ".bin"
    with open(audio_path, "rb") as a, open(sub_path, "rb") as s:
        # constant upload names on purpose: the real filenames are viewing
        # history and belong neither in logs nor on the wire
        r = requests.post(url + "/v1/jobs",
                          files={"audio": ("audio" + ext, a),
                                 "subtitle": ("sub" + os.path.splitext(sub_path)[1], s)},
                          auth=auth, timeout=600)
    if r.status_code not in (200, 201, 202):
        log(f"sync job creation failed: HTTP {r.status_code}")
        raise SyncError(f"The sync service refused the job (HTTP {r.status_code}).")
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
        status = state.get("status")
        if status in ("done", "error", "failed"):
            break
        if progress:
            try:
                pct = 25 + int(70 * float(state.get("progress") or 0))
            except (TypeError, ValueError):
                pct = 25
            stage = state.get("stage") or "aligning"
            progress.update(min(pct, 95), f"Synchronizing ({stage})...")
        time.sleep(POLL_SECONDS)
    else:
        raise SyncError("The sync service did not finish in time.")

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
