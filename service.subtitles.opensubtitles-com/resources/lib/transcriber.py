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


def ffmpeg_install_hint():
    """One honest, platform-specific sentence on how to get ffmpeg.

    Streamlined-UX doctrine: when a rung is unavailable we say exactly what
    the user can do about it - or that nothing can be done on their platform."""
    if xbmc.getCondVisibility("System.Platform.OSX"):
        return ("Install ffmpeg with Homebrew:  brew install ffmpeg  "
                "(https://brew.sh), then try again.")
    if xbmc.getCondVisibility("System.Platform.Windows"):
        return ("Install ffmpeg from an administrator terminal:  winget install ffmpeg  "
                "then restart Kodi and try again.")
    if xbmc.getCondVisibility("System.Platform.Android"):
        return ("Android does not allow Kodi add-ons to run ffmpeg. Videos up to "
                "100 MB can still be transcribed by uploading them whole.")
    if os.path.isdir("/storage/.kodi"):
        return ("Install the 'ffmpeg-tools' add-on from the LibreELEC repository "
                "(Add-ons > Install from repository > LibreELEC Add-ons > "
                "Program add-ons), then try again.")
    return ("Install ffmpeg with your system's package manager "
            "(e.g. apt install ffmpeg), then try again.")


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
    """Pick the rung for this playback (docs/audio_extraction_matrix.md).

    Doctrine: try EVERY native possibility before an install hint, and the
    install hint before giving up. Order:
      ffmpeg       - full transcode, where a viable binary exists
      android_ndk  - full transcode via AMediaCodec ctypes (probe-verified);
                     falls back internally to NDK demux of an AAC track
      afconvert    - macOS built-in: direct for MP4-family, via the pure-
                     Python demuxer for MKV+AAC (no install, ever)
      pydemux      - pure-Python AAC demux, any platform, no tools at all
      upload       - whole file when it fits the server's 100 MB cap
      too_big      - honest dialog with the platform's install hint
    """
    local = os.path.exists(file_path)
    if caps.get("ffmpeg") and (caps.get("encode_x_realtime") or 0) >= 2 and local:
        return "ffmpeg"
    # SERVER LIMITATION (measured 2026-08-29): the live /ai/transcribe
    # content-sniffs uploads and accepts ONLY MPEG Audio (MP3). The verified
    # AAC-producing rungs are gated by server_accepts_aac(), which
    # SELF-DETECTS: an AAC upload rejected with "media format not valid"
    # (a free, pre-billing 400) records a 24h hold; when the API team
    # enables AAC the hold expires and these rungs light up on their own.
    if server_accepts_aac() and local and xbmc.getCondVisibility("System.Platform.Android"):
        return "android_ndk"
    if server_accepts_aac() and local and xbmc.getCondVisibility("System.Platform.OSX")             and os.path.exists("/usr/bin/afconvert"):
        return "afconvert"
    if server_accepts_aac() and local and xbmc.getCondVisibility("System.Platform.Windows"):
        return "windows_mf"
    gst = find_gst_launch()
    if local and gst and _gst_mp3_encoder(gst):
        return "gstreamer"
    if local:
        # pydemux first even for small files: a demuxed track is a smaller,
        # cleaner upload; the rung itself falls back to the whole file when
        # the container defeats it and the file fits the cap
        return "pydemux"
    return "too_big"


def _out_path(name):
    return os.path.join(_profile_dir(), name)


def extract_android(file_path, progress=None):
    """Android rung: AMediaCodec transcode, else NDK AAC demux if it fits."""
    from resources.lib import android_audio
    out = _out_path("transcribe_audio.aac")
    try:
        android_audio.transcode(file_path, out, progress=progress)
        return out
    except android_audio.AndroidAudioError as e:
        log(f"NDK transcode unavailable ({type(e).__name__}), trying NDK demux")
    android_audio.extract_aac(file_path, out)      # raises on non-AAC tracks
    if os.path.getsize(out) > MAX_UPLOAD_BYTES:
        raise TranscriptionError(
            "the audio track alone is over the server's 100 MB limit")
    return out


def extract_afconvert(file_path, progress=None):
    """macOS rung: system afconvert, no install ever.

    Direct for the MP4 family; everything else goes through the pure-Python
    demuxer first - which now yields raw AC3/EAC3/MP3/FLAC tracks too, all of
    which afconvert decodes (measured). Output must carry the right extension:
    afconvert trusts it (measured)."""
    from resources.lib.audio_demux import (extract_audio_track, probe_extension,
                                           UnsupportedSource)
    src = file_path
    demuxed = None
    if not file_path.lower().endswith((".mp4", ".m4v", ".mov")):
        demuxed = _out_path("transcribe_demux" + probe_extension(file_path))
        extract_audio_track(file_path, demuxed)     # raises UnsupportedSource
        src = demuxed
    out = _out_path("transcribe_audio.m4a")
    cmd = ["/usr/bin/afconvert", "-f", "m4af", "-d", "aac@16000",
           "-b", "24000", "--mix", "-o", out, src]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=1800)
    if demuxed:
        try:
            os.unlink(demuxed)
        except Exception:
            pass
    if proc.returncode != 0 or not os.path.exists(out):
        raise TranscriptionError(
            f"afconvert could not process this audio (exit {proc.returncode})")
    return out


_AAC_REJECTED_PROP = "os_com:aac_rejected_until"
_AAC_RETRY_AFTER = 24 * 60 * 60


def server_accepts_aac():
    """Whether the AAC-producing rungs may run.

    True unless an AAC upload was recently rejected with the server's
    format error. First attempt after install (and after every 24h) probes
    the real server by simply trying - the rejection is a free 400."""
    try:
        import xbmcgui
        raw = xbmcgui.Window(10000).getProperty(_AAC_REJECTED_PROP)
        return not raw or float(raw) < time.time()
    except Exception:
        return True


def note_aac_rejected():
    """Records the server's MP3-only rejection for 24h."""
    try:
        import xbmcgui
        xbmcgui.Window(10000).setProperty(_AAC_REJECTED_PROP,
                                          str(time.time() + _AAC_RETRY_AFTER))
    except Exception:
        pass
    log("server rejected AAC upload - AAC rungs held for 24h, using MP3 rungs")


def find_gst_launch():
    """gst-launch-1.0 if present - GStreamer rides along with most Linux
    desktops (GNOME/KDE media stacks) and, with gst-libav's avenc_aac,
    covers EVERY codec in the matrix including DTS/Opus/PCM (measured on
    Ubuntu 24.04, docs/audio_support_matrix.md)."""
    try:
        from shutil import which
        found = which("gst-launch-1.0")
        if found:
            return found
    except Exception:
        pass
    for candidate in ("/usr/bin/gst-launch-1.0", "/usr/local/bin/gst-launch-1.0"):
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _gst_mp3_encoder(gst_launch):
    inspect = gst_launch.replace("gst-launch-1.0", "gst-inspect-1.0")
    for enc in ("lamemp3enc",):
        try:
            r = subprocess.run([inspect, enc], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=15)
            if r.returncode == 0:
                return enc
        except Exception:
            continue
    return None


def extract_gstreamer(file_path, progress=None):
    """Linux no-ffmpeg rung: decodebin -> 16 kHz mono -> AAC 24k ADTS.

    Pipeline verified against the full grid (all MKV codecs incl. DTS/Opus/
    PCM, TS with plugins-bad, AVI); outputs decode clean."""
    gst = find_gst_launch()
    if not gst:
        raise TranscriptionError("gstreamer not present")
    enc = _gst_mp3_encoder(gst)
    if not enc:
        raise TranscriptionError("gstreamer present but no MP3 encoder plugin")
    out = _out_path("transcribe_audio.mp3")
    cmd = [gst, "-q", "filesrc", "location=" + file_path, "!", "decodebin", "!",
           "audioconvert", "!", "audioresample", "!",
           "audio/x-raw,rate=16000,channels=1", "!", enc, "bitrate=32", "!",
           "filesink", "location=" + out]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    while proc.poll() is None:
        if progress and progress.iscanceled():
            proc.kill()
            raise UserCancelled()
        time.sleep(0.5)
    if proc.returncode != 0 or not os.path.exists(out) or not os.path.getsize(out):
        raise TranscriptionError(f"gstreamer pipeline failed (exit {proc.returncode})")
    return out


def extract_pydemux(file_path):
    """Last tool-free rung: pure-Python track demux, if the result fits."""
    from resources.lib.audio_demux import extract_audio_track, probe_extension
    out = _out_path("transcribe_audio" + probe_extension(file_path))
    extract_audio_track(file_path, out)             # raises UnsupportedSource
    if os.path.getsize(out) > MAX_UPLOAD_BYTES:
        raise TranscriptionError(
            "the audio track alone is over the server's 100 MB limit")
    return out


def extract_audio(ffmpeg, file_path, progress=None):
    """Reencode the audio track to mono 16kHz AAC; returns the temp file path."""
    out_path = os.path.join(_profile_dir(), "transcribe_audio.mp3")
    try:
        os.unlink(out_path)
    except Exception:
        pass
    # 32k mono MP3 (~28 MB per 2h film): the LIVE server content-sniffs
    # uploads and accepts ONLY MPEG Audio today (measured 2026-08-29 -
    # AAC/m4a/wav all rejected; asked the API team to add AAC). libmp3lame
    # ships in every ffmpeg build.
    cmd = [ffmpeg, "-nostdin", "-v", "error", "-i", file_path,
           "-vn", "-sn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame",
           "-b:a", "32k", out_path]
    log("extracting audio track (mono 16kHz MP3)")
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


class CreditsNeeded(TranscriptionError):
    """The account cannot pay for the job - the caller offers the buy flow."""


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
        if r.status_code >= 400:
            # surface the server's own explanation - a bare "400 Client Error"
            # gives the user nothing to act on
            detail = ""
            try:
                payload = r.json()
                if isinstance(payload, dict):
                    data = payload.get("data")
                    if isinstance(data, list):
                        detail = "; ".join(str(x) for x in data
                                           if x and "Traceback" not in str(x))
                    elif payload.get("message"):
                        detail = str(payload["message"])
                    elif payload.get("error"):
                        # measured live shape: {"error": "...", "STATUS": "ERROR"}
                        detail = str(payload["error"])
            except Exception:
                pass
            err = TranscriptionError(
                detail or f"transcription API answered HTTP {r.status_code}")
            err.response = r
            raise err
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

    def get_credits(self):
        """GET /ai/credits -> the account's AI credit balance, or None when
        the endpoint is unreachable (never blocks the pipeline on a probe)."""
        try:
            r = self.session.get(API_URL + "ai/credits",
                                 headers=self.headers, timeout=15)
            if r.status_code == 200:
                return int((r.json().get("data") or {}).get("credits"))
        except Exception:
            pass
        return None

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
            # MEASURED against the live API (2026-08-29): api/language must be
            # multipart FORM FIELDS - as query params the server answers
            # "language parameter missing" (it only reads the POST body).
            # NOTE the published spec (docs/open_api.json) declares them as
            # query params - the spec is wrong here, measurement wins.
            r = self.session.post(
                API_URL + API_TRANSCRIBE,
                data={"api": api_name, "language": language},
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

    def get_credits(self):
        return None

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


def _match_code(language, codes):
    """Map our 2-letter language code onto the engine's own code table.

    Engines disagree on regional suffixes (nano says "sk", aws says "sk-SK"),
    so match exact first, then by primary subtag. Returns the engine's code
    or None."""
    if not language:
        return None
    lang = str(language).lower()
    primary = lang.split("-")[0]
    exact = None
    prefix = None
    for c in codes:
        if not c:
            continue
        cl = str(c).lower()
        if cl == lang:
            exact = c
        elif prefix is None and cl != "auto" and cl.split("-")[0] == primary:
            prefix = c
    return exact or prefix


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
        if not codes or _match_code(language, codes) or "auto" in codes:
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


def _save_completed_result(session, state, headers=None):
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
        # MEASURED: /ai/files/... answers 401 without the Bearer token
        fetch_headers = dict(headers or {})
        fetch_headers.setdefault("User-Agent", get_user_agent())
        r = session.get(url, headers=fetch_headers, timeout=120)
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
            "This video is over the server's 100 MB upload limit and no usable "
            "ffmpeg was found to extract the audio track.\n" + ffmpeg_install_hint())

    client = MockTranscriptionClient() if mock else TranscriptionClient(session, token)
    progress = xbmcgui.DialogProgress()
    progress.create("OpenSubtitles AI transcription", "Checking transcription engines...")
    audio = None
    try:
        engine = _pick_engine(client.list_apis(), language)
        codes = {l.get("language_code") for l in (engine.get("languages_supported") or [])
                 if isinstance(l, dict)}
        job_language = _match_code(language, codes) or ("auto" if "auto" in codes else None)
        if codes and job_language is None:
            # e.g. openai has no "auto" - sending it anyway is a guaranteed 400
            raise TranscriptionError(
                f"{engine.get('display_name') or engine.get('name')} does not "
                f"support '{language}' and offers no automatic language "
                "detection - please pick a different engine")
        job_language = job_language or "auto"

        # honest credit gate BEFORE any extraction/upload: a 0-credit account
        # would only find out after the work, as an opaque server 400
        credits = client.get_credits()
        if credits is not None:
            try:
                duration = float(xbmc.Player().getTotalTime())
            except Exception:
                duration = 0.0
            estimate = int(duration * float(engine.get("price") or 0)) + 1 if duration else 0
            if credits <= 0 or (estimate and credits < estimate):
                need = f" - this video needs about {estimate}" if estimate else ""
                raise CreditsNeeded(
                    f"You have {credits} AI credits{need} "
                    f"({engine.get('display_name') or engine.get('name')}, "
                    f"{engine.get('price')}/s).")

        upload_path = file_path
        if source == "ffmpeg":
            progress.update(5, "Extracting audio track...")
            audio = extract_audio(caps["ffmpeg"], file_path, progress)
            upload_path = audio
        elif source == "android_ndk":
            progress.update(5, "Extracting audio (device decoder)...")
            audio = extract_android(file_path, progress)
            upload_path = audio
        elif source == "afconvert":
            progress.update(5, "Extracting audio (macOS converter)...")
            audio = extract_afconvert(file_path, progress)
            upload_path = audio
        elif source == "gstreamer":
            progress.update(5, "Extracting audio (GStreamer)...")
            audio = extract_gstreamer(file_path, progress)
            upload_path = audio
        elif source == "windows_mf":
            progress.update(5, "Extracting audio (Windows decoder)...")
            from resources.lib import windows_audio
            try:
                mf_out = _out_path("transcribe_audio.m4a")
                windows_audio.transcode(file_path, mf_out, progress)
                audio = mf_out
                upload_path = audio
            except windows_audio.WindowsAudioError as e:
                # MF codec/feature gaps vary by edition - fall to pydemux
                log(f"Media Foundation route unavailable ({type(e).__name__})")
                from resources.lib.audio_demux import UnsupportedSource
                try:
                    audio = extract_pydemux(file_path)
                    upload_path = audio
                except UnsupportedSource:
                    if os.path.getsize(file_path) > MAX_UPLOAD_BYTES:
                        raise TranscriptionError(
                            "This video's audio cannot be extracted on this platform and "
                            "the file is over the server's 100 MB upload limit.\n"
                            + ffmpeg_install_hint())
        elif source == "pydemux":
            progress.update(5, "Extracting audio track...")
            from resources.lib.audio_demux import UnsupportedSource
            try:
                audio = extract_pydemux(file_path)
                upload_path = audio
            except UnsupportedSource as e:
                # nothing native worked - whole file if it fits, else honest
                log(f"pure-Python demux unavailable ({type(e).__name__})")
                if os.path.getsize(file_path) > MAX_UPLOAD_BYTES:
                    raise TranscriptionError(
                        "This video's audio cannot be extracted on this platform and "
                        "the file is over the server's 100 MB upload limit.\n"
                        + ffmpeg_install_hint())

        try:
            job = client.create_job(engine.get("name"), job_language, upload_path, progress)
        except Exception as e:
            body = ""
            resp = getattr(e, "response", None)
            if resp is not None:
                body = (resp.text or "")[:200]
            if "media format not valid" in body and source in ("android_ndk", "afconvert", "windows_mf", "upload"):
                # self-detect: this server build is MP3-only - hold the AAC
                # rungs and rerun the ladder, which now lands on an MP3 rung
                note_aac_rejected()
                progress.update(10, "Re-extracting audio as MP3...")
                source = choose_source(caps, file_path)
                log(f"transcription rung after AAC hold: {source}")
                if source == "ffmpeg":
                    audio = extract_audio(caps["ffmpeg"], file_path, progress)
                elif source == "gstreamer":
                    audio = extract_gstreamer(file_path, progress)
                else:
                    raise TranscriptionError(
                        "The transcription server currently accepts MP3 audio only, "
                        "and this device has no MP3 encoder.\n" + ffmpeg_install_hint())
                upload_path = audio
                job = client.create_job(engine.get("name"), job_language, upload_path, progress)
            else:
                raise
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
                return _save_completed_result(session, state,
                                              headers=getattr(client, "headers", None))
            if status in ("ERROR", "TIMEOUT"):
                # MEASURED: the ERROR payload carries data=[list of messages]
                detail = state.get("error")
                if not detail and isinstance(state.get("data"), list):
                    detail = "; ".join(str(m) for m in state["data"][:2]
                                       if "Trace" not in str(m))
                raise TranscriptionError(detail or f"job ended with {status}")
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
