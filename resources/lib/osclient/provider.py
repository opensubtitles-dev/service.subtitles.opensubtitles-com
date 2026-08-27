
from typing import Union
import json
import hashlib
import time

from requests import Session, ConnectionError, HTTPError, ReadTimeout, Timeout, RequestException

from resources.lib.osclient.model.request.subtitles import OpenSubtitlesSubtitlesRequest
from resources.lib.osclient.model.request.download import OpenSubtitlesDownloadRequest

'''local kodi module imports. replace by any other exception, cache, log provider'''
from resources.lib.exceptions import AuthenticationError, ConfigurationError, DownloadLimitExceeded, ProviderError, \
    ServiceUnavailable, TooManyRequests, BadUsernameError, AICreditsExhausted
from resources.lib.cache import Cache, sync_cache_stats_setting
from resources.lib.utilities import log, get_user_agent, get_install_origin, redact_path, __addon__

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


def _redacted_mapping(mapping):
    """Copy of a query/params mapping safe for the debug log.

    Values carrying a URL (file_original_path from a stream or plugin
    source) can embed access tokens - run each through redact_path so the
    secret-bearing query string never reaches Kodi's log.
    """
    try:
        return {k: redact_path(v) if isinstance(v, str) and "://" in v else v
                for k, v in dict(mapping).items()}
    except Exception:
        return "[unloggable mapping]"


def query_to_params(query, _type):
    logging("type: ")
    logging(type(query))
    if type(query) is dict:
        logging("query: ")
        logging(_redacted_mapping(query))
        try:
            request = class_lookup[_type](**query)
        except ValueError as e:
            raise ValueError(f"Invalid request data provided: {e}")
    elif isinstance(query, class_lookup.get(_type, tuple(class_lookup.values()))):
        request = query
    else:
        raise ValueError("Invalid request data provided. Invalid query type")

    logging("request vars: ")
    logging(_redacted_mapping(vars(request)))
    params = request.request_params()
    logging("params: ")
    logging(_redacted_mapping(params))
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
            except (ValueError, KeyError, TypeError) as e:
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
            data = r.json()["data"]
            if not isinstance(data, dict):
                raise KeyError("data is not an object")
            return data
        except (ValueError, KeyError):
            raise ProviderError("Invalid JSON returned by provider")

    def get_ai_credits(self):
        """AI credits balance for the logged-in user.

        Spec-verified: GET /ai/credits (Api-Key + Bearer) -> {"data": {"credits": <int>}}.
        Returns int or None. Never raises - credits are informative and an outage
        must not break the account refresh that calls this right after login.
        """
        try:
            r = self.session.get(API_URL + "ai/credits",
                                 headers={"Authorization": "Bearer " + self.user_token},
                                 timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            credits = r.json().get("data", {}).get("credits")
            return int(credits) if credits is not None else None
        except Exception as e:
            logging(f"AI credits unavailable: {e!r}")
            return None

    def get_ai_credit_offers(self):
        """Available AI credit packages for purchase.

        Spec-verified: GET /ai/credits/buy (Api-Key + Bearer) ->
        {"data": [{"name", "value", "discount_percent", "checkout_url"}, ...]}.
        Returns the list (possibly empty). Never raises.
        """
        try:
            r = self.session.get(API_URL + "ai/credits/buy",
                                 headers={"Authorization": "Bearer " + self.user_token},
                                 timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            offers = r.json().get("data") or []
            return [o for o in offers if o.get("checkout_url")]
        except Exception as e:
            logging(f"AI credit offers unavailable: {e!r}")
            return []

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
            body = r.json()
            # a non-object body (null, list, string) is as malformed as bad JSON
            data = body.get("data") if isinstance(body, dict) else []
            data = data or []
        except ValueError:
            raise ProviderError("Invalid JSON returned by provider")

        # Defensive shape check, closed end-to-end: /features returning valid
        # JSON with ANY malformed layer (data not a list, entry not a dict,
        # attributes truthy but not a dict) must degrade to "unknown id"
        # (None -> existing id/title fallbacks), never raise out of the search.
        attributes = (data[0].get("attributes")
                      if isinstance(data, list) and data and isinstance(data[0], dict)
                      else None)
        if not isinstance(attributes, dict):
            attributes = None
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
            if not isinstance(data, dict):
                data = None
        except ValueError:
            logging("Invalid JSON returned by guessit endpoint")
            return None

        self.cache.set(cache_key, data or {}, expires=GUESSIT_CACHE_TTL)
        sync_cache_stats_setting()
        if data:
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

        # Dev toggle: nocache=1 makes the API bypass its server-side cache, and
        # the local search cache is skipped too - otherwise it would keep
        # masking exactly the fresh responses the flag is meant to expose.
        nocache = (__addon__.getSetting("test_nocache") or "").lower() in ("true", "1")
        if nocache:
            params["nocache"] = 1
            logging("DEV nocache=1: server and local search caches bypassed")

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
        use_cache = cache_ttl > 0 and not nocache
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
            if not isinstance(result, dict):
                raise ValueError("response body is not an object")
            logging(f"Search successful response JSON keys: {list(result.keys()) if result else None}")
            # "data" must exist AND be a list - {"data": null} is valid JSON
            # and len(None) would raise TypeError past this handler
            if not isinstance(result.get("data"), list):
                raise ValueError("data missing or not a list")
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

        # AI-generated subtitles can hold the request open while the translation
        # is produced server-side - sometimes past our read timeout (observed
        # live: ~20s hold succeeded, >30s hold killed the first Czech attempt).
        # A read timeout here therefore means "still translating", not "down":
        # wait and re-POST a few times before giving up.
        ai_retries = 0
        try:
            while True:
                try:
                    try:
                        r = _post_download()
                    except HTTPError as e:
                        # A cached token outlives its server-side validity (the JWT expires
                        # long before the cache entry does). On 401 with credentials
                        # available, refresh the token once and retry.
                        if e.response is not None and e.response.status_code == 401 and self.username and self.password:
                            logging("Cached token rejected (401), re-logging in and retrying download")
                            self.login()
                            r = _post_download()
                        else:
                            raise
                except (Timeout, ReadTimeout):
                    if ai_retries < 3:
                        ai_retries += 1
                        logging(f"Download read timed out (AI translation may still be "
                                f"running), retry {ai_retries}/3 in 5s")
                        time.sleep(5)
                        continue
                    raise
                break
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

        # AI-generated subtitles: while the translation is still being produced,
        # the server REDIRECTS the classic POST to
        # GET /download/{id}?wait_for_translation=N and answers without the
        # classic {"link": ...} JSON. Give the translation time and re-POST a
        # few times before declaring failure. (Observed live 2026-08-20;
        # endpoint is new/untested server-side.)
        while "wait_for_translation" in (r.url or "") and ai_retries < 3:
            ai_retries += 1
            logging(f"AI translation still in progress (redirected to {r.url}), "
                    f"retry {ai_retries}/3 in 5s")
            time.sleep(5)
            r = _post_download()

        try:
            subtitle = r.json()
            download_link = subtitle["link"]
        except (ValueError, KeyError, TypeError):
            # Log what actually came back - decisive for debugging the new AI
            # download flow. Bodies here are progress/status payloads, never secrets.
            logging(f"Invalid download JSON from {r.url}: "
                    f"status={r.status_code}, body[:200]={r.text[:200]!r}")
            # Observed live: the server answers 200 with an EMPTY body when the
            # account has no AI credits left. Name the real problem to the user
            # instead of a generic JSON error. (Server-side fix requested.)
            if not (r.text or "").strip():
                credits = self.get_ai_credits()
                if credits == 0:
                    raise AICreditsExhausted(
                        "AI translation needs credits - your balance is 0. "
                        "Buy AI credits in the add-on settings.")
                raise ProviderError(
                    f"Empty response from download endpoint (AI credits: {credits})")
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

    def rate_subtitle(self, subtitle_id, rating: int, sync=None):
        """Submits user quality feedback for a subtitle.

        !! PROPOSED ENDPOINT - not yet in the published OpenAPI spec (verified
        2026-08-19 against stoplight open_api.json; the spec ends at /download,
        /utilities/guessit and /ai/*). Contract agreed with the API team:

            POST /api/v1/subtitles/rate     (JWT bearer required)
            { "subtitle_id": <int>,         # the subtitle entity id, NOT file_id
              "rating": <int 1..5>,         # 1 bad, 2 poor, 3 okay, 4 good, 5 excellent
              "sync": <bool, optional> }    # subtitles were in sync with the video

        Returns True on 2xx. A 404 means the server side is not deployed yet -
        logged and reported as False, never raised.
        """
        try:
            subtitle_id = int(subtitle_id)
        except (TypeError, ValueError):
            # Mock/dev sessions carry non-numeric ids; never submit those.
            logging(f"Refusing to submit rating for non-numeric subtitle_id {subtitle_id!r}")
            return False
        if not 1 <= int(rating) <= 5:
            logging(f"Refusing to submit out-of-range rating {rating}")
            return False

        if not self.logged_in:
            try:
                self.login()  # populates the JWT bearer in self.headers
            except Exception as e:
                logging(f"Login failed before submitting rating: {e}")
                return False

        url = self.base_url + "subtitles/rate"
        headers = self.headers.copy()
        payload = {"subtitle_id": int(subtitle_id), "rating": int(rating)}
        if sync is not None:
            payload["sync"] = bool(sync)

        try:
            resp = self.session.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                logging(f"Submitted rating for subtitle {subtitle_id}: {payload}")
                return True
            if resp.status_code == 404:
                logging("Rating endpoint not deployed on API yet (404) - feedback dropped")
                return False
            logging(f"Rating submission response code {resp.status_code}: {resp.text[:100]}")
            return False
        except Exception as e:
            logging(f"Error submitting subtitle rating: {e}")
            return False
