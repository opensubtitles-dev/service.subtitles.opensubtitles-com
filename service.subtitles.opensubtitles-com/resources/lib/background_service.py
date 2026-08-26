import hashlib
import json
import os
import sys
import time
import threading

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

from resources.lib.utilities import log, normalize_string, redact_path, safe_media_filename, loggable_media
from resources.lib.data_collector import (
    get_media_data,
    get_file_path,
    is_kodi_hearing_impaired_preferred
)
from resources.lib.exceptions import AuthenticationError, BadUsernameError
from resources.lib.matcher import rank_subtitles, is_on_demand_translation
from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.upload_eligibility import check_upload_eligibility, format_resume
from resources.lib.account_state import load_account_state

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


# One session-scoped reminder that Kodi's native auto-download owns the job.
_kodi_autodownload_warned = False

_settings_write_lock = threading.Lock()


def _persist_settings(values):
    """Writes add-on settings from the service, one batch at a time.

    setSetting() saves the FULL settings snapshot of its Addon instance, so the
    lock + a fresh instance per batch keep concurrent service threads (e.g. two
    update probes at a day boundary) from reverting each other's fields.
    """
    with _settings_write_lock:
        addon = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
        for key, value in values.items():
            addon.setSetting(key, str(value))


# --- Account problem alerts -------------------------------------------------
# A misconfigured account is the one failure worth interrupting the user for:
# nothing the add-on does works until it is fixed, and only the user can fix it.
# Everything service-side - offline, 5xx, rate limits, spent quota - is transient
# and stays silent, so a warning always means "your settings need attention".
ACCOUNT_ALERT_REPEAT_AFTER = 24 * 60 * 60  # same problem warns at most once a day

# problem key -> (heading string id, message string id)
ACCOUNT_PROBLEMS = {
    "missing": (32251, 32252),       # no username / password entered yet
    "invalid": (32251, 32253),       # 401 - wrong username or password
    "bad_username": (32251, 32254),  # email address used in the username field
}


def _addon_icon():
    return xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("path"),
                                              "resources", "media", "os_logo_512x512.png"))


def _dev_setting_on(setting_id):
    val = xbmcaddon.Addon("service.subtitles.opensubtitles-com").getSetting(setting_id)
    return bool(val) and val.lower() in ("true", "1")


def _rating_preview_on():
    """Dev switch for the 5s rating-dialog preview.

    Own toggle (test_rating_preview) OR the mock-search interceptor - decoupled so
    the rating dialog can be previewed while searches still return real results.
    """
    return _dev_setting_on("test_rating_preview") or _dev_setting_on("test_flag_interceptor")


def _read_account_alert_state(addon):
    """Returns (problem, epoch, credentials fingerprint) of the last alert shown."""
    raw = addon.getSetting("account_alert_state") or ""
    parts = raw.split("|")
    problem = parts[0] if parts else ""
    try:
        epoch = float(parts[1])
    except (IndexError, TypeError, ValueError):
        epoch = 0.0
    fingerprint = parts[2] if len(parts) > 2 else ""
    return problem, epoch, fingerprint


def notify_account_problem(problem, addon=None, fingerprint=None):
    """Warns the user about an account problem only they can fix.

    The same problem repeats at most once a day, so an add-on left unconfigured does
    not nag on every playback. Editing the credentials lifts that hold immediately -
    someone who just retyped a password is waiting to hear whether it worked, and
    silence would read as success.
    """
    addon = addon or xbmcaddon.Addon("service.subtitles.opensubtitles-com")
    if problem not in ACCOUNT_PROBLEMS:
        log(__name__, f"Unknown account problem key {problem!r}, no alert shown")
        return
    heading_id, message_id = ACCOUNT_PROBLEMS[problem]
    if fingerprint is None:
        fingerprint = credentials_fingerprint(addon.getSetting("OSuser"), addon.getSetting("OSpass"))

    last_problem, last_epoch, last_fingerprint = _read_account_alert_state(addon)
    now = time.time()
    if (last_problem == problem and last_fingerprint == fingerprint
            and (now - last_epoch) < ACCOUNT_ALERT_REPEAT_AFTER):
        log(__name__, f"Account problem '{problem}' already reported, staying quiet")
        return

    addon.setSetting("account_alert_state", f"{problem}|{int(now)}|{fingerprint}")
    log(__name__, f"Notifying user of account problem: {problem}")
    xbmcgui.Dialog().notification(__language__(heading_id), __language__(message_id),
                                  _addon_icon(), 7000)


def clear_account_alert(addon):
    """Forgets the last warning so a problem coming back is reported immediately."""
    if addon.getSetting("account_alert_state"):
        addon.setSetting("account_alert_state", "")


def credentials_fingerprint(username, password):
    """SHA-256 digest identifying a username/password pair - never the values.

    Used only for alert dedup: the same account problem stays quiet for a day,
    but EDITED credentials re-alert immediately (a retyped password deserves a
    fresh verdict, and silence would read as success).
    """
    if not username or not password:
        return ""
    return hashlib.sha256(f"{username}\x00{password}".encode("utf-8")).hexdigest()


# NOTE (v2.0.0 architecture decision, 2026-08-19): the service does NOT manage
# account state. Credentials validation, quota, VIP flag and AI credits are
# written EXCLUSIVELY by test_connection.py (the "Test Connection" button) -
# a single writer in a single process. The service used to re-validate on
# onSettingsChanged and at startup; that fought the settings dialog's snapshot
# saves and the Test Connection process, tearing account fields (observed live).
# The service still READS credentials for auto-download and raises the
# account-problem notifications, but never writes account_* settings.


def _reconcile_account_display():
    """Re-syncs account display settings from the authoritative state file.

    Read-only against the API: no login, no network. Runs after every settings
    save; only writes when a dialog snapshot actually drifted the values.
    """
    monitor = xbmc.Monitor()
    # Let the dialog finish closing; its save is what we are correcting.
    while xbmc.getCondVisibility("Window.IsActive(addonsettings)"):
        if monitor.waitForAbort(1):
            return

    state = load_account_state()
    if not state:
        return
    addon = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
    drift = {key: value for key, value in state.items()
             if addon.getSetting(key) != value}
    if drift:
        log(__name__, f"Account display drifted from state file, restoring: {sorted(drift)}")
        _persist_settings(drift)


class OpenSubtitlesMonitor(xbmc.Monitor):
    """Monitors Kodi system events and settings updates."""
    def __init__(self, player=None):
        super().__init__()
        self.player = player

    def onSettingsChanged(self):
        # Player preferences reload + account display reconciliation. The service
        # never VALIDATES credentials (Test Connection is the single source of
        # truth) - but any settings-dialog save can revert account display values
        # to a stale snapshot (Kodi keeps the pre-RunScript dialog model alive),
        # so after each save the display is re-synced from the state file.
        log(__name__, "Settings changed, reloading background service preferences")
        if self.player:
            self.player.reload_settings()
        threading.Thread(target=_reconcile_account_display, daemon=True).start()


class OpenSubtitlesPlayer(xbmc.Player):
    """Monitors video playback lifecycle for auto-download and rating prompts."""
    def __init__(self):
        super().__init__()
        self.monitor = None
        self.active_session = None
        self.reload_settings()

    def reload_settings(self):
        try:
            val_auto = __addon__.getSetting("auto_download")
            self.auto_download_enabled = val_auto.lower() in ("true", "1") if val_auto else False

            val_rate = __addon__.getSetting("prompt_rating")
            self.prompt_rating_enabled = val_rate.lower() in ("true", "1") if val_rate else False
        except Exception as e:
            log(__name__, f"Error reading settings: {type(e).__name__}")
            self.auto_download_enabled = False
            self.prompt_rating_enabled = False

    def onAVStarted(self):
        """Called by Kodi when audio/video playback begins."""
        try:
            if not self.isPlayingVideo():
                return
            self._handle_playback_started()
        except Exception as e:
            log(__name__, f"Exception in onAVStarted: {type(e).__name__}")

    def onPlayBackStopped(self):
        """Called by Kodi when playback is stopped by user."""
        try:
            self._handle_playback_ended(natural_end=False)
        except Exception as e:
            log(__name__, f"Exception in onPlayBackStopped: {type(e).__name__}")

    def onPlayBackEnded(self):
        """Called by Kodi when video reaches its natural end."""
        try:
            self._handle_playback_ended(natural_end=True)
        except Exception as e:
            log(__name__, f"Exception in onPlayBackEnded: {type(e).__name__}")

    def _handle_playback_started(self):
        self.reload_settings()
        self.active_session = None
        log(__name__, f"Playback started: auto_download={self.auto_download_enabled}, "
                      f"rating_prompt={self.prompt_rating_enabled}")

        # Dev preview: rating dialog pops 5s into playback, so its look can be
        # checked without watching a whole film.
        if _rating_preview_on():
            threading.Thread(target=self._rating_preview, daemon=True).start()

        if not self.auto_download_enabled:
            log(__name__, "Auto-download: disabled in settings")
        else:
            # Network never runs on Kodi's callback thread (freezes the player UI).
            threading.Thread(target=self._auto_download_flow, daemon=True).start()

        # Upload dry-run: when playback runs on a LOCAL sidecar subtitle (not one
        # we just fetched), that file is the actual sharing candidate - track it.
        if _dev_setting_on("auto_upload_subtitles"):
            threading.Thread(target=self._track_local_subtitle_session, daemon=True).start()

    def _track_local_subtitle_session(self):
        """Builds a session around a user-provided sidecar subtitle, if any.

        Waits out the auto-download flow; only steps in when no session exists,
        so an OpenSubtitles-sourced session always wins (its file is already on
        the site - nothing to share).
        """
        if self.monitor and self.monitor.waitForAbort(20):
            return
        try:
            if self.active_session is not None or not self.isPlayingVideo():
                return
            file_path = get_file_path()
            if not file_path or str(file_path).startswith(
                    ("http://", "https://", "plugin://", "pvr://", "upnp://")):
                return
            folder = os.path.dirname(file_path)
            stem = os.path.splitext(safe_media_filename(file_path))[0]
            candidates = sorted(
                name for name in os.listdir(folder)
                if name.startswith(stem) and name.lower().endswith((".srt", ".vtt", ".ass", ".ssa"))
            )
            if not candidates:
                log(__name__, "Upload dry-run: no sidecar subtitle next to the video")
                return
            sub_name = candidates[0]
            # <video>.<lang>.<ext> convention: the token before the extension
            parts = sub_name[len(stem):].strip(".").split(".")
            sub_language = parts[0].lower() if len(parts) > 1 and len(parts[0]) in (2, 3) else ""

            total_time = self.getTotalTime() if hasattr(self, "getTotalTime") else 0
            self.active_session = {
                "file_id": None,
                "subtitle_id": None,
                "release": sub_name,
                "title": stem,
                "start_time": time.time(),
                "total_time": total_time,
                "origin": "local",
                "sub_path": os.path.join(folder, sub_name),
                "sub_language": sub_language,
                "media": {},
                "settle_until": time.time() + 5,
            }
            log(__name__, f"Upload dry-run: tracking a local sidecar subtitle "
                          f"(lang={sub_language or 'unknown'}, {len(candidates)} candidate(s))")
        except Exception as e:
            log(__name__, f"Upload dry-run: sidecar tracking failed ({type(e).__name__})")

    def onAVChange(self):
        """Fires on any audio/video/subtitle stream change - including our own
        setSubtitles/AddSubtitle calls, hence the settle window per session."""
        try:
            session = self.active_session
            if session and time.time() > session.get("settle_until", 0):
                if not session.get("stream_switched"):
                    log(__name__, "Playback session: subtitle/AV stream switched by user")
                session["stream_switched"] = True
        except Exception:
            pass

    def _active_subtitle_state(self):
        """Returns (enabled, language, name) of the selected subtitle, or None if unknown.

        Player.GetProperties is the authoritative probe: getAvailableSubtitleStreams()
        lists streams even when subtitle display is switched OFF, and the
        Player.Language(Subtitles) InfoLabel names the selected track whether or not
        it is shown - both were skipping auto-download for videos where the user had
        subtitles disabled. (See docs/kodi_api_internals.md section 6.)
        """
        try:
            players = json.loads(xbmc.executeJSONRPC(json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
            ))).get("result", [])
            player_id = next((p["playerid"] for p in players if p.get("type") == "video"), None)
            if player_id is None:
                return None
            props = json.loads(xbmc.executeJSONRPC(json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "Player.GetProperties",
                 "params": {"playerid": player_id,
                            "properties": ["subtitleenabled", "currentsubtitle"]}}
            ))).get("result", {})
            current = props.get("currentsubtitle") or {}
            return (bool(props.get("subtitleenabled")),
                    current.get("language", ""), current.get("name", ""))
        except Exception as e:
            log(__name__, f"Auto-download: subtitle state probe failed ({type(e).__name__}), proceeding anyway")
            return None

    def _kodi_setting(self, name):
        """Reads one of Kodi's OWN settings (not add-on settings) via JSON-RPC."""
        try:
            return json.loads(xbmc.executeJSONRPC(json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "Settings.GetSettingValue",
                 "params": {"setting": name}}
            ))).get("result", {}).get("value")
        except Exception as e:
            log(__name__, f"Kodi setting {name} unreadable ({type(e).__name__})")
            return None

    def _preferred_subtitle_languages(self):
        """(primary_iso639_1, [all wanted iso639_1]) from Kodi's subtitle settings.

        subtitles.languages is the user's multi-select "languages to download
        subtitles for"; locale.subtitlelanguage is the single preferred one
        (may hold magic values like "original"/"default", which are skipped).
        """
        from resources.lib.utilities import get_language_override
        override = get_language_override()
        if override:
            log(__name__, f"DEV language override active: auto-download uses '{override}' only")
            return override, [override]

        def to_iso(name):
            try:
                code = xbmc.convertLanguage(str(name), xbmc.ISO_639_1)
            except Exception:
                code = None
            return code if isinstance(code, str) and len(code) == 2 else str(name)[:2].lower()

        names = self._kodi_setting("subtitles.languages")
        codes = []
        for name in (names if isinstance(names, list) else []):
            code = to_iso(name)
            if code and code not in codes:
                codes.append(code)

        primary = None
        primary_name = self._kodi_setting("locale.subtitlelanguage")
        if isinstance(primary_name, str) and primary_name and \
                primary_name.lower() not in ("original", "default", "none", "forced_only"):
            primary = to_iso(primary_name)
        if not primary or len(primary) != 2:
            raw = xbmc.getInfoLabel("System.Language(Subtitles)") or "en"
            primary = str(raw)[:2].lower()

        if primary not in codes:
            codes.insert(0, primary)
        return primary, codes[:5]  # quota safety: never more than 5 downloads per file

    def _add_subtitle_stream(self, sub_path):
        """Adds a subtitle file to the player's stream list WITHOUT activating it.

        Player.AddSubtitle activates what it adds (that is what Kodi itself uses
        after a dialog download), so the primary language must be applied last
        via setSubtitles() to win the active slot back.
        """
        try:
            players = json.loads(xbmc.executeJSONRPC(json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
            ))).get("result", [])
            player_id = next((p["playerid"] for p in players if p.get("type") == "video"), None)
            if player_id is None:
                return
            xbmc.executeJSONRPC(json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "Player.AddSubtitle",
                 "params": {"playerid": player_id, "subtitle": sub_path}}))
            log(__name__, "Auto-download: added an alternative subtitle stream")
        except Exception as e:
            log(__name__, f"Auto-download: could not add a stream ({type(e).__name__})")

    def _subtitle_destination_dir(self, video_file_path):
        """Directory where the user's Kodi wants downloaded subtitles kept.

        Mirrors Kodi's own storage chain (docs/kodi_api_internals.md section 1a):
        the movie's folder when subtitles.storagemode == 0 (SUBTITLE_STORAGEMODE_
        MOVIEPATH, the default) and the source is a real file; else the custom
        subtitle folder (special://subtitles) when configured; else None - the
        subtitle then stays in special://temp for this session only.
        """
        try:
            storage_mode = self._kodi_setting("subtitles.storagemode")
            is_stream = str(video_file_path or "").startswith(
                ("http://", "https://", "plugin://", "pvr://", "upnp://"))
            if storage_mode == 0 and video_file_path and not is_stream:
                return os.path.dirname(video_file_path)
            custom = xbmcvfs.translatePath("special://subtitles") or ""
            return custom or None
        except Exception as e:
            log(__name__, f"Auto-download: could not resolve subtitle storage dir ({type(e).__name__})")
            return None

    def _store_subtitle_copy(self, source_path, target):
        """Copies a downloaded subtitle to its final home. Returns target or None.

        xbmcvfs.copy first (speaks smb://, nfs://, every Kodi VFS backend), with
        two known quirks handled: it refuses to overwrite on some backends (delete
        first), and it has been seen returning False on plain local paths - the
        stdlib fallback covers those AND logs the real OS error when even that
        fails, so a permissions problem names itself in the log.
        """
        try:
            if xbmcvfs.exists(target):
                xbmcvfs.delete(target)
            if xbmcvfs.copy(source_path, target):
                log(__name__, "Auto-download: stored subtitle beside the video")
                return target
            log(__name__, "Auto-download: xbmcvfs.copy refused the target, trying direct write")
        except Exception as e:
            log(__name__, f"Auto-download: xbmcvfs copy raised {type(e).__name__}, trying direct write")

        try:
            import shutil
            shutil.copyfile(source_path, target)
            log(__name__, "Auto-download: stored subtitle beside the video (direct write)")
            return target
        except OSError as e:
            log(__name__, f"Auto-download: cannot write the target ({type(e).__name__}) - "
                          f"keeping session-only temp copy")
            return None

    def _auto_download_flow(self):
        log(__name__, "Auto-download: flow starting")
        # Give Kodi player a moment to initialize streams and metadata
        if self.monitor and self.monitor.waitForAbort(1):
            return

        try:
            state = self._active_subtitle_state()
            # the track NAME often carries the movie title - log presence only
            state_summary = ((state[0], state[1], "named" if state[2] else "")
                             if state else None)
            log(__name__, f"Auto-download: subtitle state = {state_summary}")
            if state and state[0] and (state[1] or state[2]):
                log(__name__, f"Auto-download: a subtitle is already enabled "
                              f"(lang={state[1]!r}), skipping")
                return

            # Never fight Kodi's own "Auto download first subtitle": both firing means
            # two downloads, double quota burn and a race for the active subtitle.
            # Kodi's wins the standoff; ours stands down and says why (once).
            if self._kodi_setting("subtitles.downloadfirst"):
                log(__name__, "Auto-download: Kodi's native 'Auto download first subtitle' "
                              "is enabled - standing down to avoid a double download")
                global _kodi_autodownload_warned
                if not _kodi_autodownload_warned:
                    _kodi_autodownload_warned = True
                    xbmcgui.Dialog().notification(
                        __addon_name__, __language__(32260), _addon_icon(), 6000)
                return

            media_data = get_media_data()
            log(__name__, "Auto-download: media data = %s" % loggable_media(media_data))
            if not media_data:
                log(__name__, "Auto-download: no media data collected, aborting")
                return

            file_path = get_file_path()
            video_filename = safe_media_filename(file_path) if file_path else ""

            # Search across ALL of the user's subtitle languages in one API call,
            # so one top pick per language can be offered afterwards.
            primary_lang, wanted_langs = self._preferred_subtitle_languages()
            log(__name__, f"Auto-download: languages wanted={wanted_langs}, primary={primary_lang}")
            media_data["languages"] = ",".join(wanted_langs)

            # Check credentials
            username = __addon__.getSetting("OSuser")
            password = __addon__.getSetting("OSpass")
            api_key = __addon__.getSetting("APIKey")
            if not username or not password:
                log(__name__, "Auto-download skipped: account not configured")
                notify_account_problem("missing")
                return
            provider = OpenSubtitlesProvider(api_key, username, password)

            # Search subtitles
            log(__name__, "⚡ Auto-search executing")
            subtitles = provider.search_subtitles(media_data)
            
            # Retry fallback if empty
            if not subtitles and media_data.get("search_fallbacks"):
                for fb in media_data["search_fallbacks"]:
                    if self.monitor and self.monitor.abortRequested():
                        return
                    # each attempt is self-contained but must carry the languages
                    subtitles = provider.search_subtitles({**fb, "languages": ",".join(wanted_langs)})
                    if subtitles:
                        break

            if not subtitles:
                log(__name__, "Auto-search: no subtitles found")
                return

            # Smart ranking
            smart_ranking = __addon__.getSetting("smart_ranking") != "false"
            hi_setting = __addon__.getSetting("hearing_impaired")
            prefer_hi = (hi_setting == "only") or (hi_setting == "include" and is_kodi_hearing_impaired_preferred())

            ranked = rank_subtitles(
                subtitles,
                video_filename,
                smart_ranking=smart_ranking,
                preferred_languages=wanted_langs,
                prefer_hearing_impaired=prefer_hi
            )

            if not ranked:
                return

            # Our edge over Kodi's native auto-download: the best subtitle for EVERY
            # preferred language, not just one file. The primary language plays; the
            # rest are added to the player's subtitle stream list, one key-press away.
            top_per_lang = {}
            for sub in ranked:
                attrs = sub.get("attributes", {})
                if is_on_demand_translation(attrs):
                    # Silent background downloads must never trigger a paid,
                    # slow on-demand AI translation - that is a user decision.
                    continue
                lang = str(attrs.get("language", "")).lower()
                if lang and lang not in top_per_lang and attrs.get("files"):
                    top_per_lang[lang] = sub
            picks = [(lang, top_per_lang[lang]) for lang in wanted_langs if lang in top_per_lang]
            if not picks:
                picks = [(str(ranked[0]["attributes"].get("language", "")).lower(), ranked[0])]
            log(__name__, f"Auto-download: top pick per language = "
                          f"{[(l, (s.get('id') or (s['attributes'].get('files') or [{}])[0].get('file_id'))) for l, s in picks]}")

            temp_dir = xbmcvfs.translatePath("special://temp/")
            # Persist where the user's Kodi wants subtitles, named the way Kodi
            # names them (<video>.<lang>.srt) so future plays pick them up
            # automatically without any search.
            dest_dir = self._subtitle_destination_dir(file_path)
            video_stem = os.path.splitext(safe_media_filename(file_path))[0] if file_path else ""
            storage_kind = "video folder or custom dir" if dest_dir else "special://temp (session only)"
            log(__name__, f"Auto-download: storage = {storage_kind}")

            loaded = []  # (lang, sub, path, file_id) per successful download
            for lang, sub in picks:
                if self.monitor and self.monitor.abortRequested():
                    return
                file_id = sub["attributes"]["files"][0].get("file_id")
                try:
                    download_data = provider.download_subtitle({"file_id": file_id})
                except Exception as e:
                    log(__name__, f"Auto-download: {lang} download failed ({type(e).__name__}), continuing")
                    continue
                content = download_data.get("content")
                if not content:
                    log(__name__, f"Auto-download: {lang} content empty, continuing")
                    continue

                sub_path = os.path.join(temp_dir, f"os_auto_{file_id}.{lang}.srt")
                with open(sub_path, "wb") as f:
                    f.write(content)

                if dest_dir and video_stem:
                    target = os.path.join(dest_dir, f"{video_stem}.{lang}.srt")
                    stored = self._store_subtitle_copy(sub_path, target)
                    if stored:
                        sub_path = stored
                loaded.append((lang, sub, sub_path, file_id))

            if not loaded:
                log(__name__, "Auto-download: nothing could be downloaded")
                return

            # Primary language becomes the active subtitle; the rest join the
            # player's stream list as selectable alternatives.
            primary = next((entry for entry in loaded if entry[0] == primary_lang), loaded[0])
            for entry in loaded:
                if entry is not primary:
                    self._add_subtitle_stream(entry[2])

            lang, sub, sub_path, file_id = primary
            self.setSubtitles(sub_path)

            attributes = sub["attributes"]
            loaded_langs = [entry[0] for entry in loaded]
            release_name = attributes.get("release") or attributes.get("feature_details", {}).get("title") or "OpenSubtitles"
            log(__name__, f"Auto-download: applied {lang}, loaded languages: {loaded_langs}")

            # Always tell the user a subtitle was silently applied - an unannounced
            # subtitle looks like it came from nowhere (setting removed 2026-08-19).
            langs_suffix = f" (+{', '.join(l for l in loaded_langs if l != lang)})" if len(loaded_langs) > 1 else ""
            xbmcgui.Dialog().notification(__addon_name__,
                                          f"Auto-loaded: {release_name[:30]}{langs_suffix}",
                                          _addon_icon(), 3500)

            # Record active session for optional post-playback rating.
            # The API item carries the id top-level ({"id": ..., "attributes": {...}})
            # AND inside attributes as subtitle_id - take whichever survived the
            # provider, and log it so a lost id is visible in the log, not silent.
            subtitle_id = sub.get("id") or attributes.get("subtitle_id")
            log(__name__, f"Rating session: subtitle_id={subtitle_id!r}, file_id={file_id}")
            total_time = self.getTotalTime() if hasattr(self, "getTotalTime") else 0
            self.active_session = {
                "file_id": file_id,
                "subtitle_id": subtitle_id,
                "release": release_name,
                "title": media_data.get("query") or video_filename,
                "start_time": time.time(),
                "total_time": total_time,
                # upload dry-run context: this file CAME from OpenSubtitles, so it
                # is never upload-eligible itself - tracked to prove the pipeline.
                "origin": "opensubtitles",
                "sub_path": sub_path,
                "sub_language": lang,
                "media": media_data,
                # our own setSubtitles/AddSubtitle calls fire onAVChange; changes
                # within this window are ours, later ones are the user switching.
                "settle_until": time.time() + 15,
            }

        except AuthenticationError:
            log(__name__, "Auto-download failed: credentials rejected")
            notify_account_problem("invalid")
        except BadUsernameError:
            log(__name__, "Auto-download failed: email used instead of username")
            notify_account_problem("bad_username")
        except Exception as e:
            # Anything else (offline, 5xx, quota, no results) is transient: log only.
            log(__name__, f"Error in auto-download execution: {type(e).__name__}")

    def _handle_playback_ended(self, natural_end=False):
        if not self.active_session:
            return

        session = dict(self.active_session)
        self.active_session = None
        log(__name__, f"Session closing: watched={session.get('last_position', 0):.0f}s"
                      f"/{session.get('total_time', 0):.0f}s, "
                      f"subtitle_delay={session.get('subtitle_delay', 'unknown')!r}")

        # Auto-upload DRY RUN: log the full eligibility resume, upload nothing.
        try:
            eligible, upload_checks = check_upload_eligibility(
                session, _dev_setting_on("auto_upload_subtitles"))
            log(__name__, format_resume(eligible, upload_checks))
        except Exception as e:
            log(__name__, f"Upload dry-run evaluation failed: {type(e).__name__}")

        # Rating prompt only for sessions with something to rate
        if self.prompt_rating_enabled and session.get("subtitle_id"):
            # Run voting prompt in background thread so Kodi UI doesn't hang
            threading.Thread(target=self._prompt_rating, args=(session, natural_end), daemon=True).start()

    def _rating_preview(self):
        """Dev-only: pops the rating dialog 5s into playback so it can be inspected.

        Triggered from playback start when test_flag_interceptor is ON. Marked as a
        preview session so no vote is ever sent to the API.
        """
        if self.monitor and self.monitor.waitForAbort(5):
            return
        title = xbmc.getInfoLabel("VideoPlayer.Title") or "Preview Movie"
        session = {
            "file_id": 0,
            "subtitle_id": "preview",
            "release": "Movie.2024.1080p.Preview.DEV-MOCK",
            "title": title,
            "start_time": time.time(),
            "total_time": 0,
            "preview": True,
        }
        log(__name__, "DEV: showing rating dialog preview (test interceptor ON)")
        self._prompt_rating(session, natural_end=True)

    # Star glyphs are the two confirmed-rendering Misc Symbols
    # (docs/kodi_ui_font_compatibility.md) - never emoji.
    RATING_OPTIONS = [
        ("★☆☆☆☆   1 - Bad", 1),
        ("★★☆☆☆   2 - Poor", 2),
        ("★★★☆☆   3 - Okay", 3),
        ("★★★★☆   4 - Good", 4),
        ("★★★★★   5 - Excellent", 5),
    ]

    def _prompt_rating(self, session, natural_end):
        try:
            elapsed = time.time() - session.get("start_time", 0)
            total = session.get("total_time", 0)

            # Check if watched at least 3 minutes and > 30% of media (or finished naturally)
            if not session.get("preview") and not natural_end and total > 0 and (elapsed / total) < 0.3:
                log(__name__, "Watched duration too short for rating prompt")
                return

            dialog = xbmcgui.Dialog()
            title = session.get("title", "Video")
            release = session.get("release", "Subtitle")

            # Step 1 - quality, 1..5. select() fits a five-way choice on a TV
            # remote far better than chained yes/no dialogs; autoclose after 60s
            # so an unattended TV is not held hostage. Returns -1 on cancel or
            # autoclose - no rating is ever submitted that nobody cast.
            heading = f"Rate subtitles: {title[:40]} ({release[:30]})"
            choice = dialog.select(heading, [label for label, _val in self.RATING_OPTIONS],
                                   autoclose=60000)
            if choice < 0:
                log(__name__, "Rating prompt dismissed without a rating")
                return
            rating = self.RATING_OPTIONS[choice][1]

            # Step 2 - sync verdict, optional. yesnocustom because plain yesno
            # cannot distinguish autoclose from a real "No".
            # Returns: 1 = yes, 0 = no, 2 = custom (skip), -1 = cancelled/autoclosed.
            sync_answer = dialog.yesnocustom(__addon_name__,
                                             "Were the subtitles in sync with the video?",
                                             customlabel="Skip",
                                             yeslabel="Yes", nolabel="No",
                                             autoclose=30000)
            sync = {1: True, 0: False}.get(sync_answer)  # None when skipped/closed

            if session.get("preview"):
                log(__name__, f"DEV preview: rating={rating}, sync={sync}, nothing sent")
                return

            api_key = __addon__.getSetting("APIKey")
            username = __addon__.getSetting("OSuser")
            password = __addon__.getSetting("OSpass")

            provider = OpenSubtitlesProvider(api_key, username, password)
            success = provider.rate_subtitle(session["subtitle_id"], rating, sync=sync)

            if success:
                dialog.notification(__addon_name__, __language__(32246), _addon_icon(), 3000)

        except AuthenticationError:
            log(__name__, "Rating vote rejected: credentials no longer valid")
            notify_account_problem("invalid")
        except Exception as e:
            log(__name__, f"Error during post-playback rating: {type(e).__name__}")


UPDATE_CHECK_EVERY = 24 * 60 * 60  # once per day


def _update_state_path():
    profile = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
    return os.path.join(profile, "update_check.json")


def _read_update_state():
    try:
        with open(_update_state_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_update_state(state):
    """The schedule stamp lives in its OWN file, not in settings.

    Settings are one shared snapshot written whole by every process (service,
    search plugin, settings dialog) - any of them can silently revert a field
    written by another. A dedicated file has exactly one writer (this function)
    and an atomic replace, so the 24h schedule can never be clobbered. The
    settings row is written too, but only as a best-effort display.
    """
    path = _update_state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp_path, path)


def check_for_update_silently():
    """Daily background version check - no dialogs, result lands in settings + log.

    Reuses check_updates.py's fetch/compare. On a newer version: one notification
    and a repo refresh so Kodi's own auto-update can pick it up. The read-only
    "Update last checked" settings row always shows when and what was found.
    """
    addon = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
    try:
        last = float(_read_update_state().get("checked_at")
                     or addon.getSetting("update_checked_at") or 0)
    except (TypeError, ValueError):
        last = 0
    if time.time() - last < UPDATE_CHECK_EVERY:
        return

    from datetime import datetime
    import check_updates as updater

    monitor = xbmc.Monitor()
    if monitor.abortRequested():
        return

    latest = updater.fetch_latest_remote_version()
    now = datetime.now()

    current = addon.getAddonInfo("version")
    stamp = now.strftime("%Y-%m-%d %H:%M")
    if not latest:
        result = f"{stamp} (update server unreachable)"
        _write_update_state({"checked_at": int(now.timestamp()), "result": result})
        _persist_settings({"update_last_checked": result})
        log(__name__, "Update check: remote version unavailable")
        return

    if updater.parse_version_tuple(latest) > updater.parse_version_tuple(current):
        result = f"{stamp} (v{latest} available!)"
        _write_update_state({"checked_at": int(now.timestamp()), "result": result})
        _persist_settings({"update_last_checked": result})
        log(__name__, f"Update check: v{latest} available (installed v{current})")
        xbmc.executebuiltin("UpdateAddonRepos")
        xbmcgui.Dialog().notification(__addon_name__,
                                      f"{__language__(32257)}: v{latest}",
                                      _addon_icon(), 6000)
    else:
        result = f"{stamp} (v{current} is latest)"
        _write_update_state({"checked_at": int(now.timestamp()), "result": result})
        _persist_settings({"update_last_checked": result})
        log(__name__, f"Update check: up to date (v{current})")


def run_service():
    """Main entrypoint for xbmc.service background monitor."""
    player = OpenSubtitlesPlayer()
    monitor = OpenSubtitlesMonitor(player)
    player.monitor = monitor

    log(__name__, "OpenSubtitles.com Background Monitor Service started")

    # Update check only - account state belongs to Test Connection (single writer)
    threading.Thread(target=check_for_update_silently, daemon=True).start()

    last_update_probe = time.time()

    # Non-blocking main loop with zero shutdown delay
    while not monitor.abortRequested():
        if monitor.waitForAbort(1):
            break

        # While a rated session is active, sample the things only available
        # DURING playback: watched position and the user's subtitle offset
        # (Player.SubtitleDelay InfoLabel - it has no JSON-RPC equivalent and
        # is unreadable once playback stops).
        try:
            session = player.active_session
            if session and player.isPlaying():
                session["last_position"] = player.getTime()
                delay = xbmc.getInfoLabel("Player.SubtitleDelay") or ""
                if delay:
                    session["subtitle_delay"] = delay
        except Exception:
            pass  # player state races a stop; next tick corrects it

        now = time.time()
        # Hourly probe; check_for_update_silently() itself enforces the 24h spacing
        # against the persisted stamp, so restarts don't reset the schedule.
        if now - last_update_probe > 3600:
            last_update_probe = now
            threading.Thread(target=check_for_update_silently, daemon=True).start()

    log(__name__, "OpenSubtitles.com Background Monitor Service stopped gracefully")


if __name__ == "__main__":
    run_service()
