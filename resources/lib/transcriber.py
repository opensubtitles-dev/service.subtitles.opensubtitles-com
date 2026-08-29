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

from resources.lib.utilities import log as _log, get_user_agent, safe_media_filename

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")

API_URL = "https://api.opensubtitles.com/api/v1/"
# Spec-verified against docs/opensubtitles_api_reference.html:
#   GET  /ai/info/transcription            Api-Key          - APIs + languages + price
#   POST /ai/transcribe                    Api-Key + Bearer - multipart: api, language, file
#                                          max file size 100 MB; -> {status: CREATED, correlation_id}
#   GET  /ai/transcribe/{correlation_id}   Api-Key + Bearer - CREATED|PENDING|COMPLETED|ERROR|TIMEOUT
API_TRANSCRIBE = "ai/transcribe"
API_TRANSCRIBE_INFO = "ai/info/transcription"
MAX_UPLOAD_BYTES = 100 * 1024 * 1024   # hard server-side cap per the spec

CAPS_SCHEMA = 1
BENCH_SECONDS_AUDIO = 30       # synthetic audio the encode benchmark processes
BENCH_TIMEOUT = 20             # hard wall for the whole benchmark run
POLL_INTERVAL = 5
POLL_MAX_SECONDS = 15 * 60
UPLOAD_CHUNK = 4 * 1024 * 1024

# Common install locations Kodi's PATH may not include (macOS brew, Linux
# opt, and the LibreELEC/CoreELEC ffmpeg-tools add-on - the sanctioned way to
# get an ffmpeg CLI on those systems; docs/audio_extraction_matrix.md)
FFMPEG_EXTRA_PATHS = ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg",
                      "/usr/bin/ffmpeg", "/opt/bin/ffmpeg",
                      "/storage/.kodi/addons/tools.ffmpeg-tools/bin/ffmpeg")


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
        log(f"ffmpeg benchmark failed: {type(e).__name__}")
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
        log(f"io benchmark failed: {type(e).__name__}")
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
        log(f"caps cache write failed: {type(e).__name__}")
    log(f"capabilities: {caps}")
    return caps


def choose_source(caps, file_path):
    """Pick the rung for this playback: 'ffmpeg' | 'upload' | 'too_big'.

    The real API accepts one multipart file of max 100 MB - no URL mode - so
    for anything larger the local ffmpeg audio extraction is not an
    optimization, it is the only way in (2h of 48k mono AAC ~= 42 MB, fits).
    """
    local = os.path.exists(file_path)
    if caps.get("ffmpeg") and (caps.get("encode_x_realtime") or 0) >= 2 and local:
        return "ffmpeg"
    if local and os.path.getsize(file_path) <= MAX_UPLOAD_BYTES:
        return "upload"
    return "too_big"


def extract_audio(ffmpeg, file_path, progress=None):
    """Reencode the audio track to mono 16kHz AAC; returns the temp file path."""
    out_path = os.path.join(_profile_dir(), "transcribe_audio.m4a")
    try:
        os.unlink(out_path)
    except Exception:
        pass
    # 24k mono AAC: measured 21 MB for a 2h film (docs/audio_extraction_matrix.md)
    # - half the upload of 48k with no ASR quality loss at 16 kHz mono. AAC over
    # opus because every ffmpeg build carries the encoder.
    cmd = [ffmpeg, "-nostdin", "-v", "error", "-i", file_path,
           "-vn", "-sn", "-ac", "1", "-ar", "16000", "-c:a", "aac", "-b:a", "24k",
           "-movflags", "+faststart", out_path]
    log("extracting audio track (mono 16kHz AAC)")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    while proc.poll() is None:
        if progress and progress.iscanceled():
            proc.kill()
            raise UserCancelled()
        time.sleep(0.5)
    if proc.returncode != 0 or not os.path.exists(out_path):
        err = (proc.stderr.read() or b"").decode(errors="replace")
        # ffmpeg error text embeds the input path (viewing history) - scrub it
        err = err.replace(file_path, "<video>").replace(out_path, "<audio>")[:200]
        raise TranscriptionError(f"ffmpeg audio extraction failed (exit {proc.returncode}): {err}")
    return out_path


class TranscriptionError(Exception):
    pass


class NotDeployed(TranscriptionError):
    pass


class UserCancelled(TranscriptionError):
    pass


class TranscriptionClient:
    """Spec-verified /ai/transcribe client (docs/opensubtitles_api_reference.html)."""

    def __init__(self, session, token):
        self.session = session
        self.headers = {"Authorization": "Bearer " + token,
                        "User-Agent": get_user_agent()}

    def _check(self, r):
        if r.status_code == 404:
            raise NotDeployed("transcription API not available on this server")
        r.raise_for_status()
        body = r.json()
        # valid JSON is not necessarily an object - callers .get() the result
        if not isinstance(body, dict):
            raise TranscriptionError("unexpected non-object response from the transcription API")
        return body

    def list_apis(self):
        """GET /ai/info/transcription - engines, languages and per-second price."""
        r = self.session.get(API_URL + API_TRANSCRIBE_INFO,
                             headers={"User-Agent": get_user_agent()}, timeout=30)
        return self._check(r).get("data") or []

    def create_job(self, api_name, language, media_path, progress=None):
        """POST /ai/transcribe - one multipart file (server cap 100 MB).

        Returns {"status": "CREATED", "correlation_id": ...}.
        """
        size = os.path.getsize(media_path)
        if size > MAX_UPLOAD_BYTES:
            raise TranscriptionError(
                f"file is {size // (1024 * 1024)} MB - the server accepts at most 100 MB")
        if progress:
            progress.update(20, f"Uploading {size // (1024 * 1024)} MB to the transcription service...")
        with open(media_path, "rb") as f:
            r = self.session.post(
                API_URL + API_TRANSCRIBE,
                params={"api": api_name, "language": language},
                files={"file": (safe_media_filename(media_path), f)},
                headers=self.headers, timeout=600)
        return self._check(r)

    def poll(self, correlation_id):
        """GET /ai/transcribe/{correlation_id} - CREATED|PENDING|COMPLETED|ERROR|TIMEOUT."""
        r = self.session.get(f"{API_URL}{API_TRANSCRIBE}/{correlation_id}",
                             headers=self.headers, timeout=30)
        return self._check(r)


class MockTranscriptionClient:
    """Development-tab stand-in: no network, real response shapes, finishes
    after a few polls with a placeholder subtitle - the whole pipeline is
    testable in Kodi today."""

    def __init__(self, *_args, **_kwargs):
        self._polls = 0

    def list_apis(self):
        return [{"name": "mock", "display_name": "Mock Transcribe", "price": 0.0,
                 "languages_supported": [{"language_code": "auto",
                                          "language_name": "automatic selection"}]}]

    def create_job(self, api_name, language, media_path, progress=None):
        log(f"MOCK transcription job: api={api_name} lang={language} "
            f"({os.path.getsize(media_path)} bytes)")
        if progress:
            progress.update(60, "Mock upload complete")
        return {"status": "CREATED", "correlation_id": "mock-1"}

    def poll(self, correlation_id):
        self._polls += 1
        if self._polls < 3:
            return {"status": "PENDING"}
        srt = ("1\n00:00:01,000 --> 00:00:05,000\n"
               "[OpenSubtitles AI transcription - mock pipeline result]\n")
        out = os.path.join(_profile_dir(), "mock_transcription.srt")
        with open(out, "w") as f:
            f.write(srt)
        return {"status": "COMPLETED", "url": "file://" + out}


def _pick_engine(apis, language):
    """Choose the transcription engine; ask the user when there are several."""
    if not apis:
        raise TranscriptionError("the server offers no transcription engines")
    usable = []
    for api in apis:
        if not isinstance(api, dict):
            continue
        codes = {l.get("language_code") for l in (api.get("languages_supported") or [])
                 if isinstance(l, dict)}
        if not codes or language in codes or "auto" in codes:
            usable.append(api)
    if not usable:
        usable = apis
    if len(usable) == 1:
        return usable[0]
    labels = [f"{a.get('display_name') or a.get('name')}  ({a.get('price', '?')}/s)"
              for a in usable]
    idx = xbmcgui.Dialog().select("Choose a transcription engine", labels)
    if idx < 0:
        raise UserCancelled()
    return usable[idx]


def _save_completed_result(session, state):
    """COMPLETED payload shape is loose - accept a url or inline subtitle text."""
    out = os.path.join(_profile_dir(), "transcription_result.srt")
    url = state.get("url")
    if not url and isinstance(state.get("data"), dict):
        url = state["data"].get("url")
    if url and str(url).startswith("file://"):
        return str(url)[7:]
    if url:
        # same rule as download links: a null/garbage url must raise a
        # controlled error, not a raw requests exception
        if not str(url).startswith(("http://", "https://")):
            raise TranscriptionError("transcription result carried an invalid url")
        r = session.get(url, headers={"User-Agent": get_user_agent()}, timeout=120)
        r.raise_for_status()
        with open(out, "wb") as f:
            f.write(r.content)
        return out
    for key in ("subtitles", "subtitle", "content", "data"):
        val = state.get(key)
        if isinstance(val, str) and val.strip():
            with open(out, "w") as f:
                f.write(val)
            return out
    log(f"COMPLETED but unrecognized payload keys: {sorted(state.keys())}")
    raise TranscriptionError("transcription finished but returned no subtitle")


def run_transcription(session, token, file_data, language, mock=False):
    """The whole pipeline. Returns a local subtitle file path.

    Spec: docs/opensubtitles_api_reference.html (/ai/transcribe). Shows its own
    progress dialog; cancel supported everywhere; NotDeployed on 404.
    """
    caps = get_capabilities()
    file_path = file_data.get("file_original_path", "")
    source = choose_source(caps, file_path)
    log(f"transcription rung: {source} (encode_x={caps.get('encode_x_realtime')}, io={caps.get('io_mb_per_s')})")
    if source == "too_big":
        raise TranscriptionError(
            "the server accepts at most 100 MB and no usable ffmpeg was found to "
            "extract the audio track - install ffmpeg and try again")

    client = MockTranscriptionClient() if mock else TranscriptionClient(session, token)
    progress = xbmcgui.DialogProgress()
    progress.create("OpenSubtitles AI transcription", "Checking transcription engines...")
    audio = None
    try:
        engine = _pick_engine(client.list_apis(), language)
        codes = {l.get("language_code") for l in (engine.get("languages_supported") or [])
                 if isinstance(l, dict)}
        job_language = language if language in codes else "auto"

        if source == "ffmpeg":
            progress.update(5, "Extracting audio track...")
            audio = extract_audio(caps["ffmpeg"], file_path, progress)
            upload_path = audio
        else:
            upload_path = file_path

        job = client.create_job(engine.get("name"), job_language, upload_path, progress)
        correlation_id = job.get("correlation_id")
        if not correlation_id:
            raise TranscriptionError(f"no correlation_id in response (keys: {sorted(job.keys())})")

        start = time.time()
        while time.time() - start < POLL_MAX_SECONDS:
            if progress.iscanceled():
                raise UserCancelled()
            state = client.poll(correlation_id)
            status = (state.get("status") or "").upper()
            if status == "COMPLETED":
                return _save_completed_result(session, state)
            if status in ("ERROR", "TIMEOUT"):
                raise TranscriptionError(state.get("error") or f"job ended with {status}")
            progress.update(80, "Transcribing on the server...")
            for _ in range(POLL_INTERVAL * 2):
                if progress.iscanceled():
                    raise UserCancelled()
                time.sleep(0.5)
        raise TranscriptionError("timed out waiting for the transcription job")
    finally:
        if audio:
            try:
                os.unlink(audio)
            except Exception:
                pass
        progress.close()
