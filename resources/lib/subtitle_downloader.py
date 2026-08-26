
import os
import shutil
import sys
import time
import uuid
import xbmc



import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.data_collector import get_language_data, get_media_data, get_file_path, convert_language, \
    clean_feature_release_name, get_flag, _call_guessit_api
from resources.lib.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError, \
    ServiceUnavailable, TooManyRequests, BadUsernameError
from resources.lib.file_operations import get_file_data
from resources.lib.matcher import rank_subtitles, get_match_display_tag
from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.utilities import get_params, log, error

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__scriptid__ = __addon__.getAddonInfo("id")

__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, "temp", ""))


# Entries younger than this survive cleanup: overlapping invocations (manual
# search during an auto-download, quick re-searches) must not delete each
# other's freshly written subtitle out from under Kodi.
TEMP_MAX_AGE_SECONDS = 3600


def clean_temp_directory():
    """Removes STALE temp entries and ensures the add-on temp directory exists.

    Only entries older than TEMP_MAX_AGE_SECONDS are deleted - a concurrent
    invocation's fresh subtitle stays on disk.
    """
    try:
        if os.path.exists(__temp__):
            now = time.time()
            for entry in os.listdir(__temp__):
                entry_path = os.path.join(__temp__, entry)
                try:
                    if now - os.path.getmtime(entry_path) < TEMP_MAX_AGE_SECONDS:
                        continue
                    if os.path.isfile(entry_path) or os.path.islink(entry_path):
                        os.unlink(entry_path)
                    elif os.path.isdir(entry_path):
                        shutil.rmtree(entry_path, ignore_errors=True)
                except Exception as err:
                    log(__name__, f"Failed to clean temp file {entry_path}: {err}")
        else:
            os.makedirs(__temp__, exist_ok=True)
    except Exception as e:
        log(__name__, f"Temp directory initialization error: {e}")


# Run initial cleanup on load
clean_temp_directory()


def unique_subtitle_path(dir_path, language, sub_format):
    """Invocation-unique temp path for a downloaded subtitle.

    Kodi runs add-on scripts as sub-interpreters inside ONE process, so a PID
    would be identical for overlapping invocations - a uuid keeps each
    download's temp and destination paths private to its own invocation.
    """
    return os.path.join(dir_path, f"TempSubtitle.{uuid.uuid4().hex[:8]}.{language}.{sub_format}")


class SubtitleDownloader:

    def __init__(self):

        self.api_key = __addon__.getSetting("APIKey")
        self.username = __addon__.getSetting("OSuser")
        self.password = __addon__.getSetting("OSpass")

        log(__name__, sys.argv)

        self.sub_format = "srt"
        self.handle = int(sys.argv[1])
        self.params = get_params()
        self.query = {}
        self.subtitles = {}
        self.file = {}

        try:
            self.open_subtitles = OpenSubtitlesProvider(self.api_key, self.username, self.password)
        except ConfigurationError as e:
            error(__name__, 32002, e)

    def handle_action(self):
        log(__name__, "action '%s' called" % self.params["action"])
        version = __addon__.getAddonInfo("version")
        addon_name = __addon__.getAddonInfo("name")
        icon_path = xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("path"), "resources", "media", "os_logo_512x512.png"))

        if self.params["action"] == "manualsearch":
            self.search(self.params['searchstring'])
        elif self.params["action"] == "search":
            self.search()
        elif self.params["action"] == "download":
            xbmcgui.Dialog().notification(f"{addon_name} v{version}", "Downloading subtitle...", icon_path, 2000, False)
            self.download()

    def search(self, query=""):
        file_data = get_file_data(get_file_path())
        language_data = get_language_data(self.params)

        log(__name__, "file_data '%s' " % file_data)
        log(__name__, "language_data '%s' " % language_data)

        # if there's query passed we use it, don't try to pull media data from VideoPlayer
        if query:
            media_data = {"query": query}
        else:
            media_data = get_media_data()
            has_id = bool(media_data.get("imdb_id") or media_data.get("tmdb_id") or
                          media_data.get("parent_imdb_id") or media_data.get("parent_tmdb_id"))
            # Only use basename as fallback if no ID and no query was set by media data collection
            if not has_id and "basename" in file_data and not media_data.get("query"):
                media_data["query"] = file_data["basename"]
                log(__name__, f"Using basename as query fallback: {file_data['basename']}")
            elif media_data.get("query"):
                log(__name__, f"Using parsed query from media_data: {media_data['query']}")
            log(__name__, "media_data '%s' " % media_data)

        self.query = {**media_data, **file_data, **language_data}

        # Store video filename and Guessit metadata for smart subtitle ranking
        self.video_filename = file_data.get("filename") or file_data.get("basename") or ""
        self.video_guessit = None
        if self.video_filename:
            try:
                self.video_guessit = _call_guessit_api(self.video_filename)
            except Exception as e:
                log(__name__, f"Failed to retrieve Guessit metadata for ranking: {e}")

        # Extract ordered preferred languages for multi-language display
        from urllib.parse import unquote
        preferred_lang = self.params.get("preferredlanguage")
        raw_langs = unquote(self.params.get("languages", "")).split(",")
        self.preferred_languages = []

        if preferred_lang and preferred_lang not in ("Unknown", "Undetermined"):
            p_code = convert_language(preferred_lang)
            if p_code:
                self.preferred_languages.append(p_code.lower())

        for l in raw_langs:
            l_str = l.strip()
            if l_str:
                l_code = convert_language(l_str)
                if l_code and l_code.lower() not in self.preferred_languages:
                    self.preferred_languages.append(l_code.lower())

        # Adaptive Language Memory: promote last downloaded language to top priority
        try:
            last_dl_lang = xbmcgui.Window(10000).getProperty("os_com:last_downloaded_lang")
            if last_dl_lang and last_dl_lang.lower() in self.preferred_languages:
                self.preferred_languages.remove(last_dl_lang.lower())
                self.preferred_languages.insert(0, last_dl_lang.lower())
        except Exception:
            pass

        # Build informative on-screen search notification
        addon_name = __addon__.getAddonInfo("name")
        version = __addon__.getAddonInfo("version")
        icon_path = xbmcvfs.translatePath(os.path.join(__addon__.getAddonInfo("path"), "resources", "media", "os_logo_512x512.png"))

        search_desc = []
        if self.query.get("imdb_id"):
            search_desc.append(f"IMDb: tt{self.query['imdb_id']}")
        elif self.query.get("parent_imdb_id"):
            s = self.query.get("season_number", "")
            e = self.query.get("episode_number", "")
            search_desc.append(f"IMDb: tt{self.query['parent_imdb_id']} S{s}E{e}")
        elif self.query.get("tmdb_id"):
            search_desc.append(f"TMDb: {self.query['tmdb_id']}")
        elif self.query.get("parent_tmdb_id"):
            s = self.query.get("season_number", "")
            e = self.query.get("episode_number", "")
            search_desc.append(f"TMDb: {self.query['parent_tmdb_id']} S{s}E{e}")
        elif self.query.get("query"):
            search_desc.append(f"'{self.query['query']}'")

        langs = self.query.get("languages", "")
        if langs:
            search_desc.append(f"[{langs}]")

        notify_msg = "Searching " + " ".join(search_desc) if search_desc else "Searching subtitles..."
        xbmcgui.Dialog().notification(f"{addon_name} v{version}", notify_msg, icon_path, 2500, False)

        # get_media_data may hand us an ordered plan: when it cannot tell whether the id the
        # player gave us belongs to the show or to the episode, each reading is a separate
        # attempt. Take the first one that returns something (see issue #40).
        fallbacks = self.query.pop("search_fallbacks", None) or []

        # If we could not tell locally whether the player's id names the show or the episode,
        # ask OS.com outright before resorting to trying both readings.
        ambiguous = self.query.pop("ambiguous_player_id", None)
        if ambiguous:
            resolved = self._resolve_ambiguous_id(ambiguous)
            if resolved:
                self.query.update(resolved)

        self.subtitles, searched_ok = self._search_subtitles(self.query)

        for attempt in fallbacks:
            if self.subtitles or not searched_ok:
                break
            retry = {**self.query, **attempt}
            log(__name__, f"No results, retrying with: {({k: v for k, v in attempt.items() if v})}")
            self.subtitles, searched_ok = self._search_subtitles(retry)

        if self.subtitles and len(self.subtitles):
            log(__name__, len(self.subtitles))
            self.list_subtitles()
        else:
            # TODO retry using guessit???
            log(__name__, "No subtitle found")

    def _resolve_ambiguous_id(self, ambiguous):
        """Turn a player-supplied id of unknown role into a definite set of search params.

        Returns query overrides, or None when the lookup cannot answer - in which case
        search() just falls back to trying both readings in turn.
        """
        try:
            info = self.open_subtitles.get_feature_info(**ambiguous)
        except (ProviderError, ServiceUnavailable, TooManyRequests, ValueError) as e:
            log(__name__, f"Feature lookup unavailable, will try both readings instead: {e}")
            return None

        if not info:
            log(__name__, f"OS.com does not know {ambiguous}, will try both readings instead")
            return None

        feature_type = str(info.get("feature_type") or "").lower()

        if feature_type == "episode":
            # Best case: we get the show's id and the true season/episode, so we can search
            # the way most subtitles are actually filed, whatever Kodi reported.
            parent_imdb = info.get("parent_imdb_id")
            season = info.get("season_number")
            episode = info.get("episode_number")
            if parent_imdb and season and episode:
                log(__name__, f"/features: {ambiguous} is episode S{season}E{episode} of "
                              f"imdb {parent_imdb}")
                return {"parent_imdb_id": int(parent_imdb), "parent_tmdb_id": None,
                        "imdb_id": None, "tmdb_id": None,
                        "season_number": str(season), "episode_number": str(episode),
                        "query": ""}
            # Known to be an episode but without parent details: search the id on its own.
            log(__name__, f"/features: {ambiguous} is an episode, searching the id alone")
            return {"parent_imdb_id": None, "parent_tmdb_id": None,
                    "query": "", "season_number": None, "episode_number": None, **ambiguous}

        if feature_type == "tvshow":
            # Drop the title: with a confirmed show id it is just one more condition the
            # results have to satisfy, and a localized or mis-parsed title would exclude
            # perfectly good subtitles.
            key = "parent_imdb_id" if "imdb_id" in ambiguous else "parent_tmdb_id"
            log(__name__, f"/features: {ambiguous} is a show, pairing it with season/episode")
            return {key: next(iter(ambiguous.values())), "imdb_id": None, "tmdb_id": None,
                    "query": ""}

        if feature_type == "movie":
            log(__name__, f"/features: {ambiguous} is a movie, searching the id alone")
            return {"parent_imdb_id": None, "parent_tmdb_id": None,
                    "query": "", "season_number": None, "episode_number": None, **ambiguous}

        log(__name__, f"/features returned unexpected feature_type {feature_type!r}")
        return None

    def _search_subtitles(self, query):
        """Run one search, turning provider failures into a user-facing message.

        Returns (results, ok); ok is False when the provider errored, so the caller can
        tell "no subtitles for this query" apart from "the search never got through".
        """
        try:
            return self.open_subtitles.search_subtitles(query), True
        except TooManyRequests as e:
            error(__name__, 32007, e, detail=str(e))
        except ServiceUnavailable as e:
            error(__name__, 32008, e, detail=str(e))
        except ProviderError as e:
            error(__name__, 32009, e, detail=str(e))
        except ValueError as e:
            error(__name__, 32001, e, detail=str(e))
        return None, False

    def download(self):
        valid = 1
        try:
            self.file = self.open_subtitles.download_subtitle(
                {"file_id": self.params["id"], "sub_format": self.sub_format})
        except AuthenticationError as e:
            error(__name__, 32003, e)
            valid = 0
        except BadUsernameError as e:
            error(__name__, 32214, e)
            valid = 0
        except DownloadLimitExceeded as e:
            log(__name__, f"Download limit exceeded: {e}")
            if self.username=="":
                error(__name__, 32006, e)
            else:
                error(__name__, 32004, e)
            valid = 0
        except TooManyRequests as e:
            error(__name__, 32007, e, detail=str(e))
            valid = 0
        except ServiceUnavailable as e:
            error(__name__, 32008, e, detail=str(e))
            valid = 0
        except ProviderError as e:
            error(__name__, 32009, e, detail=str(e))
            valid = 0
        except ValueError as e:
            error(__name__, 32001, e, detail=str(e))
            valid = 0

        clean_temp_directory()
        dir_path = __temp__

        # Kodi lang-code difference vs OS.com API langcodes return
        if self.params["language"].lower() == 'pt-pt':
            self.params["language"] = 'pt'
        elif self.params["language"].lower() == 'pt-pb':
            self.params["language"] = 'pb'

        subtitle_path = unique_subtitle_path(dir_path, self.params["language"], self.sub_format)
        tmp_path = subtitle_path + ".tmp"
        log(__name__, f"download subtitle_path: {subtitle_path}")

        # Only hand Kodi a subtitle entry when the download actually succeeded; the
        # directory was wiped above, so on failure the path points at nothing.
        if valid == 1 and self.file.get("content"):
            try:
                with open(tmp_path, "wb") as tmp_file:
                    tmp_file.write(self.file["content"])

                if os.path.exists(subtitle_path):
                    try:
                        os.unlink(subtitle_path)
                    except Exception:
                        pass

                os.rename(tmp_path, subtitle_path)
            except Exception as e:
                log(__name__, f"Failed to save subtitle file: {e}")
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                return

            if self.file.get("remaining") is not None:
                from datetime import datetime
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                remaining = self.file.get("remaining")
                vip_str = "VIP" if self.username else "Free User"
                __addon__.setSetting("account_status", f"OK ({vip_str})")
                __addon__.setSetting("account_details", f"Quota: {remaining} downloads left today")
                __addon__.setSetting("account_checked_at", now_str)

            # Save downloaded language to adaptive memory
            dl_lang = self.params.get("language")
            if dl_lang:
                try:
                    norm_lang = convert_language(dl_lang) or dl_lang
                    xbmcgui.Window(10000).setProperty("os_com:last_downloaded_lang", str(norm_lang).lower())
                except Exception:
                    pass

            list_item = xbmcgui.ListItem(label=subtitle_path)
            xbmcplugin.addDirectoryItem(handle=self.handle, url=subtitle_path, listitem=list_item, isFolder=False)

        return

        """old code"""
        # subs = Download(params["ID"], params["link"], params["format"])
        # for sub in subs:
        #    listitem = xbmcgui.ListItem(label=sub)
        #    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

    def list_subtitles(self):
        if self.subtitles:
            smart_ranking_setting = __addon__.getSetting("smart_ranking")
            smart_ranking = smart_ranking_setting.lower() in ("true", "1") if smart_ranking_setting else True

            from resources.lib.data_collector import is_kodi_hearing_impaired_preferred
            hi_setting = __addon__.getSetting("hearing_impaired")
            prefer_hi = (hi_setting == "only") or (hi_setting == "include" and is_kodi_hearing_impaired_preferred()) or (not hi_setting and is_kodi_hearing_impaired_preferred())

            # Ranking is a nicety; showing the subtitles is not. If scoring trips over an
            # unexpected field type, fall back to the API's own order rather than raising
            # out of list_subtitles() - that would skip endOfDirectory() below and leave
            # the subtitle dialog hanging with nothing in it.
            try:
                ranked_subtitles = rank_subtitles(
                    self.subtitles,
                    getattr(self, "video_filename", ""),
                    getattr(self, "video_guessit", None),
                    smart_ranking=smart_ranking,
                    preferred_languages=getattr(self, "preferred_languages", None),
                    prefer_hearing_impaired=prefer_hi
                )
            except Exception as e:
                log(__name__, f"Subtitle ranking failed, falling back to unranked order: {e!r}")
                ranked_subtitles = self.subtitles
                smart_ranking = False

            for subtitle in ranked_subtitles:
                # One odd entry must not cost the user every other result. Ranking is
                # guarded above; this guards rendering, where a missing feature_details or
                # files[0] would otherwise abort the loop and leave an empty list.
                try:
                    attributes = subtitle["attributes"]
                    language = convert_language(attributes["language"], True)
                    log(__name__, attributes)
                    clean_name = clean_feature_release_name(attributes["feature_details"]["title"], attributes["release"],
                                                            attributes["feature_details"]["movie_name"])

                    # Append yellow match badge to label2 (e.g. (+95) or (Hash))
                    if smart_ranking:
                        match_tag = get_match_display_tag(subtitle)
                        if match_tag:
                            clean_name = f"{clean_name} {match_tag}".strip()

                    list_item = xbmcgui.ListItem(label=language,
                                                 label2=clean_name)
                    list_item.setArt({
                        "icon": str(int(round(float(attributes.get("ratings") or 0) / 2))),
                        "thumb": get_flag(attributes["language"])})

                    is_sync = bool(attributes.get("moviehash_match"))
                    list_item.setProperty("sync", "true" if is_sync else "false")
                    list_item.setProperty("hearing_imp", "true" if attributes.get("hearing_impaired") else "false")

                    url = f"plugin://{__scriptid__}/?action=download&id={attributes['files'][0]['file_id']}&language={language}"
                    xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=list_item, isFolder=False)
                except Exception as e:
                    # log the id only - the attributes dict is large and noisy
                    log(__name__, f"Skipping unusable subtitle entry "
                                  f"{subtitle.get('id') if isinstance(subtitle, dict) else '?'}: {e!r}")
                    continue

        xbmcplugin.endOfDirectory(self.handle)
