
from typing import Union
import json
import hashlib

from requests import Session, ConnectionError, HTTPError, ReadTimeout, Timeout, RequestException

from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
from resources.lib.osclient.model.request.download import OpenSubtitlesDownloadRequest

'''local kodi module imports. replace by any other exception, cache, log provider'''
from resources.lib.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError, \
    ServiceUnavailable, TooManyRequests, BadUsernameError
from resources.lib.cache import Cache, sync_cache_stats_setting
from resources.lib.utilities import log, get_user_agent, get_install_origin, __addon__

API_URL = "https://api.opensubtitles.com/api/v1/"
API_LOGIN = "login"
API_SUBTITLES = "subtitles"
API_DOWNLOAD = "download"
API_USER_INFO = "infos/user"
API_FEATURES = "features"
API_GUESSIT = "utilities/guessit"

# A feature's type, parent and episode numbers never change, so this can be cached hard.
FEATURE_CACHE_TTL = 60 * 60 * 24 * 30
GUESSIT_CACHE_TTL = 60 * 60 * 24 * 30


CONTENT_TYPE = "application/json"
REQUEST_TIMEOUT = 30

class_lookup = {"OpenSubtitlesSubtitlesRequest": OpenSubtitlesSubtitlesRequest,
                "OpenSubtitlesDownloadRequest": OpenSubtitlesDownloadRequest}


# TODO implement search for features, logout, infos, guessit. Response(-s) objects

# Replace with any other log implementation outside fo module/Kodi
def logging(msg):
    return log(__name__, msg)


def query_to_params(query, _type):
    logging("type: ")
    logging(type(query))
    logging("query: ")
    logging(query)
    if type(query) is dict:
        try:
            request = class_lookup[_type](**query)
        except ValueError as e:
            raise ValueError(f"Invalid request data provided: {e}")
    elif isinstance(query, class_lookup.get(_type, tuple(class_lookup.values()))):
        request = query
    else:
        raise ValueError("Invalid request data provided. Invalid query type")

    logging("request vars: ")
    logging(vars(request))
    params = request.request_params()
    logging("params: ")
    logging(params)
    return params


class OpenSubtitlesProvider:

    def __init__(self, api_key, username, password):

       # if not all((username, password)):
       #     raise ConfigurationError("Username and password must be specified")

        if not api_key:
            raise ConfigurationError("Api_key must be specified")

        self.api_key = api_key
        self.username = username
        self.password = password

        if not self.username or not self.password:
            logging(f"Credentials incomplete: username set: {bool(self.username)}, password set: {bool(self.password)}")

        self.request_headers = {"Api-Key": self.api_key,
                                "User-Agent": get_user_agent(),
                                # install channel for server-side distribution stats:
                                # repository id, 'zip' (manual install) or 'unknown'
                                "X-Kodi-Origin-Repo": get_install_origin(),
                                "Content-Type": CONTENT_TYPE, "Accept": CONTENT_TYPE}

        self.session = Session()
        self.session.headers = self.request_headers

        # Use any other cache outside of module/Kodi
        self.cache = Cache(key_prefix="os_com")

    # make login request. Sets auth token
    def login(self):

        # build login request
        login_url = API_URL + API_LOGIN
        login_body = {"username": self.username, "password": self.password}

        logging(f"Login attempt to: {login_url}")

        try:
            r = self.session.post(login_url, json=login_body, allow_redirects=False, timeout=REQUEST_TIMEOUT)
            # Never log the login response headers or body: the body carries the JWT token.
            logging(f"Login response status: {r.status_code}")

            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout) as e:
            # A DNS/connect/read failure carries no HTTP response, so there is no status
            # code to report - reading one here raised AttributeError inside the handler
            # instead of surfacing the intended "service unavailable" message.
            logging(f"Connection error during login: {e}")
            raise ServiceUnavailable(f"Connection error: {e!r}")
        except HTTPError as e:
            status_code = e.response.status_code
            logging(f"HTTP error during login: {status_code}")


            if status_code == 401:
                raise AuthenticationError(f"Login failed (401 Unauthorized): Invalid username or password.")
            elif status_code == 400:
                raise BadUsernameError(f"Login failed (400 Bad Request): Make sure to enter your username and not your email.")
            elif status_code == 429:
                raise TooManyRequests("Rate limit reached (429 Too Many Requests). Please wait a moment.")
            elif 500 <= status_code <= 599:
                raise ServiceUnavailable(f"Server error ({status_code}): OpenSubtitles.com is currently experiencing issues.")
            else:
                raise ProviderError(f"HTTP Error {status_code} during login.")
        else:
            try:
                response_json = r.json()
                self.user_token = response_json["token"]
                logging("Login successful, token received")
            except (ValueError, KeyError) as e:
                logging(f"Failed to parse login response JSON: {e!r}")
                raise ValueError("Invalid JSON returned by provider")

    def get_user_info(self):
        user_info_url = API_URL + API_USER_INFO
        auth_headers = {"Authorization": "Bearer " + self.user_token}

        logging(f"Fetching user info from: {user_info_url}")

        try:
            r = self.session.get(user_info_url, headers=auth_headers, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout) as e:
            raise ServiceUnavailable(f"Connection error: {e!r}")
        except HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AuthenticationError(f"Authentication failed (401 Unauthorized).")
            elif status_code == 429:
                raise TooManyRequests("Rate limit reached (429 Too Many Requests).")
            elif 500 <= status_code <= 599:
                raise ServiceUnavailable(f"Server error ({status_code}): OpenSubtitles.com is currently unavailable.")
            else:
                raise ProviderError(f"HTTP Error {status_code} fetching user info.")

        try:
            return r.json()["data"]
        except (ValueError, KeyError):
            raise ProviderError("Invalid JSON returned by provider")

    def get_feature_info(self, imdb_id=None, tmdb_id=None):
        """Ask OS.com what an id actually refers to: a Movie, a Tvshow or a single Episode.

        Video add-ons hand Kodi either a show's id or an episode's id in the same field and
        nothing on the device distinguishes them (issue #40). This does, and for an episode
        it also returns parent_imdb_id plus the real season/episode numbers.

        Returns the feature's attributes, or None if OS.com does not know the id.
        """
        if imdb_id:
            params = {"imdb_id": imdb_id}
            cache_key = f"feature_imdb_{imdb_id}"
        elif tmdb_id:
            params = {"tmdb_id": tmdb_id}
            cache_key = f"feature_tmdb_{tmdb_id}"
        else:
            return None

        cached = self.cache.get(cache_key)
        if cached is not None:
            logging(f"CACHE HIT: feature info for {params}")
            return cached or None

        try:
            r = self.session.get(API_URL + API_FEATURES, params=params, timeout=REQUEST_TIMEOUT)
            logging(f"Feature lookup URL: {r.url} -> {r.status_code}")
            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout) as e:
            raise ServiceUnavailable(f"Connection error: {e!r}")
        except HTTPError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise TooManyRequests()
            raise ProviderError(f"Bad status code on feature lookup: {status_code}")

        try:
            data = r.json().get("data") or []
        except ValueError:
            raise ProviderError("Invalid JSON returned by provider")

        attributes = data[0].get("attributes") if data else None
        # cache misses too, as {}, so an unknown id is not looked up again every search
        self.cache.set(cache_key, attributes or {}, expires=FEATURE_CACHE_TTL)
        logging(f"Feature lookup {params} -> {attributes.get('feature_type') if attributes else 'unknown'}")
        return attributes

    def guessit(self, filename: str) -> dict:
        """Parse video filename using the /api/v1/utilities/guessit endpoint with caching."""
        if not filename:
            return None

        clean_filename = filename.strip()
        cache_key = f"guessit_{hashlib.sha256(clean_filename.encode('utf-8')).hexdigest()}"

        cached = self.cache.get(cache_key)
        if cached is not None:
            logging(f"CACHE HIT: guessit for {clean_filename}")
            return cached or None

        params = {"filename": clean_filename}
        try:
            r = self.session.get(API_URL + API_GUESSIT, params=params, timeout=REQUEST_TIMEOUT)
            logging(f"Guessit lookup URL: {r.url} -> {r.status_code}")
            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout) as e:
            logging(f"Guessit connection error: {e}")
            return None
        except HTTPError as e:
            logging(f"Guessit HTTP error: {e.response.status_code}")
            return None

        try:
            data = r.json()
        except ValueError:
            logging("Invalid JSON returned by guessit endpoint")
            return None

        self.cache.set(cache_key, data or {}, expires=GUESSIT_CACHE_TTL)
        sync_cache_stats_setting()
        logging(f"Guessit parsed: {data.get('title')} ({data.get('year')}) type={data.get('type')}")
        return data or None

    @property
    def user_token(self):
        return self.cache.get(key="user_token")

    @user_token.setter
    def user_token(self, value):
        # The API's JWT is valid for ~24h server-side; cache it for less than that so a
        # long-running device re-logins instead of presenting an expired token.
        self.cache.set(key="user_token", value=value, expires=60 * 60 * 20)

    def search_subtitles(self, query: Union[dict, OpenSubtitlesSubtitlesRequest]):

        params = query_to_params(query, 'OpenSubtitlesSubtitlesRequest')

        if not len(params):
            raise ValueError("Invalid subtitle search data provided. Empty Object built")

        # --- [START] Cache Config (Added) ---
        # Get duration from settings (default 5 minutes)
        try:
            # We access __addon__ directly since we imported it from utilities
            cache_setting = __addon__.getSetting("search_cache_duration")
            
            # If setting is empty or 0, we treat it as disabled
            if not cache_setting:
                cache_ttl = 0 # Default if undefined
            else:
                cache_ttl = int(float(cache_setting)) * 60 # Convert minutes to seconds
        except (ValueError, TypeError) as e:
            logging(f"Error reading cache setting: {e}")
            cache_ttl = 0

        # If user sets duration to 0, we disable caching
        use_cache = cache_ttl > 0
        # --- [END] Cache Config ---

        # --- [START] Cache Check (Added) ---
        cache_key = None
        if use_cache:
            try:
                # Create unique cache key from params (non-cryptographic, for cache keying only)
                params_str = json.dumps(params, sort_keys=True)
                cache_key = hashlib.sha256(params_str.encode('utf-8')).hexdigest()
                
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    logging(f"CACHE HIT: Returning cached subtitles for key {cache_key} (TTL: {cache_ttl}s)")
                    return cached_result
            except Exception as e:
                logging(f"Cache check failed: {e}")
        # --- [END] Cache Check ---

        logging(f"User token cached: {bool(self.user_token)}")

        try:
            # build query request
            subtitles_url = API_URL + API_SUBTITLES
            logging(f"Search request params: {params}")

            # Never log request or response headers: they carry the Api-Key (and would
            # carry the Authorization token) - users paste debug logs to public forums.
            r = self.session.get(subtitles_url, params=params, timeout=REQUEST_TIMEOUT)
            logging(f"Search response: {r.url} -> {r.status_code}")

            r.raise_for_status()
        except (ConnectionError, Timeout, ReadTimeout) as e:
            logging(f"Connection error during search: {e}")
            raise ServiceUnavailable(f"Connection error: {e!r}")
        except HTTPError as e:
            status_code = e.response.status_code
            logging(f"HTTP error during subtitle search: {e}")

            # Log the error response body for debugging (no secrets on this endpoint)
            try:
                logging(f"Search error response body: {e.response.text}")
            except Exception:
                logging("Failed to get search error response text")

            if status_code == 401:
                logging("401 error - authentication required. Checking if login was attempted...")
                raise ProviderError(f"Authentication failed during search (401 Unauthorized)")
            elif status_code == 429:
                raise TooManyRequests("Rate limit reached (429 Too Many Requests).")
            elif 500 <= status_code <= 599:
                raise ServiceUnavailable(f"Server error ({status_code}): OpenSubtitles.com is currently experiencing issues.")
            else:
                raise ProviderError(f"HTTP Error {status_code} on subtitle search.")

        try:
            result = r.json()
            logging(f"Search successful response JSON keys: {list(result.keys()) if result else None}")
            if "data" not in result:
                raise ValueError
        except ValueError as e:
            logging(f"Failed to parse search response JSON: {e}")
            raise ProviderError("Invalid JSON returned by provider")
        else:
            logging(f"Query returned {len(result['data'])} subtitles")

        if len(result["data"]):
            # --- [START] Cache Save (Added) ---
            if use_cache and cache_key:
                try:
                    logging(f"CACHE SAVE: Storing results for {cache_key} (expires in {cache_ttl}s)")
                    self.cache.set(cache_key, result["data"], expires=cache_ttl)
                    sync_cache_stats_setting()
                except Exception as e:
                    logging(f"Cache save failed: {e}")
            # --- [END] Cache Save ---

            return result["data"]

        return None

#   def download_subtitle(self, query: Union[dict, OpenSubtitlesDownloadRequest]):
#       if self.user_token is None:
#           logging("No cached token, we'll try to login again.")
#           try:
#               self.login()
#           except AuthenticationError as e:
#               logging("Unable to authenticate.")
#               raise AuthenticationError("Unable to authenticate.")
#           except (ServiceUnavailable, TooManyRequests, ProviderError, ValueError) as e:
#               logging("Unable to obtain an authentication token.")
#               raise ProviderError(f"Unable to obtain an authentication token: {e}")
#       if self.user_token == "":
#           logging("Unable to obtain an authentication token.")
#           #raise ProviderError("Unable to obtain an authentication token")
        
    def download_subtitle(self, query: Union[dict, OpenSubtitlesDownloadRequest]):
        if self.user_token is None and self.username and self.password:
            logging("No cached token, we'll try to login again.")
            try:
                self.login()
            except AuthenticationError as e:
                logging("Unable to authenticate.")
                raise AuthenticationError("Unable to authenticate.")
            except BadUsernameError as e:
                logging("Bad username, email instead of useername.")
                raise BadUsernameError("Bad username. Email instead of username. ")
            except (ServiceUnavailable, TooManyRequests, ProviderError, ValueError) as e:
                logging("Unable to obtain an authentication token.")
                raise ProviderError(f"Unable to obtain an authentication token: {e}")
        elif self.user_token is None:
            logging("No cached token, but username or password is missing. Proceeding with free downloads.")
        if self.user_token == "":
            logging("Unable to obtain an authentication token.")

        params = query_to_params(query, "OpenSubtitlesDownloadRequest")

        logging(f"Downloading subtitle {params['file_id']!r} ")

        # build download request
        download_url = API_URL + API_DOWNLOAD
        download_params = {"file_id": params["file_id"], "sub_format": "srt"}

        def _post_download():
            headers = {}
            if self.user_token:
                headers = {"Authorization": "Bearer " + self.user_token}
            resp = self.session.post(download_url, headers=headers, json=download_params,
                                     timeout=REQUEST_TIMEOUT)
            logging(f"Download response: {resp.url} -> {resp.status_code}")
            resp.raise_for_status()
            return resp

        try:
            try:
                r = _post_download()
            except HTTPError as e:
                # A cached token outlives its server-side validity (the JWT expires long
                # before the cache entry does). On 401 with credentials available, refresh
                # the token once and retry instead of surfacing "login failed".
                if e.response is not None and e.response.status_code == 401 and self.username and self.password:
                    logging("Cached token rejected (401), re-logging in and retrying download")
                    self.login()
                    r = _post_download()
                else:
                    raise
        except (ConnectionError, Timeout, ReadTimeout) as e:
            logging(f"Connection error during download: {e}")
            raise ServiceUnavailable(f"Connection error: {e!r}")
        except HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AuthenticationError(f"Login failed: {e.response.reason}")
            elif status_code == 429:
                raise TooManyRequests()
            elif status_code == 406:
                raise DownloadLimitExceeded(f"Daily download limit reached: {e.response.reason}")
            elif status_code == 503:
                raise ProviderError(e)
            else:
                raise ProviderError(f"Bad status code on download: {status_code}")

        try:
            subtitle = r.json()
            download_link = subtitle["link"]
        except (ValueError, KeyError):
            raise ProviderError("Invalid JSON returned by provider")
        else:
            try:
                res = self.session.get(download_link, timeout=REQUEST_TIMEOUT)
                res.raise_for_status()
            except HTTPError as e:
                # exception reprs embed the URL; the download link is one-time and
                # quota-bearing, so report only the status
                raise ServiceUnavailable(
                    f"Could not fetch subtitle file: HTTP {e.response.status_code if e.response is not None else 'error'}")
            except (ConnectionError, Timeout, ReadTimeout):
                raise ServiceUnavailable("Could not fetch subtitle file: connection error")

            subtitle["content"] = res.content

            if not subtitle["content"]:
                # do not log the download link itself - it is a one-time quota-bearing URL
                logging(f"Empty subtitle content for file_id {params['file_id']!r}")

        return subtitle
