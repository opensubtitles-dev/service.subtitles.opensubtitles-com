
import os
import re
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
    ServiceUnavailable, TooManyRequests, BadUsernameError, AICreditsExhausted
from resources.lib.file_operations import get_file_data
from resources.lib.matcher import rank_subtitles, get_match_display_tag, is_on_demand_translation
from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.utilities import get_params, log, error, redact_path, TEMP_MAX_AGE_SECONDS

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__scriptid__ = __addon__.getAddonInfo("id")

__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, "temp", ""))


# Entries younger than TEMP_MAX_AGE_SECONDS (shared via utilities with the
# Clear Cache script) survive cleanup: overlapping invocations (manual search
# during an auto-download, quick re-searches) must not delete each other's
# freshly written subtitle out from under Kodi.


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
                    log(__name__, f"Failed to clean temp file {entry_path}: {type(err).__name__}")
        else:
            os.makedirs(__temp__, exist_ok=True)
    except Exception as e:
        log(__name__, f"Temp directory initialization error: {type(e).__name__}")


# Run initial cleanup on load
clean_temp_directory()


def unique_subtitle_path(dir_path, language, sub_format):
    """Invocation-unique temp path for a downloaded subtitle.

    Kodi runs add-on scripts as sub-interpreters inside ONE process, so a PID
    would be identical for overlapping invocations - a uuid keeps each
    download's temp and destination paths private to its own invocation
    (docs/kodi_api_internals.md gotcha 17).
    """
    return os.path.join(dir_path, f"TempSubtitle.{uuid.uuid4().hex[:8]}.{language}.{sub_format}")


# ---------------------------------------------------------------------------
# Glyph rendering test harness (enabled by the test_flag_interceptor setting)
#
# Kodi's default fonts carry no emoji and only part of the symbol blocks, so any
# glyph used in a list label has to be seen on screen before it ships. Each row
# below prints its glyphs next to their codepoints, so a blank rectangle names
# the character that failed. Rows render in this order: OK first (a known-good
# baseline to judge a font or skin change against), TRY next (untested), FAIL
# last (already known bad - kept so a different font can be re-checked).
#
# Confirmed results belong in docs/kodi_ui_font_compatibility.md.
# Format: (tier tag, Kodi color, [(glyph, codepoint), ...])
# ---------------------------------------------------------------------------
GLYPH_TEST_ROWS = [
    # -- Confirmed rendering (Estuary, Default fonts) -----------------------
    ("OK", "green", [("√", "221A"), ("★", "2605"), ("☆", "2606"), ("●", "25CF"), ("○", "25CB")]),
    ("OK", "green", [("■", "25A0"), ("▪", "25AA"), ("▫", "25AB"), ("▬", "25AC"), ("▲", "25B2"), ("▼", "25BC")]),
    ("OK", "green", [("►", "25BA"), ("◄", "25C4"), ("◘", "25D8"), ("◙", "25D9"), ("•", "2022")]),
    ("OK", "green", [("←", "2190"), ("↑", "2191"), ("→", "2192"), ("↓", "2193"), ("↔", "2194")]),
    ("OK", "green", [("│", "2502"), ("─", "2500"), ("═", "2550"), ("║", "2551"), ("‖", "2016"), ("¦", "00A6")]),
    ("OK", "green", [("░", "2591"), ("▒", "2592"), ("▓", "2593"), ("█", "2588"), ("▌", "258C")]),
    ("OK", "green", [("»", "00BB"), ("‹", "2039"), ("›", "203A"), ("…", "2026"), ("°", "00B0")]),
    ("OK", "green", [("†", "2020"), ("‡", "2021"), ("‰", "2030"), ("¶", "00B6"), ("§", "00A7"), ("¤", "00A4")]),
    ("OK", "green", [("∞", "221E"), ("≈", "2248"), ("≠", "2260"), ("±", "00B1"), ("×", "00D7"), ("÷", "00F7")]),
    ("OK", "green", [("¬", "00AC"), ("′", "2032"), ("″", "2033"), ("™", "2122"), ("©", "00A9")]),
    ("OK", "green", [("€", "20AC"), ("£", "00A3"), ("¥", "00A5"), ("¢", "00A2")]),

    # -- Untested candidates ------------------------------------------------
    ("TRY", "white", [("①", "2460"), ("②", "2461"), ("ⓘ", "24D8"), ("Ⓐ", "24B6"), ("⑴", "2474")]),
    ("TRY", "white", [("–", "2013"), ("—", "2014"), ("‾", "203E"), ("«", "00AB"), ("„", "201E")]),
    ("TRY", "white", [("¹", "00B9"), ("²", "00B2"), ("³", "00B3"), ("½", "00BD"), ("¼", "00BC"), ("¾", "00BE")]),
    # WGL4 symbols - present in many desktop TTFs, so plausible even though the rest of
    # Misc Symbols failed. Card suits and notes would be useful for genre / audio marks.
    ("TRY", "white", [("☺", "263A"), ("☻", "263B"), ("☼", "263C"), ("☐", "2610"), ("⌂", "2302")]),
    ("TRY", "white", [("♠", "2660"), ("♣", "2663"), ("♥", "2665"), ("♦", "2666"), ("♪", "266A"), ("♫", "266B")]),
    ("TRY", "white", [("♀", "2640"), ("♂", "2642"), ("µ", "00B5"), ("∙", "2219"), ("⌐", "2310"), ("⌀", "2300")]),
    ("TRY", "cyan", [("⇐", "21D0"), ("⇑", "21D1"), ("⇓", "21D3"), ("⇔", "21D4"), ("↕", "2195"), ("↺", "21BA")]),
    ("TRY", "cyan", [("∆", "2206"), ("∑", "2211"), ("∏", "220F"), ("∫", "222B"), ("≤", "2264"), ("≥", "2265")]),
    # Timing and playback marks - the semantics we would most like for sync / duration.
    ("TRY", "cyan", [("⌛", "231B"), ("⌚", "231A"), ("⏱", "23F1"), ("⏳", "23F3"), ("⏩", "23E9"), ("⏸", "23F8")]),

    # -- Known failures, kept for re-testing under other fonts / skins ------
    ("FAIL", "red", [("✓", "2713"), ("✔", "2714"), ("☑", "2611"), ("✗", "2717"), ("✘", "2718")]),
    ("FAIL", "red", [("✕", "2715"), ("✖", "2716"), ("☒", "2612"), ("⚠", "26A0"), ("⚡", "26A1")]),
    ("FAIL", "red", [("✦", "2726"), ("✪", "272A"), ("❖", "2756"), ("▶", "25B6"), ("◆", "25C6")]),
    ("FAIL", "red", [("⇒", "21D2"), ("┃", "2503"), ("┆", "2506")]),
    # More of the same blocks: every one of these is the icon somebody eventually asks
    # for, so they stay on screen as a standing answer rather than a memory of one.
    ("FAIL", "red", [("☓", "2613"), ("✚", "271A"), ("✜", "271C"), ("✝", "271D"), ("✤", "2724")]),
    ("FAIL", "red", [("➜", "279C"), ("➤", "27A4"), ("➡", "27A1"), ("✈", "2708"), ("✉", "2709"), ("✍", "270D")]),
    ("FAIL", "red", [("⚑", "2691"), ("⚐", "2690"), ("⚓", "2693"), ("⚔", "2694"), ("⚙", "2699"), ("⛔", "26D4")]),
    # Emoji do not just go missing: they break the [COLOR] markup around them, so the
    # tag leaks into the label as literal text. Never put one in an on-screen string.
    ("FAIL", "red", [("✅", "2705"), ("❌", "274C"), ("❎", "274E"), ("❗", "2757"), ("❓", "2753")]),
    ("FAIL", "red", [("🤖", "1F916"), ("⭐", "2B50"), ("👍", "1F44D"), ("🔒", "1F512")]),
    ("FAIL", "red", [("🎬", "1F3AC"), ("🔥", "1F525"), ("👂", "1F442"), ("🏆", "1F3C6"), ("🎯", "1F3AF")]),
]


# Real-world subtitle titles are not ASCII. Each entry renders as one list row so a
# script that cannot be drawn - or is drawn backwards, as RTL text is without a
# bi-directional shaper - shows up here instead of in a user's search results.
CHARSET_TEST_ROWS = [
    ("Latin diacritics", "Film.2024.Slovenske.a.Ceske.ľščťžýáíéôäňĎĹŔ.Größe.Français.Español.Português"),
    ("Polish Hungarian Turkish", "Film.2024.Ąćęłńóśźż.Őőűű.İıĞğŞşÇç"),
    ("Cyrillic", "Фильм.2024.Русские.Субтитры.Проверено.Ґїєњ"),
    ("Greek", "Ταινία.2024.Ελληνικοί.Υπότιτλοι"),
    ("Hebrew RTL", "סרט.2024.כתוביות.בעברית"),
    ("Arabic RTL", "فيلم.2024.ترجمة.عربية"),
    ("Chinese", "电影.2024.简体中文字幕.繁體中文字幕"),
    ("Japanese", "映画.2024.日本語字幕.カタカナ.ひらがな.漢字"),
    ("Korean", "영화.2024.한국어자막"),
    ("Thai", "ภาพยนตร์.2024.คำบรรยายไทย"),
    ("Vietnamese", "Phim.2024.Phụ.đề.tiếng.Việt.Chuẩn"),
]


def _mock_subtitle(sub_id, language, release, file_id, title="Movie 2024", ratings=8.0,
                   from_trusted=False, moviehash_match=False, hearing_impaired=False,
                   ai_translated=False, machine_translated=False, foreign_parts_only=False):
    """One synthetic search result in the shape the provider returns."""
    return {
        "id": sub_id,
        "attributes": {
            "language": language,
            "release": release,
            "ratings": ratings,
            "votes": 100,
            "download_count": 1000,
            "from_trusted": from_trusted,
            "moviehash_match": moviehash_match,
            "hearing_impaired": hearing_impaired,
            "ai_translated": ai_translated,
            "machine_translated": machine_translated,
            "foreign_parts_only": foreign_parts_only,
            "hd": True,
            "files": [{"file_id": file_id}],
            "feature_details": {"title": title, "movie_name": title},
        },
    }


class SubtitleDownloader:

    def __init__(self):

        self.api_key = __addon__.getSetting("APIKey")
        self.username = __addon__.getSetting("OSuser")
        self.password = __addon__.getSetting("OSpass")

        self.sub_format = "srt"
        self.handle = int(sys.argv[1])
        self.params = get_params()

        # Never log raw sys.argv: a calling video add-on can embed stream
        # tokens or credentials in its plugin URL / query arguments, and Kodi
        # debug logs are exactly what users paste on public forums. Log only
        # a whitelist of known-safe parameters instead.
        safe_keys = ("action", "languages", "preferredlanguage", "id")
        safe_params = {k: self.params[k] for k in safe_keys if k in self.params}
        log(__name__, f"invoked: handle={self.handle} params={safe_params}")
        self.query = {}
        self.subtitles = {}
        self.file = {}

        try:
            self.open_subtitles = OpenSubtitlesProvider(self.api_key, self.username, self.password)
        except ConfigurationError as e:
            # The user has seen the dialog; leave a None provider so
            # handle_action ends the listing cleanly instead of a later
            # AttributeError mid-search.
            error(__name__, 32002)
            self.open_subtitles = None

    def handle_action(self):
        if self.open_subtitles is None:
            log(__name__, "No provider (missing API key) - ending listing cleanly")
            xbmcplugin.endOfDirectory(self.handle)
            return
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
        elif self.params["action"] == "transcribe":
            self.transcribe()

    def search(self, query=""):
        file_data = get_file_data(get_file_path())
        language_data = get_language_data(self.params)

        # file_original_path can be a tokened stream URL - redact before logging
        log(__name__, "file_data '%s' " % {
            k: (redact_path(v) if k == "file_original_path" else v)
            for k, v in file_data.items()})
        log(__name__, "language_data '%s' " % language_data)  # greptile-ok: filter flags and language codes only, never paths

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
            # any value can be a library file URL with a stream token - redact
            # every string that looks like one before logging
            log(__name__, "media_data '%s' " % {
                k: (redact_path(v) if isinstance(v, str) and "://" in v else v)
                for k, v in media_data.items()})

        self.query = {**media_data, **file_data, **language_data}

        # Store video filename and Guessit metadata for smart subtitle ranking
        self.video_filename = file_data.get("filename") or file_data.get("basename") or ""
        self.video_guessit = None
        if self.video_filename:
            try:
                self.video_guessit = _call_guessit_api(self.video_filename)
            except Exception as e:
                log(__name__, f"Failed to retrieve Guessit metadata for ranking: {type(e).__name__}")

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

        self._run_search_attempts(fallbacks)

        # If test flag interceptor is ON, return ONLY sample mock subtitles with flags
        test_interceptor = __addon__.getSetting("test_flag_interceptor")
        if test_interceptor and test_interceptor.lower() in ("true", "1"):
            log(__name__, "Test Flag Interceptor is ON: returning ONLY mock glyph/flag subtitles")
            self.subtitles = self._inject_test_flag_subtitles()
            # Keep the authored order so the confirmed-good glyph rows stay on top.
            self.mock_glyph_mode = True
            self.list_subtitles()
            return

        if (__addon__.getSetting("test_show_search_debug") or "").lower() in ("true", "1"):
            self.subtitles = [self._search_debug_item()] + (self.subtitles or [])

        if self.subtitles and len(self.subtitles):
            log(__name__, len(self.subtitles))
            self.list_subtitles()
        else:
            # TODO retry using guessit???
            log(__name__, "No subtitle found")

    def _search_debug_item(self):
        """Dev-only first row showing exactly what was sent to the API.

        One row per search attempt, joined with >>>. Clicking it is harmless:
        the row carries no file_id, so the download action refuses it.
        """
        SEND_KEYS = ("imdb_id", "tmdb_id", "parent_imdb_id", "parent_tmdb_id",
                     "season_number", "episode_number", "query", "year",
                     "moviehash", "languages")
        parts = []
        for attempt in getattr(self, "search_attempts", []):
            sent = {k: attempt[k] for k in SEND_KEYS if attempt.get(k)}
            parts.append(", ".join(f"{k}={v}" for k, v in sent.items()))
        text = "  >>>  ".join(parts) or "no search executed"
        return {
            "id": "search_debug",
            "_match_score": 99999.0,  # pinned on top even through ranking
            "attributes": {
                "language": "en",
                "release": f"[COLOR yellow][B]SEARCH:[/B] {text}[/COLOR]",
                "ratings": 0, "votes": 0, "download_count": 0,
                "from_trusted": False, "moviehash_match": False,
                "hearing_impaired": False, "ai_translated": False,
                "machine_translated": False, "foreign_parts_only": False,
                "files": [],
                "feature_details": {"title": "SEARCH", "movie_name": "SEARCH"},
            },
        }

    def _run_search_attempts(self, fallbacks):
        """Primary search plus the fallback ladder; records what was attempted.

        Dev toggle test_disable_query_fallback keeps an empty id/hash result
        empty instead of retrying by title - the title fallback can surface
        fuzzy wrong-feature matches.
        """
        no_fallback = (__addon__.getSetting("test_disable_query_fallback") or "").lower() in ("true", "1")
        attempts_made = [dict(self.query)]

        # A title search that misses does not come back empty - see _results_match_title.
        # Hold such results aside instead of accepting them, so the remaining attempts still
        # run; if none does better they are restored below. This can only add attempts, never
        # show the user less than before.
        expected_title = str(self.query.get("query") or "")
        held_back = None

        self.subtitles, searched_ok = self._search_subtitles(self.query)
        if self.subtitles and not self._results_match_title(self.subtitles, expected_title):
            log(__name__, f"{len(self.subtitles)} results, none matching '{expected_title}' - "
                          f"holding them and trying the remaining attempts")
            held_back, self.subtitles = self.subtitles, None

        for attempt in fallbacks:
            if self.subtitles or not searched_ok:
                break
            if no_fallback:
                log(__name__, "DEV: title-search fallback disabled, keeping empty result")
                break
            retry = {**self.query, **attempt}
            # Each attempt is a self-contained reading of the player's id.
            # Id fields it does not name must not leak in from the (possibly
            # /features-resolved) primary query - a retry carrying both the
            # attempt's id AND a leftover parent id is over-constrained and
            # can miss subtitles the attempt's reading alone would find.
            for id_field in ("imdb_id", "tmdb_id", "parent_imdb_id", "parent_tmdb_id"):
                if id_field not in attempt:
                    retry[id_field] = None
            log(__name__, f"No results, retrying with: {({k: v for k, v in attempt.items() if v})}")
            attempts_made.append(retry)
            self.subtitles, searched_ok = self._search_subtitles(retry)
            # Gate against the title THIS attempt searched for: on an id-first
            # plan the primary query is empty, and gating fallback title
            # attempts against "" would accept the first look-alike set and
            # end the chain before the no-year or filename attempt ran.
            attempt_title = str(retry.get("query") or "") or expected_title
            if self.subtitles and not self._results_match_title(self.subtitles, attempt_title):
                log(__name__, f"{len(self.subtitles)} results, still none matching "
                              f"'{attempt_title}' - holding them and continuing")
                if held_back is None:
                    held_back = self.subtitles
                self.subtitles = None

        if not self.subtitles and held_back:
            # Nothing matched the title anywhere. The look-alikes are all we have, and one of
            # them may still be right if our parsed title is the thing that is wrong.
            log(__name__, "No attempt matched the title; showing the closest results found")
            self.subtitles = held_back

        self.search_attempts = attempts_made

    def _inject_test_flag_subtitles(self):
        """Builds the glyph rendering test list shown when test_flag_interceptor is ON.

        Order on screen is the order returned here (list_subtitles() skips ranking in
        mock mode): confirmed-good glyphs first as a baseline, unknown candidates next,
        known failures last, functional badge/icon rows at the bottom.
        """
        language = (self.preferred_languages[0] if getattr(self, "preferred_languages", None) else "en")

        subtitles = []
        for index, (tag, color, glyphs) in enumerate(GLYPH_TEST_ROWS, start=1):
            cells = " ".join(f"[COLOR {color}]{glyph} {codepoint}[/COLOR]" for glyph, codepoint in glyphs)
            subtitles.append(_mock_subtitle(
                sub_id=f"mock_glyph_{index:02d}",
                language=language,
                # "GLYPH" is also the feature title so clean_feature_release_name()
                # returns the release untouched instead of prefixing a movie name.
                release=f"GLYPH {index:02d} {tag} {cells}",
                file_id=990000 + index,
                title="GLYPH",
            ))

        # Functional rows: badge pipeline, native Kodi icons, and non-ASCII charsets.
        subtitles.extend([
            _mock_subtitle(
                sub_id="mock_flags_hash_trusted",
                language=language,
                release="FLAGS Movie.2024.1080p.BluRay.x264-FLUX",
                file_id=999001,
                ratings=9.8,
                from_trusted=True,
                moviehash_match=True,
            ),
            _mock_subtitle(
                sub_id="mock_flags_ai_hi",
                language=language,
                release="FLAGS Movie.2024.1080p.WEB-DL.DDP5.1",
                file_id=999002,
                ratings=8.0,
                hearing_impaired=True,
                ai_translated=True,
            ),
            _mock_subtitle(
                sub_id="mock_flags_machine_forced",
                language=language,
                release="FLAGS Movie.2024.720p.HDTV.x264",
                file_id=999003,
                ratings=4.5,
                machine_translated=True,
                foreign_parts_only=True,
            ),
        ])

        for index, (script, sample) in enumerate(CHARSET_TEST_ROWS, start=1):
            subtitles.append(_mock_subtitle(
                sub_id=f"mock_charset_{index:02d}",
                language=language,
                title="CHARSET",
                release=f"CHARSET {script} {sample}",
                file_id=998000 + index,
                ratings=9.0,
            ))

        return subtitles

    @staticmethod
    def _title_tokens(text):
        return set(re.findall(r"[a-z0-9]+", str(text or "").lower()))

    def _results_match_title(self, results, expected_title):
        """Does any result plausibly belong to the feature we think we are playing?

        OS.com's `query` is a fuzzy token match, so a title search that misses does not
        return nothing - it returns everything sharing a word. Searching "Freaky Tales"
        (a 2024 film) with the release year 2025 excluded the real feature and produced 30
        subtitles for "7 immoral Tales", "A Tooth Fairy Tale", "Dracula: A Love Tale".
        Treating "non-empty" as "found it" stopped the fallback chain dead and showed the
        user a page of wrong films.

        Deliberately permissive - it decides only whether to *keep trying*, and a caller
        that runs out of attempts falls back to these results anyway:

          * no expected title (an id search) -> always True. An id is authoritative and
            OS.com may file the feature under a localised or alternate title.
          * an unexpected result shape -> True. Not our place to discard results here.
        """
        wanted = self._title_tokens(expected_title)
        if not wanted or not results:
            return True
        single_token = len(wanted) == 1
        for entry in results:
            try:
                attributes = entry.get("attributes") or {}
                details = attributes.get("feature_details") or {}
                title_candidates = (details.get("title"), details.get("movie_name"))
                release = attributes.get("release")
            except AttributeError:
                # one malformed entry says nothing about the rest of the set -
                # skip it; a fully malformed set returns False and is merely
                # held back, the hold-back restore still shows it if nothing
                # better turns up
                continue
            for candidate in title_candidates:
                ctokens = self._title_tokens(candidate)
                if not ctokens or not wanted <= ctokens:
                    continue
                # "Up", "It", "Her": one shared token means nothing - a
                # single-token title is confirmed only by an exactly matching
                # feature title (a trailing year token like "Up (2009)" aside)
                if single_token:
                    extras = ctokens - wanted
                    if any(not (t.isdigit() and len(t) == 4) for t in extras):
                        continue
                return True
            # a release string is token soup ("...BluRay.x265..."), so a
            # single-token title can never be confirmed by it
            if not single_token and wanted <= self._title_tokens(release):
                return True
        return False

    def _resolve_ambiguous_id(self, ambiguous):
        """Turn a player-supplied id of unknown role into a definite set of search params.

        Returns query overrides, or None when the lookup cannot answer - in which case
        search() just falls back to trying both readings in turn.
        """
        try:
            info = self.open_subtitles.get_feature_info(**ambiguous)
        except (ProviderError, ServiceUnavailable, TooManyRequests, ValueError) as e:
            log(__name__, f"Feature lookup unavailable, will try both readings instead: {type(e).__name__}")
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
            # A truthy but non-numeric parent id from /features must not raise
            # out of the search - fall through to the id-alone path instead.
            try:
                parent_imdb = int(parent_imdb) if parent_imdb else None
            except (TypeError, ValueError):
                parent_imdb = None
            # season 0 = specials, a real value - but both coordinates must be
            # cleanly numeric: a malformed one would be dropped by the request
            # model later while the parent id stayed, silently widening the
            # search to the whole show
            def _coord(value):
                s = str(value).strip() if value is not None else ""
                return s if s.isdigit() else None
            season = _coord(season)
            episode = _coord(episode)
            if parent_imdb and season is not None and episode is not None:
                log(__name__, f"/features: {ambiguous} is episode S{season}E{episode} of "
                              f"imdb {parent_imdb}")
                return {"parent_imdb_id": parent_imdb, "parent_tmdb_id": None,
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
            error(__name__, 32007, detail=str(e))
        except ServiceUnavailable as e:
            error(__name__, 32008, detail=str(e))
        except ProviderError as e:
            error(__name__, 32009, detail=str(e))
        except ValueError as e:
            error(__name__, 32001, detail=str(e))
        return None, False

    def download(self):
        if str(self.params.get("id", "")) in ("", "0"):
            # The dev search-debug row (and any malformed item) has no file
            log(__name__, "Download refused: item carries no file_id (debug row?)")
            return
        valid = 1
        try:
            self.file = self.open_subtitles.download_subtitle(
                {"file_id": self.params.get("id"), "sub_format": self.sub_format})
        except AuthenticationError as e:
            error(__name__, 32003)
            valid = 0
        except BadUsernameError as e:
            error(__name__, 32214)
            valid = 0
        except AICreditsExhausted as e:
            # Not the download quota - the AI credits balance. Own dialog text,
            # otherwise the generic limit message misleads (seen live).
            log(__name__, f"AI credits exhausted: {type(e).__name__}")
            error(__name__, 32272)
            valid = 0
        except DownloadLimitExceeded as e:
            log(__name__, f"Download limit exceeded: {type(e).__name__}")
            if self.username=="":
                error(__name__, 32006)
            else:
                error(__name__, 32004)
            valid = 0
        except TooManyRequests as e:
            error(__name__, 32007, detail=str(e))
            valid = 0
        except ServiceUnavailable as e:
            error(__name__, 32008, detail=str(e))
            valid = 0
        except ProviderError as e:
            error(__name__, 32009, detail=str(e))
            valid = 0
        except ValueError as e:
            error(__name__, 32001, detail=str(e))
            valid = 0

        clean_temp_directory()
        if valid != 1:
            # the user saw the error dialog; nothing to hand to Kodi
            return
        dir_path = __temp__

        # Invocation params are external input - a crafted or truncated URL
        # must not KeyError here. Kodi lang-code difference vs API codes:
        language_param = str(self.params.get("language") or "en").lower()
        if language_param == 'pt-pt':
            language_param = 'pt'
        elif language_param == 'pt-pb':
            language_param = 'pb'
        self.params["language"] = language_param

        subtitle_path = unique_subtitle_path(dir_path, language_param, self.sub_format)
        tmp_path = subtitle_path + ".tmp"
        log(__name__, f"download subtitle_path: {subtitle_path}")

        # Only hand Kodi a subtitle entry when the download actually succeeded; the
        # directory was wiped above, so on failure the path points at nothing.
        if self.file.get("content"):
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
                log(__name__, f"Failed to save subtitle file: {type(e).__name__}")
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
        # The dev search-debug row must survive ranking (which recomputes scores)
        # and always sit on top - detach it here, re-attach after ranking.
        debug_rows = [s for s in (self.subtitles or []) if s.get("id") == "search_debug"]
        if debug_rows:
            self.subtitles = [s for s in self.subtitles if s.get("id") != "search_debug"]

        if self.subtitles or debug_rows:
            smart_ranking_setting = __addon__.getSetting("smart_ranking")
            smart_ranking = smart_ranking_setting.lower() in ("true", "1") if smart_ranking_setting else True

            from resources.lib.data_collector import is_kodi_hearing_impaired_preferred
            hi_setting = __addon__.getSetting("hearing_impaired")
            prefer_hi = (hi_setting == "only") or (hi_setting == "include" and is_kodi_hearing_impaired_preferred()) or (not hi_setting and is_kodi_hearing_impaired_preferred())

            if getattr(self, "mock_glyph_mode", False):
                # Glyph test harness: ranking would reorder the rows by match score and
                # break the OK / TRY / FAIL grouping the list is meant to show.
                ranked_subtitles = self.subtitles
            else:
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
                    log(__name__, f"Subtitle ranking failed, falling back to unranked order: {type(e).__name__}")
                    ranked_subtitles = self.subtitles
                    smart_ranking = False

            for subtitle in debug_rows + list(ranked_subtitles):
                # One odd entry must not cost the user every other result. Ranking is
                # guarded above; this guards rendering, where a missing feature_details
                # would otherwise abort the loop and leave an empty list.
                try:
                    attributes = subtitle["attributes"]
                    language = convert_language(attributes["language"], True)
                    clean_name = clean_feature_release_name(attributes["feature_details"]["title"], attributes["release"],
                                                            attributes["feature_details"]["movie_name"])

                    # Build visual attribute badges and append at the END of the line
                    # (SDH and Hash are handled natively by Kodi dialog icons: hearing_imp and sync)
                    badges = []
                    if attributes.get("from_trusted"):
                        # √ (U+221A) is the only check-like glyph Kodi's default fonts have -
                        # real check marks are Dingbats and render as tofu (see the matrix in
                        # docs/kodi_ui_font_compatibility.md).
                        badges.append("[COLOR green][B]√[/B][/COLOR]")
                    if is_on_demand_translation(attributes):
                        # Not a real file yet: the server translates it when picked
                        # (takes ~20s+, uses AI credits) - users deserve the warning.
                        badges.append("[COLOR cyan][AI on demand][/COLOR]")
                    elif attributes.get("ai_translated"):
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
                    try:
                        rating_icon = str(int(round(float(attributes.get("ratings") or 0) / 2)))
                    except (TypeError, ValueError):
                        rating_icon = "0"
                    list_item.setArt({
                        "icon": rating_icon,
                        "thumb": get_flag(attributes["language"])})

                    is_sync = bool(attributes.get("moviehash_match"))
                    list_item.setProperty("sync", "true" if is_sync else "false")
                    list_item.setProperty("hearing_imp", "true" if attributes.get("hearing_impaired") else "false")

                    files = attributes.get("files") or [{"file_id": 0}]
                    url = f"plugin://{__scriptid__}/?action=download&id={files[0]['file_id']}&language={language}"
                    xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=list_item, isFolder=False)
                except Exception as e:
                    # log the id only - the attributes dict is large and noisy
                    log(__name__, f"Skipping unusable subtitle entry "
                                  f"{subtitle.get('id') if isinstance(subtitle, dict) else '?'}: {type(e).__name__}")
                    continue

        self._inject_transcribe_row()
        xbmcplugin.endOfDirectory(self.handle)

    def _inject_transcribe_row(self):
        """EXPERIMENTAL (expert setting ai_transcription_enabled): one extra row
        at the end of the result list that generates subtitles by AI
        transcription when picked. Sits behind action=transcribe, so selecting
        it enters the pipeline in resources/lib/transcriber.py instead of a
        normal download. Never allowed to break the listing."""
        try:
            if (__addon__.getSetting("ai_transcription_enabled") or "").lower() not in ("true", "1"):
                return
            language = (self.params.get("preferredlanguage")
                        or (self.params.get("languages") or "en").split(",")[0])
            list_item = xbmcgui.ListItem(
                label=language,
                label2="[COLOR magenta][AI][/COLOR] Generate subtitles by transcription (uses AI credits)")
            list_item.setArt({"icon": "0", "thumb": get_flag(convert_language(language, True) or "en")})
            url = f"plugin://{__scriptid__}/?action=transcribe&language={language}"
            xbmcplugin.addDirectoryItem(handle=self.handle, url=url, listitem=list_item, isFolder=False)
        except Exception as e:
            log(__name__, f"transcribe row injection failed: {type(e).__name__}")

    def transcribe(self):
        """action=transcribe - run the AI transcription pipeline and hand the
        resulting subtitle file to Kodi exactly like a download would."""
        from resources.lib import transcriber
        mock = (__addon__.getSetting("test_transcribe_mock") or "").lower() in ("true", "1")
        try:
            if not mock and not getattr(self.open_subtitles, "user_token", None):
                self.open_subtitles.login()
            file_data = get_file_data(get_file_path())
            result = transcriber.run_transcription(
                getattr(self.open_subtitles, "session", None),
                getattr(self.open_subtitles, "user_token", "") or "",
                file_data,
                self.params.get("language", "en"),
                mock=mock)
            if result and os.path.exists(str(result)):
                list_item = xbmcgui.ListItem(label=str(result))
                xbmcplugin.addDirectoryItem(handle=self.handle, url=str(result),
                                            listitem=list_item, isFolder=False)
            elif result:
                # PROPOSED contract may answer with a subtitle_id instead of a
                # ready file (cache hit) - fetch it through the normal channel.
                self.params["id"] = str(result)
                self.download()
                return
            else:
                log(__name__, "transcription returned nothing")
        except transcriber.UserCancelled:
            log(__name__, "transcription cancelled by user")
        except transcriber.NotDeployed:
            xbmcgui.Dialog().ok(__addon__.getAddonInfo("name"),
                                "AI transcription is not available on the server yet.\n"
                                "The feature is being rolled out - please try a later version.")
        except Exception as e:
            log(__name__, f"transcription failed: {type(e).__name__}")
            xbmcgui.Dialog().ok(__addon__.getAddonInfo("name"),
                                f"AI transcription failed:\n[I]{str(e)[:120]}[/I]")
        xbmcplugin.endOfDirectory(self.handle)
