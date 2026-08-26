"""AI transcription pipeline (EXPERIMENTAL - expert setting, see
docs/ai_transcription_plan.md).

Flow when the user picks the injected "[AI] Transcribe" row in the subtitle
dialog: capability check (cached, one-time benchmark) -> choose the best
source rung (local ffmpeg -> URL handoff -> whole-file upload) -> talk to the
PROPOSED transcription API -> poll the job -> hand back a subtitle file.

API endpoints are PROPOSED per project rules: they follow the contract in
docs/ai_transcription_plan.md and treat 404 as "not deployed yet" with a
friendly dialog. The Development-tab mock setting (test_transcribe_mock,
stripped from release builds) simulates the whole server side so the pipeline
is end-to-end testable in Kodi today.
"""
import json
import os
import subprocess
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib.utilities import log as _log, get_user_agent

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")

API_URL = "https://api.opensubtitles.com/api/v1/"
API_TRANSCRIBE = "ai/transcribe"  # PROPOSED - handle 404 as "not deployed yet"

CAPS_SCHEMA = 1
BENCH_SECONDS_AUDIO = 30       # synthetic audio the encode benchmark processes
BENCH_TIMEOUT = 20             # hard wall for the whole benchmark run
POLL_INTERVAL = 5
POLL_MAX_SECONDS = 15 * 60
UPLOAD_CHUNK = 4 * 1024 * 1024

# Common install locations Kodi's PATH may not include (macOS brew, Linux opt)
FFMPEG_EXTRA_PATHS = ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg",
                      "/usr/bin/ffmpeg", "/opt/bin/ffmpeg")


def log(msg):
    _log(__name__, msg)


def _profile_dir():
    profile = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
    os.makedirs(profile, exist_ok=True)
    return profile


def _caps_path():
    return os.path.join(_profile_dir(), "transcription_caps.json")


def find_ffmpeg():
    try:
        from shutil import which
        found = which("ffmpeg")
        if found:
            return found
    except Exception:
        pass
    for candidate in FFMPEG_EXTRA_PATHS:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _benchmark_ffmpeg(ffmpeg):
    """Encode BENCH_SECONDS_AUDIO s of synthetic audio; return realtime factor.

    A TV box that manages e.g. 8x realtime reencodes a 2h movie's audio in
    ~15 min - viable. Below ~2x the whole-file/URL rungs are the better deal.
    Returns None when the run fails or times out (slow enough to count as
    not viable anyway).
    """
    cmd = [ffmpeg, "-nostdin", "-v", "error",
           "-f", "lavfi", "-i", f"sine=frequency=440:duration={BENCH_SECONDS_AUDIO}",
           "-ac", "1", "-ar", "16000", "-c:a", "aac", "-f", "null", "-"]
    start = time.time()
    try:
        # stdout/stderr=PIPE, not capture_output: that kwarg needs Python 3.7
        # and Kodi Matrix Linux builds run 3.6 (vermin gate enforces the floor)
        out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=BENCH_TIMEOUT)
        elapsed = time.time() - start
        if out.returncode != 0 or elapsed <= 0:
            return None
        return round(BENCH_SECONDS_AUDIO / elapsed, 1)
    except Exception as e:
        log(f"ffmpeg benchmark failed: {e!r}")
        return None


def _benchmark_io():
    """MB/s reading a temp file through xbmcvfs - proxy for the upload rungs."""
    path = os.path.join(_profile_dir(), "bench_io.bin")
    try:
        with open(path, "wb") as f:
            f.write(b"\0" * (8 * 1024 * 1024))
        start = time.time()
        f = xbmcvfs.File(path)
        read = 0
        while True:
            chunk = f.readBytes(1024 * 1024)
            if not chunk:
                break
            read += len(chunk)
        f.close()
        elapsed = max(time.time() - start, 0.001)
        return round(read / (1024 * 1024) / elapsed, 1)
    except Exception as e:
        log(f"io benchmark failed: {e!r}")
        return None
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def get_capabilities():
    """Detected capabilities + one-time benchmark, cached forever in the profile.

    Cache invalidates only when the schema number changes or the cached ffmpeg
    binary disappeared (uninstall) - "test capabilities first, save locally,
    never run again".
    """
    path = _caps_path()
    try:
        with open(path) as f:
            caps = json.load(f)
        if caps.get("schema") == CAPS_SCHEMA:
            if not caps.get("ffmpeg") or os.path.exists(caps["ffmpeg"]):
                return caps
    except Exception:
        pass

    log("Probing transcription capabilities (one-time)")
    ffmpeg = find_ffmpeg()
    caps = {
        "schema": CAPS_SCHEMA,
        "probed_at": int(time.time()),
        "is_android": bool(xbmc.getCondVisibility("System.Platform.Android")),
        "ffmpeg": ffmpeg or "",
        "encode_x_realtime": _benchmark_ffmpeg(ffmpeg) if ffmpeg else None,
        "io_mb_per_s": _benchmark_io(),
    }
    try:
        with open(path, "w") as f:
            json.dump(caps, f, indent=2, sort_keys=True)
    except Exception as e:
        log(f"caps cache write failed: {e!r}")
    log(f"capabilities: {caps}")
    return caps


def choose_source(caps, file_path):
    """Pick the best rung for this playback. Returns 'ffmpeg' | 'url' | 'upload'."""
    if caps.get("ffmpeg") and (caps.get("encode_x_realtime") or 0) >= 2 \
            and os.path.exists(file_path):
        return "ffmpeg"
    if file_path.startswith(("http://", "https://")):
        return "url"
    return "upload"


def extract_audio(ffmpeg, file_path, progress=None):
    """Reencode the audio track to mono 16kHz AAC; returns the temp file path."""
    out_path = os.path.join(_profile_dir(), "transcribe_audio.m4a")
    try:
        os.unlink(out_path)
    except Exception:
        pass
    cmd = [ffmpeg, "-nostdin", "-v", "error", "-i", file_path,
           "-vn", "-sn", "-ac", "1", "-ar", "16000", "-c:a", "aac", "-b:a", "48k",
           "-movflags", "+faststart", out_path]
    log(f"extracting audio: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    while proc.poll() is None:
        if progress and progress.iscanceled():
            proc.kill()
            raise UserCancelled()
        time.sleep(0.5)
    if proc.returncode != 0 or not os.path.exists(out_path):
        err = (proc.stderr.read() or b"").decode(errors="replace")[:200]
        raise TranscriptionError(f"ffmpeg audio extraction failed: {err}")
    return out_path


class TranscriptionError(Exception):
    pass


class NotDeployed(TranscriptionError):
    pass


class UserCancelled(TranscriptionError):
    pass


class TranscriptionClient:
    """PROPOSED /ai/transcribe endpoints (docs/ai_transcription_plan.md par.4)."""

    def __init__(self, session, token):
        self.session = session
        self.headers = {"Authorization": "Bearer " + token,
                        "User-Agent": get_user_agent()}

    def _check(self, r):
        if r.status_code == 404:
            raise NotDeployed("transcription API not deployed")
        r.raise_for_status()
        return r.json()

    def create_job(self, meta):
        r = self.session.post(API_URL + API_TRANSCRIBE, json=meta,
                              headers=self.headers, timeout=30)
        if r.status_code == 409:            # cache hit - subtitle already exists
            return {"cache_hit": True, **r.json()}
        return self._check(r)

    def upload_audio(self, job_id, path, progress=None):
        size = os.path.getsize(path)
        sent = 0
        with open(path, "rb") as f:
            while True:
                chunk = f.read(UPLOAD_CHUNK)
                if not chunk:
                    break
                r = self.session.put(
                    f"{API_URL}{API_TRANSCRIBE}/{job_id}/audio",
                    data=chunk, headers={**self.headers,
                                         "Content-Range": f"bytes {sent}-{sent + len(chunk) - 1}/{size}"},
                    timeout=120)
                self._check(r)
                sent += len(chunk)
                if progress:
                    if progress.iscanceled():
                        raise UserCancelled()
                    progress.update(min(99, int(sent * 100 / size)),
                                    f"Uploading audio... {sent // (1024 * 1024)} / {size // (1024 * 1024)} MB")

    def poll(self, job_id):
        r = self.session.get(f"{API_URL}{API_TRANSCRIBE}/{job_id}",
                             headers=self.headers, timeout=30)
        return self._check(r)


class MockTranscriptionClient:
    """Development-tab stand-in: no network, finishes after a few polls and
    yields a placeholder subtitle so the whole pipeline is testable in Kodi."""

    def __init__(self, *_args, **_kwargs):
        self._polls = 0

    def create_job(self, meta):
        log(f"MOCK transcription job for {meta}")
        return {"job_id": "mock-1", "credits_charged": 0}

    def upload_audio(self, job_id, path, progress=None):
        size = os.path.getsize(path)
        log(f"MOCK upload of {size} bytes skipped")
        if progress:
            progress.update(99, "Mock upload complete")

    def poll(self, job_id):
        self._polls += 1
        if self._polls < 3:
            return {"status": "processing"}
        srt = ("1\n00:00:01,000 --> 00:00:05,000\n"
               "[OpenSubtitles AI transcription - mock pipeline result]\n")
        out = os.path.join(_profile_dir(), "mock_transcription.srt")
        with open(out, "w") as f:
            f.write(srt)
        return {"status": "done", "subtitle_path": out}


def run_transcription(session, token, file_data, language, mock=False):
    """The whole pipeline. Returns a local subtitle file path, or None.

    Raises NotDeployed when the real API is not live yet; shows its own
    progress dialog (cancel supported everywhere).
    """
    caps = get_capabilities()
    file_path = file_data.get("file_original_path", "")
    source = choose_source(caps, file_path)
    log(f"transcription source rung: {source} (caps: encode_x={caps.get('encode_x_realtime')}, io={caps.get('io_mb_per_s')})")

    client = MockTranscriptionClient() if mock else TranscriptionClient(session, token)
    progress = xbmcgui.DialogProgress()
    progress.create("OpenSubtitles AI transcription", "Preparing...")
    try:
        meta = {
            "moviehash": file_data.get("moviehash", ""),
            "file_size": file_data.get("file_size", 0),
            "language_hint": language,
            "source": {"type": "url" if source == "url" else "upload",
                       "url": file_path if source == "url" else None},
            "credits_ack": True,
        }
        job = client.create_job(meta)
        if job.get("cache_hit"):
            log(f"transcription cache hit: {job}")
            return job.get("subtitle_path")

        if source == "ffmpeg":
            progress.update(5, "Extracting audio track...")
            audio = extract_audio(caps["ffmpeg"], file_path, progress)
            client.upload_audio(job["job_id"], audio, progress)
            try:
                os.unlink(audio)
            except Exception:
                pass
        elif source == "upload":
            progress.update(5, "Uploading media file...")
            client.upload_audio(job["job_id"], file_path, progress)
        # source == "url": nothing to send, the server fetches it

        start = time.time()
        while time.time() - start < POLL_MAX_SECONDS:
            if progress.iscanceled():
                raise UserCancelled()
            state = client.poll(job["job_id"])
            if state.get("status") == "done":
                return state.get("subtitle_path") or state.get("subtitle_id")
            if state.get("status") == "failed":
                raise TranscriptionError(state.get("error") or "transcription failed")
            progress.update(99, "Transcribing on the server...")
            for _ in range(POLL_INTERVAL * 2):
                if progress.iscanceled():
                    raise UserCancelled()
                time.sleep(0.5)
        raise TranscriptionError("timed out waiting for the transcription job")
    finally:
        progress.close()
