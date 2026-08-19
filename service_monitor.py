import os
import sys
import time
import threading

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

from resources.lib.utilities import log, normalize_string
from resources.lib.data_collector import (
    get_media_data,
    get_file_path,
    is_kodi_hearing_impaired_preferred
)
from resources.lib.exceptions import AuthenticationError, BadUsernameError
from resources.lib.matcher import rank_subtitles
from resources.lib.osclient.provider import OpenSubtitlesProvider

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def check_and_refresh_account_status(force=False):
    """
    Silently checks and refreshes account status in background with a short timeout.
    Updates quota and VIP info if stale (> 12 hours) or forced on settings change.
    """
    username = __addon__.getSetting("OSuser")
    password = __addon__.getSetting("OSpass")
    api_key = __addon__.getSetting("APIKey")

    if not username or not password:
        return

    verified_at = __addon__.getSetting("account_verified_at")
    try:
        age = time.time() - float(verified_at) if verified_at and verified_at != "0" else 9999999
    except (ValueError, TypeError):
        age = 9999999

    # Only refresh if older than 12 hours (43,200s) or forced
    if not force and age < 43200:
        log(__name__, f"Account status is fresh (age: {int(age/3600)}h), skipping background refresh")
        return

    log(__name__, "🔄 Background Service: Refreshing account verification & quota...")
    try:
        from datetime import datetime
        provider = OpenSubtitlesProvider(api_key, username, password)
        provider.login()
        user_info = provider.get_user_info()

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M")
        now_epoch = int(now.timestamp())

        level = user_info.get("level", "User")
        remaining = user_info.get("remaining_downloads", "N/A")
        allowed = user_info.get("allowed_downloads", "N/A")
        vip_badge = "VIP" if user_info.get("vip") else "Free User"

        __addon__.setSetting("account_status", f"OK ({vip_badge})")
        __addon__.setSetting("account_details", f"Quota: {remaining}/{allowed} left | Level: {level}")
        __addon__.setSetting("account_checked_at", now_str)
        __addon__.setSetting("account_verified_at", str(now_epoch))
        log(__name__, f"✅ Background account refresh complete: {vip_badge} ({remaining}/{allowed} left)")
    except AuthenticationError:
        __addon__.setSetting("account_status", "Error 401 (Invalid credentials)")
        __addon__.setSetting("account_details", "Check username and password")
    except BadUsernameError:
        __addon__.setSetting("account_status", "Error 400 (Bad username)")
        __addon__.setSetting("account_details", "Use username, not email address")
    except Exception as e:
        log(__name__, f"Background account refresh skipped/failed: {e}")
        if age > 86400:
            last_checked = __addon__.getSetting("account_checked_at")
            if last_checked:
                __addon__.setSetting("account_status", "Active (Offline / Cached)")


class OpenSubtitlesMonitor(xbmc.Monitor):
    """Monitors Kodi system events and settings updates."""
    def __init__(self, player=None):
        super().__init__()
        self.player = player

    def onSettingsChanged(self):
        log(__name__, "Settings changed, reloading background service preferences")
        if self.player:
            self.player.reload_settings()
        threading.Thread(target=check_and_refresh_account_status, kwargs={"force": True}, daemon=True).start()


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
            
            val_notify = __addon__.getSetting("auto_download_notify")
            self.auto_download_notify = val_notify.lower() not in ("false", "0") if val_notify else True

            val_rate = __addon__.getSetting("prompt_rating")
            self.prompt_rating_enabled = val_rate.lower() in ("true", "1") if val_rate else False
        except Exception as e:
            log(__name__, f"Error reading settings: {e}")
            self.auto_download_enabled = False
            self.auto_download_notify = True
            self.prompt_rating_enabled = False

    def onAVStarted(self):
        """Called by Kodi when audio/video playback begins."""
        try:
            if not self.isPlayingVideo():
                return
            self._handle_playback_started()
        except Exception as e:
            log(__name__, f"Exception in onAVStarted: {e}")

    def onPlayBackStopped(self):
        """Called by Kodi when playback is stopped by user."""
        try:
            self._handle_playback_ended(natural_end=False)
        except Exception as e:
            log(__name__, f"Exception in onPlayBackStopped: {e}")

    def onPlayBackEnded(self):
        """Called by Kodi when video reaches its natural end."""
        try:
            self._handle_playback_ended(natural_end=True)
        except Exception as e:
            log(__name__, f"Exception in onPlayBackEnded: {e}")

    def _handle_playback_started(self):
        self.reload_settings()
        self.active_session = None

        if not self.auto_download_enabled:
            return

        # Give Kodi player a moment to initialize streams and metadata
        if self.monitor and self.monitor.waitForAbort(1):
            return

        try:
            # Check if video already has embedded/active subtitles in preferred language
            available_streams = self.getAvailableSubtitleStreams() if hasattr(self, "getAvailableSubtitleStreams") else []
            preferred_lang = xbmc.getInfoLabel("Player.Language(Subtitles)")
            if available_streams and preferred_lang and preferred_lang.lower() != "none":
                log(__name__, f"Embedded subtitle stream already active ({preferred_lang}), skipping auto-download")
                return

            media_data = get_media_data()
            if not media_data:
                log(__name__, "No media data collected for playback")
                return

            file_path = get_file_path()
            video_filename = os.path.basename(file_path) if file_path else ""

            # Check credentials
            username = __addon__.getSetting("OSuser")
            password = __addon__.getSetting("OSpass")
            api_key = __addon__.getSetting("APIKey")
            provider = OpenSubtitlesProvider(api_key, username, password)

            # Search subtitles
            log(__name__, f"⚡ Auto-search executing for: {video_filename or media_data.get('query')}")
            subtitles = provider.search_subtitles(media_data)
            
            # Retry fallback if empty
            if not subtitles and media_data.get("search_fallbacks"):
                for fb in media_data["search_fallbacks"]:
                    if self.monitor and self.monitor.abortRequested():
                        return
                    subtitles = provider.search_subtitles(fb)
                    if subtitles:
                        break

            if not subtitles:
                log(__name__, "Auto-search: no subtitles found")
                return

            # Smart ranking
            smart_ranking = __addon__.getSetting("smart_ranking") != "false"
            hi_setting = __addon__.getSetting("hearing_impaired")
            prefer_hi = (hi_setting == "only") or (hi_setting == "include" and is_kodi_hearing_impaired_preferred())

            preferred_languages = []
            pref_lang_raw = xbmc.getInfoLabel("System.Language(Subtitles)") or "en"
            preferred_languages.append(pref_lang_raw[:2].lower())

            ranked = rank_subtitles(
                subtitles,
                video_filename,
                smart_ranking=smart_ranking,
                preferred_languages=preferred_languages,
                prefer_hearing_impaired=prefer_hi
            )

            if not ranked:
                return

            best_sub = ranked[0]
            attributes = best_sub.get("attributes", {})
            files = attributes.get("files", [])
            if not files:
                return

            file_id = files[0].get("file_id")
            release_name = attributes.get("release") or attributes.get("feature_details", {}).get("title") or "OpenSubtitles"
            sub_id = best_sub.get("id")

            # Check match score confidence
            match_score = best_sub.get("_match_score", 0)
            log(__name__, f"Auto-download top pick: {release_name} (Score: {match_score})")

            # Download subtitle
            download_data = provider.download_subtitle({"file_id": file_id})
            content = download_data.get("content")
            if not content:
                log(__name__, "Downloaded subtitle content is empty")
                return

            # Save subtitle file to Kodi temporary directory
            temp_dir = xbmcvfs.translatePath("special://temp/")
            sub_filename = f"os_auto_{file_id}.srt"
            sub_path = os.path.join(temp_dir, sub_filename)

            with open(sub_path, "wb") as f:
                f.write(content)

            # Apply subtitle to current video player
            self.setSubtitles(sub_path)
            log(__name__, f"✅ Successfully applied auto-downloaded subtitle: {sub_path}")

            # Notify user if enabled
            if self.auto_download_notify:
                icon_path = xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("path"), "resources", "media", "os_logo_512x512.png"))
                xbmcgui.Dialog().notification(__addon_name__, f"Auto-loaded: {release_name[:35]}", icon_path, 3500)

            # Record active session for optional post-playback rating
            total_time = self.getTotalTime() if hasattr(self, "getTotalTime") else 0
            self.active_session = {
                "file_id": file_id,
                "subtitle_id": sub_id,
                "release": release_name,
                "title": media_data.get("query") or video_filename,
                "start_time": time.time(),
                "total_time": total_time
            }

        except Exception as e:
            log(__name__, f"Error in auto-download execution: {e}")

    def _handle_playback_ended(self, natural_end=False):
        if not self.prompt_rating_enabled or not self.active_session:
            self.active_session = None
            return

        session = dict(self.active_session)
        self.active_session = None

        def prompt_and_vote():
            try:
                # If natural end or watched sufficient duration
                elapsed = time.time() - session.get("start_time", 0)
                total = session.get("total_time", 0)
                
                # Check if watched at least 3 minutes and > 30% of media (or finished naturally)
                if not natural_end and total > 0 and (elapsed / total) < 0.3:
                    log(__name__, "Watched duration too short for rating prompt")
                    return

                dialog = xbmcgui.Dialog()
                title = session.get("title", "Video")
                release = session.get("release", "Subtitle")

                msg = (
                    f"How was the subtitle synchronization for:\n"
                    f"\"{title}\"?\n\n"
                    f"• Release: {release[:40]}\n\n"
                    f"Did the subtitles sync well?"
                )

                vote_in_sync = dialog.yesno(__addon_name__, msg, yeslabel="👍 Yes (In Sync)", nolabel="👎 No (Out of Sync)")
                
                score = 5 if vote_in_sync else 1
                api_key = __addon__.getSetting("APIKey")
                username = __addon__.getSetting("OSuser")
                password = __addon__.getSetting("OSpass")
                
                provider = OpenSubtitlesProvider(api_key, username, password)
                success = provider.vote_subtitle(session["file_id"], score)

                if success:
                    icon_path = xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("path"), "resources", "media", "os_logo_512x512.png"))
                    dialog.notification(__addon_name__, "Thank you for your rating!", icon_path, 3000)

            except Exception as e:
                log(__name__, f"Error during post-playback rating: {e}")

        # Run voting prompt in background thread so Kodi UI doesn't hang
        threading.Thread(target=prompt_and_vote, daemon=True).start()


def run_service():
    """Main entrypoint for xbmc.service background monitor."""
    player = OpenSubtitlesPlayer()
    monitor = OpenSubtitlesMonitor(player)
    player.monitor = monitor

    log(__name__, "OpenSubtitles.com Background Monitor Service started")

    # Launch non-blocking background account status check on startup
    threading.Thread(target=check_and_refresh_account_status, daemon=True).start()

    last_refresh_check = time.time()

    # Non-blocking main loop with zero shutdown delay
    while not monitor.abortRequested():
        if monitor.waitForAbort(1):
            break

        # Check every 6 hours if account needs background refresh
        now = time.time()
        if now - last_refresh_check > 21600:
            last_refresh_check = now
            threading.Thread(target=check_and_refresh_account_status, daemon=True).start()

    log(__name__, "OpenSubtitles.com Background Monitor Service stopped gracefully")


if __name__ == "__main__":
    run_service()
