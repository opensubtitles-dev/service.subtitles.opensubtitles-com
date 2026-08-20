
import os
import shutil
import sys
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


def clean_temp_directory():
    """Safely cleans stale temp files and ensures the add-on temp directory exists."""
    try:
        if os.path.exists(__temp__):
            for entry in os.listdir(__temp__):
                entry_path = os.path.join(__temp__, entry)
                try:
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

        # If test flag interceptor is ON, return ONLY sample mock subtitles with flags
        test_interceptor = __addon__.getSetting("test_flag_interceptor")
        if test_interceptor and test_interceptor.lower() in ("true", "1"):
            log(__name__, "🧪 Test Flag Interceptor is ON: returning ONLY mock flag subtitles")
            self.subtitles = self._inject_test_flag_subtitles()
            self.list_subtitles()
            return

        if self.subtitles and len(self.subtitles):
            log(__name__, len(self.subtitles))
            self.list_subtitles()
        else:
            # TODO retry using guessit???
            log(__name__, "No subtitle found")

    def _inject_test_flag_subtitles(self):
        """Injects test subtitles demonstrating all flag types, UTF-8, symbols, and formatting."""
        test_lang = (self.preferred_languages[0] if getattr(self, "preferred_languages", None) else "en")
        return [
            {
                "id": "mock_ok_checks",
                "_match_score": 10500.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.1080p.BluRay.x264 [COLOR green]✓ OK1[/COLOR] [COLOR green]✔ OK2[/COLOR] [COLOR green]☑ OK3[/COLOR] [COLOR green]√ OK4[/COLOR]",
                    "ratings": 9.8,
                    "votes": 120,
                    "download_count": 4500,
                    "from_trusted": True,
                    "moviehash_match": True,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999001}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_bad_crosses",
                "_match_score": 4500.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.1080p.BluRay.x264 [COLOR red]✗ Bad1[/COLOR] [COLOR red]✘ Bad2[/COLOR] [COLOR red]✕ Bad3[/COLOR] [COLOR red]✖ Bad4[/COLOR] [COLOR red]☒ Bad5[/COLOR]",
                    "ratings": 4.5,
                    "votes": 15,
                    "download_count": 300,
                    "from_trusted": False,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": True,
                    "foreign_parts_only": False,
                    "hd": False,
                    "files": [{"file_id": 999002}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_warnings_lightning",
                "_match_score": 4200.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.1080p.WEB-DL [COLOR yellow]⚠ Warning[/COLOR] [COLOR yellow]⚡ Sync[/COLOR] [COLOR yellow]⚡ Fast[/COLOR]",
                    "ratings": 8.0,
                    "votes": 50,
                    "download_count": 1800,
                    "from_trusted": False,
                    "moviehash_match": False,
                    "hearing_impaired": True,
                    "ai_translated": True,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999003}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_stars_ratings",
                "_match_score": 4000.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.1080p.BluRay [COLOR gold]★ 9.8[/COLOR] [COLOR gold]☆ 4/5[/COLOR] [COLOR gold]✪ Top[/COLOR] [COLOR gold]✦ HQ[/COLOR]",
                    "ratings": 9.8,
                    "votes": 250,
                    "download_count": 5200,
                    "from_trusted": True,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999004}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_dots_diamonds",
                "_match_score": 3800.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.1080p.WEB [COLOR lightblue]● Dot1[/COLOR] [COLOR lightblue]○ Dot2[/COLOR] [COLOR lightblue]• Bullet[/COLOR] [COLOR lightblue]◆ Diamond[/COLOR]",
                    "ratings": 8.5,
                    "votes": 60,
                    "download_count": 1800,
                    "from_trusted": True,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": False,
                    "foreign_parts_only": True,
                    "hd": True,
                    "files": [{"file_id": 999005}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_arrows_pointers",
                "_match_score": 3600.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.1080p.BluRay [COLOR white]► Play[/COLOR] [COLOR white]▶ Arrow[/COLOR] [COLOR white]» Next[/COLOR] [COLOR grey]│[/COLOR] [COLOR white]DTS-HD[/COLOR]",
                    "ratings": 7.5,
                    "votes": 25,
                    "download_count": 900,
                    "from_trusted": False,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": True,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999006}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_triangles_quality",
                "_match_score": 3400.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.2160p.HDR [COLOR green]▲ High[/COLOR] [COLOR red]▼ Low[/COLOR] [COLOR cyan]■ Square[/COLOR] [COLOR yellow]❖ Badge[/COLOR]",
                    "ratings": 8.0,
                    "votes": 40,
                    "download_count": 1100,
                    "from_trusted": True,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999007}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_bracket_badges",
                "_match_score": 3200.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Movie.2024.1080p.BluRay.x264-FLUX [COLOR green][✔ Trusted][/COLOR] [COLOR cyan][✦ AI][/COLOR] [COLOR gold][★ 9.5][/COLOR]",
                    "ratings": 9.5,
                    "votes": 110,
                    "download_count": 3500,
                    "from_trusted": False,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999008}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_czech_slovak_glyphs",
                "_match_score": 3000.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Film.2024.Slovenské.a.České.Znaky.ľščťžýáíéôäň [COLOR green]✔ Overené[/COLOR] [COLOR gold]★ 9.9[/COLOR]",
                    "ratings": 9.9,
                    "votes": 180,
                    "download_count": 4200,
                    "from_trusted": True,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999009}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            },
            {
                "id": "mock_cyrillic_glyphs",
                "_match_score": 2800.0,
                "attributes": {
                    "language": test_lang,
                    "release": "Фильм.2024.1080p.Русские.Субтитры.Проверено [COLOR green]✔ Проверено[/COLOR] [COLOR gold]★ 9.4[/COLOR]",
                    "ratings": 9.4,
                    "votes": 90,
                    "download_count": 2100,
                    "from_trusted": True,
                    "moviehash_match": False,
                    "hearing_impaired": False,
                    "ai_translated": False,
                    "machine_translated": False,
                    "foreign_parts_only": False,
                    "hd": True,
                    "files": [{"file_id": 999010}],
                    "feature_details": {"title": "Movie 2024", "movie_name": "Movie 2024"}
                }
            }
        ]

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

        subtitle_path = os.path.join(dir_path, f"TempSubtitle.{self.params['language']}.{self.sub_format}")
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

            ranked_subtitles = rank_subtitles(
                self.subtitles,
                getattr(self, "video_filename", ""),
                getattr(self, "video_guessit", None),
                smart_ranking=smart_ranking,
                preferred_languages=getattr(self, "preferred_languages", None),
                prefer_hearing_impaired=prefer_hi
            )

            for subtitle in ranked_subtitles:
                attributes = subtitle["attributes"]
                language = convert_language(attributes["language"], True)
                log(__name__, attributes)
                clean_name = clean_feature_release_name(attributes["feature_details"]["title"], attributes["release"],
                                                        attributes["feature_details"]["movie_name"])
                
                # Build visual attribute badges and append at the END of the line
                # (SDH and Hash are handled natively by Kodi dialog icons: hearing_imp and sync)
                badges = []
                if attributes.get("from_trusted"):
                    badges.append("[COLOR green][Trusted][/COLOR]")
                if attributes.get("ai_translated"):
                    badges.append("[COLOR cyan][AI][/COLOR]")
                elif attributes.get("machine_translated"):
                    badges.append("[COLOR orange][Machine][/COLOR]")
                if attributes.get("foreign_parts_only"):
                    badges.append("[COLOR yellow][Forced][/COLOR]")

                # Append yellow match badge to label2 (e.g. (+95), omits (Hash) since sync icon is active)
                if smart_ranking:
                    match_tag = get_match_display_tag(subtitle)
                    if match_tag:
                        badges.append(match_tag)

                if badges:
                    clean_name = f"{clean_name} {' '.join(badges)}".strip()

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

        xbmcplugin.endOfDirectory(self.handle)
