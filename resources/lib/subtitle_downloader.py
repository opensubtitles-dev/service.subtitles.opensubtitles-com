
import os
import shutil
import sys
import xbmc



import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.data_collector import get_language_data, get_media_data, get_file_path, convert_language, \
    clean_feature_release_name, get_flag
from resources.lib.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError, \
    ServiceUnavailable, TooManyRequests, BadUsernameError
from resources.lib.file_operations import get_file_data
from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.utilities import get_params, log, error

__addon__ = xbmcaddon.Addon()
__scriptid__ = __addon__.getAddonInfo("id")

__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, "temp", ""))

if xbmcvfs.exists(__temp__):
    shutil.rmtree(__temp__)
xbmcvfs.mkdirs(__temp__)


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
        if self.params["action"] == "manualsearch":
            self.search(self.params['searchstring'])
        elif self.params["action"] == "search":
            self.search()
        elif self.params["action"] == "download":
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
            # Only use basename as fallback if no query was set by media data collection
            if "basename" in file_data and not media_data.get("query"):
                media_data["query"] = file_data["basename"]
                log(__name__, f"Using basename as query fallback: {file_data['basename']}")
            elif media_data.get("query"):
                log(__name__, f"Using parsed query from media_data: {media_data['query']}")
            log(__name__, "media_data '%s' " % media_data)

        self.query = {**media_data, **file_data, **language_data}

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
            log(__name__, "XYXYXX download '%s' " % self.file)
        except AuthenticationError as e:
            error(__name__, 32003, e)
            valid = 0
        except BadUsernameError as e:
            error(__name__, 32214, e)
            valid = 0
        except DownloadLimitExceeded as e:
            log(__name__, f"XYXYXX limit excedded, username: {self.username}  {e}")
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

        #subtitle_path = os.path.join(__temp__, f"{str(uuid.uuid4())}.{self.sub_format}")
        try:    # kodi > k19
            dir_path = xbmcvfs.translatePath('special://temp/oss/')       
        except AttributeError: # kodi < k19
            dir_path = xbmc.translatePath('special://temp/oss/')

        # Kodi lang-code difference vs OS.com API langcodes return
        if self.params["language"].lower() == 'pt-pt': self.params["language"] = 'pt'
        elif self.params["language"].lower() == 'pt-pb': self.params["language"] = 'pb'

        if xbmcvfs.exists(dir_path):    # lets clean files from last usage
            dirs, files = xbmcvfs.listdir(dir_path)
            for file in files:
                xbmcvfs.delete(os.path.join(dir_path, file))
        
        if not xbmcvfs.exists(dir_path):  # lets create custom OSS sub directory if not exists
            xbmcvfs.mkdir(dir_path)

        subtitle_path = os.path.join(dir_path, "{0}.{1}.{2}".format('TempSubtitle', self.params["language"], self.sub_format))   
        
        log(__name__, "XYXYXX download subtitle_path: {}".format(subtitle_path))


        if (valid==1):
            tmp_file = open(subtitle_path, "w" + "b")
            tmp_file.write(self.file["content"])
            tmp_file.close()
        

        list_item = xbmcgui.ListItem(label=subtitle_path)
        xbmcplugin.addDirectoryItem(handle=self.handle, url=subtitle_path, listitem=list_item, isFolder=False)

        return

        """old code"""
        # subs = Download(params["ID"], params["link"], params["format"])
        # for sub in subs:
        #    listitem = xbmcgui.ListItem(label=sub)
        #    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

    def list_subtitles(self):
        """TODO rewrite using new data. do not forget Series/Episodes"""
        if self.subtitles:
            for subtitle in reversed(sorted(self.subtitles, key=lambda x: (
                    bool(x["attributes"].get("from_trusted", False)),
                    x["attributes"].get("votes", 0) or 0,
                    x["attributes"].get("ratings", 0) or 0,
                    x["attributes"].get("download_count", 0) or 0))):
                attributes = subtitle["attributes"]
                language = convert_language(attributes["language"], True)
                log(__name__, attributes)
                clean_name = clean_feature_release_name(attributes["feature_details"]["title"], attributes["release"],
                                                        attributes["feature_details"]["movie_name"])
                list_item = xbmcgui.ListItem(label=language,
                                             label2=clean_name)
                list_item.setArt({
                    "icon": str(int(round(float(attributes["ratings"]) / 2))),
                    "thumb": get_flag(attributes["language"])})
               # list_item.setArt({
               #     "icon": str(int(round(float(attributes["ratings"]) / 2))),
               #     "thumb": get_flag(language)})
               
                log(__name__, "XYXYXX download get_flag: language in url {}".format(get_flag(attributes["language"])))

                
                list_item.setProperty("sync", "true" if ("moviehash_match" in attributes and attributes["moviehash_match"]) else "false")
                list_item.setProperty("hearing_imp", "true" if attributes["hearing_impaired"] else "false")
                """TODO take care of multiple cds id&id or something"""
                #url = f"plugin://{__scriptid__}/?action=download&id={attributes['files'][0]['file_id']}"
                url = f"plugin://{__scriptid__}/?action=download&id={attributes['files'][0]['file_id']}&language={language}"    
                log(__name__, "XYXYXX download list_subtitles: language in url {url}")

                xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=list_item, isFolder=False)
        xbmcplugin.endOfDirectory(self.handle)
