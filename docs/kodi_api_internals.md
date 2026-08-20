# Kodi Python API Internals — Subtitle Add-on Reference

Ground-truth reference for every Kodi API surface this add-on touches. Compiled from:
- **Kodistubs** (`romanvm/Kodistubs`, generated from Kodi's own doxygen — exact signatures)
- **Kodi C++ source** `xbmc/video/dialogs/GUIDialogSubtitles.cpp` (the definitive subtitle-plugin contract)
- Verified against Kodi Matrix (19) → Piers (22). Version annotations use `@v19`-style tags.

Read this before touching `service.py`, `service_monitor.py`, or anything that talks to the Kodi runtime.

---

## 1. The Two Extension Points

### 1a. `xbmc.subtitle.module` (`service.py`) — the search/download plugin

Kodi treats a subtitle add-on as a **plugin** invoked with a URL. Every invocation is a **fresh Python process**: no state survives between search and download except what you persist (settings, window properties, files).

**What Kodi sends** (built in `CGUIDialogSubtitles::Search()`):

```
plugin://service.subtitles.opensubtitles-com/?action=search
    &languages=<CSV of English language names, e.g. "English,Czech">
    &preferredlanguage=<one English language name>
    [&stack=1]                     # only when playing a stacked (multi-part) file
```

- `sys.argv[1]` = the integer **handle** for `xbmcplugin` calls; `sys.argv[2]` = the query string.
- **Manual search** sends `action=manualsearch&searchstring=<user text>` plus the same language params.
- `languages` comes from Kodi setting `subtitles.languages`; `preferredlanguage` from `locale.subtitlelanguage`. Two magic values are resolved by Kodi *before* we see them: "Original stream's language" → the audio stream's language name; "Interface language" → the UI language. We always receive plain English names ("Portuguese (Brazil)" style).
- **Download** is OUR url, echoed back: whatever `url=` we passed to `addDirectoryItem` for the picked result, with `action=download` appended by Kodi **only if the url has no `action` option already**. Everything the download step needs (file_id, language) must therefore be baked into the result url at search time.

**What Kodi expects back:**

- *Search*: one `xbmcplugin.addDirectoryItem(handle, url, listitem, isFolder=False)` per result, then `xbmcplugin.endOfDirectory(handle)`. ListItem contract:
  - `label` = language name (drives the flag column: skin resolves `windows/subtitles/flags/<thumb>.png`)
  - `label2` = display name / release (the text row — our badges live here)
  - `setArt({"icon": "0".."5"})` = star rating column (`flags/starrating/rating<icon>.png`)
  - `setArt({"thumb": "<2-letter code>"})` = language flag image
  - `setProperty("sync", "true"/"false")` = native SYNC icon
  - `setProperty("hearing_imp", "true"/"false")` = native CC icon
  - These four are the ONLY visuals a subtitle plugin controls; paths are composed by the skin (see `docs/kodi_ui_font_compatibility.md` §1c).
- *Download*: `addDirectoryItem` items whose **path is a local file** (the downloaded `.srt`). Kodi then does everything else itself (`OnDownloadComplete`):
  1. Copies our file to `special://subtitles` (if set), else next to the movie (`storagemode == MOVIEPATH` and path writable), else `special://temp` — **fallback chain, silent**.
  2. Renames it `<moviefilename>.<iso639-1 lang>.<ext>` (language converted from the `language=` param we put in the result URL — `g_LangCodeExpander.ConvertToISO6391`).
  3. If ext is `.sub`, automatically looks for the `.idx` twin next to it and copies that too.
  4. For **stacks** (`stack=1`): return one item *per part, in order*; Kodi maps item N → part N. Size mismatch = only the current part gets a subtitle.
  5. Activates it via `appPlayer->AddSubtitle(path)` on the currently playing item.
  6. Fires GUI message `GUI_MSG_SUBTITLE_DOWNLOADED` and closes the dialog.
- Returning zero download items ⇒ Kodi shows an error toast (label 24113 "Failed to download subtitle") naming our add-on.

**Auto-download path (Kodi-side, not ours):** if Kodi setting `subtitles.downloadfirst` is on, the video has **no embedded subtitle streams** (`GetSubtitleCount() == 0`), and nothing was auto-downloaded for this file yet, Kodi silently downloads **the first item** of our search results. Our smart-ranking order is therefore user-facing even when no dialog is shown — the #1 result IS the auto-pick.

### 1b. `xbmc.service` (`service_monitor.py`) — the background service

- Started when Kodi starts (or the add-on is enabled), one **long-lived process** for the whole Kodi session. Module-level state persists here — unlike `service.py`.
- Must exit promptly on shutdown: main loop is `while not monitor.abortRequested(): monitor.waitForAbort(1)`. Kodi logs and eventually kills add-ons that block exit ~5s.
- All Kodi API calls remain available; there is no reduced sandbox.

---

## 2. `xbmc.Player` — complete surface (subtitle-relevant)

Subclass it and keep the instance alive (the service does); callbacks fire on Kodi's thread.

### Lifecycle callbacks — exact firing semantics

| Callback | Fires when | Notes |
| :--- | :--- | :--- |
| `onPlayBackStarted()` | Play was **requested** | @v18: media may NOT be open yet. `getPlayingFile()` may still raise. Do not collect metadata here. |
| `onAVStarted()` | Kodi actually **has** a video/audio stream | @v18+. The correct hook for auto-download — streams, InfoLabels and InfoTag are ready. |
| `onAVChange()` | Any A/V **or subtitle** stream changes | @v18+. Fires when WE call `setSubtitles()` too — guard against self-triggering. Also fires on audio track switch: chance to re-offer subs in the new audio language. |
| `onPlayBackEnded()` | Playback finished naturally | Kodi moves to next item after this. |
| `onPlayBackStopped()` | User stopped | Ended/Stopped are mutually exclusive. |
| `onPlayBackError()` | Playback died on error | Clean up sessions here too — Ended/Stopped won't fire. |
| `onPlayBackPaused()` / `onPlayBackResumed()` | pause toggle | |
| `onPlayBackSeek(time, seekOffset)` | user seeks | `time` in **ms**. |
| `onPlayBackSeekChapter(chapter)` | chapter jump | |
| `onPlayBackSpeedChanged(speed)` | FF/RW; negative = rewinding, 1 = normal | |
| `onQueueNextItem()` | next playlist item queued | |

**Rule we follow:** metadata collection and auto-download hang off `onAVStarted`, never `onPlayBackStarted`. Session cleanup hooks all three of Ended/Stopped/Error.

### Subtitle methods

| Method | Signature | Behavior |
| :--- | :--- | :--- |
| `setSubtitles` | `(subtitleFile: str) -> None` | Loads an external file AND enables display. Path may be any Kodi VFS path. Triggers `onAVChange`. |
| `showSubtitles` | `(bVisible: bool) -> None` | Toggle visibility only. |
| `getSubtitles` | `() -> str` | Name of the **current** subtitle stream ("" if none). |
| `getAvailableSubtitleStreams` | `() -> List[str]` | Stream *names* (embedded + loaded external). Index in this list = `iStream` for `setSubtitleStream`. |
| `setSubtitleStream` | `(iStream: int) -> None` | Switch by index. |

### Player state / info

| Method | Returns | Raises |
| :--- | :--- | :--- |
| `isPlaying()` / `isPlayingVideo()` / `isPlayingAudio()` | bool | never |
| `isExternalPlayer()` @v18 | bool — if true, none of the stream/subtitle APIs work | never |
| `getPlayingFile()` | full path/url of current item (`pvr://` for LiveTV) | **Exception if not playing** |
| `getPlayingItem()` @v20 | the `ListItem` being played | Exception if not playing |
| `getVideoInfoTag()` | `InfoTagVideo` (getIMDBNumber, getUniqueID('imdb'/'tmdb'), getSeason, getEpisode, getTVShowTitle, getYear, getDbId, getMediaType...) | Exception if not video |
| `getTime()` / `getTotalTime()` | float seconds (`getTotalTime` accurate to 1s) | Exception if not playing |
| `seekTime(secs: float)` | — | Exception if not playing |
| `updateInfoTag(item)` @v18 | refresh info of playing item | Exception if not playing |

**Every `get*` raises when nothing is playing — always wrap in `isPlaying()` check or try/except**, especially in callbacks racing a stop.

---

## 3. `xbmc.Monitor` — complete surface

| Member | Signature | Notes |
| :--- | :--- | :--- |
| `waitForAbort` | `(timeout: float = -1) -> bool` | Blocks; True = abort requested, False = timeout. THE idle primitive — never `time.sleep()` in a service. |
| `abortRequested` | `() -> bool` | Poll before/after any network call in background threads. |
| `onSettingsChanged` | `() -> None` | Fires after settings dialog closes AND after **every programmatic `setSetting()`, including our own**. Must be re-entrant and cheap; see §7 gotcha #1. |
| `onNotification` | `(sender, method, data-json) -> None` | System-wide event bus. `sender="xbmc"` methods include `Player.OnPlay`, `Player.OnAVStart`, `Player.OnAVChange`, `Player.OnSeek`, `Player.OnStop`, `System.OnSleep`, `System.OnWake`, `GUI.OnScreensaverActivated`... Other add-ons can send too (`NotifyAll`). Richer than Player callbacks: `data` carries the item JSON. |
| `onScreensaverActivated/Deactivated` | — | Pause background polling while the screen is off. |
| `onDPMSActivated/Deactivated` | — | Display power saving. |
| `onScanStarted/Finished(library)` `onCleanStarted/Finished(library)` | `library` = "video"/"music" | Library scan lifecycle. |

A Monitor subclass only receives callbacks while the instance is alive — keep a reference for the whole service lifetime.

---

## 4. `xbmc` module functions worth knowing

| Function | Signature | Use |
| :--- | :--- | :--- |
| `log` | `(msg: str, level=LOGDEBUG)` | Levels: LOGDEBUG 0, LOGINFO 1, LOGWARNING 2, LOGERROR 3, LOGFATAL 4, LOGNONE 5. INFO+ shows without debug mode; keep routine chatter at DEBUG. |
| `sleep` | `(timemillis: int)` | **milliseconds**; prefer `Monitor.waitForAbort` in services. |
| `executeJSONRPC` | `(json_str) -> json_str` | Full JSON-RPC without HTTP. See §6. |
| `executebuiltin` | `(function: str, wait=False)` | e.g. `ActivateWindow(SubtitleSearch)`, `Notification(...)`, `SetSubtitle`. |
| `getInfoLabel` | `(cLine) -> str` | Any InfoLabel: `VideoPlayer.Title/Year/Season/Episode/TVshowtitle/OriginalTitle/DBID/UniqueID(imdb)`, `Player.FilenameAndPath`... Snapshot at call time; empty string when unavailable. |
| `getCondVisibility` | `(condition) -> bool` | e.g. `Player.HasVideo`, `VideoPlayer.HasSubtitles`, `System.HasAddon(id)`, `Window.IsActive(subtitlesearch)`. |
| `getLanguage` | `(format=ENGLISH_NAME, region=False) -> str` | Formats: `xbmc.ISO_639_1` (=0, "en"), `xbmc.ISO_639_2` (=1, "eng"), `xbmc.ENGLISH_NAME` (=2). `region=True` appends "-US" style. **UI language, not subtitle preference.** |
| `convertLanguage` | `(language, format) -> str` | Converts any recognized language name/code between the three formats. The right tool instead of `lang[:2].lower()` slicing. |
| `getLocalizedString` | `(id) -> str` | Kodi-core strings (30000+ range is addon-local via `Addon.getLocalizedString`). |
| `getRegion` | `(id)` | `id` ∈ dateshort/datelong/time/meridiem/tempunit/speedunit. |
| `getSupportedMedia` | `(mediaType)` | 'video'/'music'/'picture' extension list. |
| `getFreeMem`, `getGlobalIdleTime`, `getIPAddress`, `getUserAgent` | | misc. |

---

## 5. `xbmcgui`, `xbmcplugin`, `xbmcaddon`, `xbmcvfs` essentials

### `xbmcgui.Dialog`
- `notification(heading, message, icon="", time=0, sound=True)` — icon can be `xbmcgui.NOTIFICATION_INFO/WARNING/ERROR` or a path to our PNG; time in ms (default 5000).
- `yesno(heading, message, nolabel="", yeslabel="", autoclose=0, defaultbutton=None)` — `autoclose` ms (0 = never; returns False on autoclose); `defaultbutton` @v20: `xbmcgui.DLG_YESNO_NO_BTN/_YES_BTN/_CUSTOM_BTN`. Our rating prompt should pass `autoclose` so an unattended TV doesn't hold the prompt forever.
- `yesnocustom(heading, message, customlabel, ...) -> int` — -1 cancelled / 0 no / 1 yes / 2 custom. Three-way: e.g. "Rate: Good / Bad / Don't ask again".
- `ok`, `textviewer(heading, text, usemono=False)`, `select(heading, list, autoclose=0, preselect=-1, useDetails=False)`, `multiselect`, `contextmenu(list)`, `input(heading, defaultt="", type=xbmcgui.INPUT_ALPHANUM, option=...)`.
- `DialogProgressBG` — non-modal background progress (top corner), `create/update/close`; polite for slow searches.

### `xbmcgui.ListItem`
`ListItem(label="", label2="", path="", offscreen=False)` — **pass `offscreen=True`** for items never drawn before handing to `xbmcplugin` (skips GUI-thread locks; big win when listing many results). `setLabel/setLabel2/setArt/setProperty/setPath`; `setInfo()` deprecated @v20 in favor of `getVideoInfoTag().set*()` — irrelevant for subtitle items (subtitle dialog reads only label/label2/art/properties above).

### `xbmcplugin`
- `addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0) -> bool`
- `addDirectoryItems(handle, [(url, item, isFolder), ...]) -> bool` — **one C++ boundary crossing for the whole list**; use for result sets.
- `endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True)` — ALWAYS call, even on failure (`succeeded=False`), or the dialog spinner hangs until timeout.

### `xbmcaddon.Addon`
- `Addon(id=None)` — no id = the *calling* add-on. Cheap to construct; **construct fresh when reading settings after a change** (long-lived instances hold a stale settings snapshot in some versions).
- `getSetting/setSetting` (str) plus typed `getSettingBool/Int/Number/String` and setters. @v20: `getSettings() -> Settings` object with `getBool/getInt/getNumber/getString/getStringList` + setters — one snapshot, typed access.
- `setSetting` on an id **not declared in `resources/settings.xml`** logs an error and may not persist (version-dependent) — declare every persisted key, even hidden ones (`<level>4</level>`). Definition changes require settings-dialog reopen or Kodi restart to register.
- `getAddonInfo(id)` — id ∈ author/changelog/description/disclaimer/fanart/icon/id/name/path/profile/stars/summary/type/version.

### `xbmcvfs`
- `translatePath(path)` (moved here from `xbmc` @v19) — `special://home`, `special://temp`, `special://profile`, `special://subtitles` (empty if unset), `special://userdata`.
- `File` (context-manager), `exists`, `copy`, `delete`, `rename`, `mkdirs`, `listdir`, `makeLegalFilename`, `Stat`. Use these over `os.*` for anything that might be a VFS path (smb://, nfs://, zip://).

---

## 6. JSON-RPC via `xbmc.executeJSONRPC` — the power tools

No HTTP, no auth, always available in-process. `json.dumps` in, `json.loads` out.

| Call | Why we care |
| :--- | :--- |
| `Player.GetActivePlayers` | playerid (video is almost always 1, but don't hardcode). |
| `Player.GetProperties (playerid, ["subtitleenabled","currentsubtitle","subtitles","audiostreams","currentaudiostream"])` | **Richer than xbmc.Player**: each subtitle entry has `index, language (ISO 639-2), name, isdefault, isforced, isimpaired`. `Player.getAvailableSubtitleStreams` gives names only — this gives structured flags. The right way to detect "a forced/SDH sub is already active". |
| `Player.SetSubtitle (playerid, subtitle="on"/"off"/"next"/index, enable=True)` | Switch by index with explicit enable. |
| `Player.AddSubtitle (playerid, subtitle=path_or_url)` | What Kodi itself calls after a download. Accepts **remote URLs** too. |
| `Player.GetItem (playerid, ["imdbnumber","season","episode","showtitle","uniqueid","file","streamdetails"])` | Library metadata incl. `uniqueid` dict — sturdier than InfoLabel scraping. |
| `Settings.GetSettingValue (setting="subtitles.languages" / "locale.subtitlelanguage" / "subtitles.storagemode" / "subtitles.custompath" / "subtitles.downloadfirst" / "subtitles.pauseonsearch")` | Read Kodi's own subtitle prefs — e.g. warn when `downloadfirst` overlaps our auto-download. |
| `VideoLibrary.GetTVShowDetails / GetEpisodeDetails / GetMovieDetails` | Already used by `data_collector` for parent-show IMDb. |
| `JSONRPC.NotifyAll (sender, message, data)` | Broadcast to other add-ons; also received by our own `onNotification`. |
| `XBMC.GetInfoLabels (labels=[...])` | Batch InfoLabel read in one call. |

---

## 7. Gotchas & internals (hard-won; keep updated)

1. **`onSettingsChanged` echo loop.** Fires for every `setSetting()` we perform, not just user edits. A handler that writes settings retriggers itself → storm. Guard: fingerprint the inputs you care about (we hash credentials) and bail when unchanged. Fixed 2026-08-19.
2. **Fresh process per plugin call, long process for service.** Cache cross-invocation data in settings, `xbmcgui.Window(10000).setProperty` (RAM, session-scoped — our `cache.py`), or files under `special://profile/addon_data/<id>/`. Dev corollary: `service.py`-side edits are live on the next search, but **`service_monitor.py` edits do nothing until Kodi restarts** (or the add-on is disabled/re-enabled) — the old service process keeps running. "My change has no effect" during service work is almost always this.
3. **`getPlayingFile()`/`getTime()`/`getVideoInfoTag()` raise** when playback stopped — callbacks race stops, so try/except everything in `onAVStarted` handlers.
4. **`waitForAbort(1)`-after-play is a hack; `onAVStarted` is the contract.** Streams aren't guaranteed at `onPlayBackStarted`; they are at `onAVStarted`.
5. **Kodi renames whatever we return.** Download results become `<video>.<lang>.<ext>` in Kodi's chosen location — never rely on our temp filename surviving; never pre-copy next to the movie ourselves (Kodi handles storagemode + read-only fallback).
6. **`stack=1`** means the user plays a multi-part file; return download items per part in order.
7. **Kodi's own auto-download** (`subtitles.downloadfirst`) takes our #1 search result with no UI. Ranking quality is a functional feature, not cosmetics. Also: it only triggers when the file has zero embedded subs, and once per file per session (`m_LastAutoDownloaded`).
8. **`special://subtitles`** (custom subtitle folder) empty = unset. Kodi's fallback chain on download: custom path → movie folder (if writable + storagemode) → `special://temp`.
9. **Emoji/glyph rendering** in list rows and dialogs: see `docs/kodi_ui_font_compatibility.md` — Dingbats block absent, emoji break `[COLOR]` parsing.
10. **Debug logging without the on-screen overlay:** `userdata/advancedsettings.xml` → `<advancedsettings><loglevel hide="true">1</loglevel></advancedsettings>`. Debug-level lines go to kodi.log, no OSD box, survives restarts (the GUI toggle always shows the overlay). Log lives at `~/Library/Logs/kodi.log` (macOS) / `~/.kodi/temp/kodi.log` (Linux).
11. **`offscreen=True`** on ListItems destined for `xbmcplugin` — skips per-property GUI locks.
12. **`Addon()` settings snapshots:** construct a fresh `xbmcaddon.Addon()` inside handlers that run after settings changes; a module-level instance can serve stale values.
13. **Never block Kodi's callback thread**: Player/Monitor callbacks run on Kodi's thread — spawn `threading.Thread(daemon=True)` for network work, checking `abortRequested()` before/after each request (our pattern).
14. **`isExternalPlayer()`**: when true, `setSubtitles`/stream APIs are no-ops; skip auto-download gracefully.

## 8. Current usage audit (2026-08-19) — where we stand

| Area | Today | Verdict / opportunity |
| :--- | :--- | :--- |
| Auto-download trigger | `onAVStarted` + `waitForAbort(1)` settle delay | Correct hook. The extra 1s is defensive; harmless. |
| Embedded-sub check | `getAvailableSubtitleStreams()` + `Player.Language(Subtitles)` InfoLabel | Upgrade: JSON-RPC `Player.GetProperties` gives structured `isforced/isimpaired/language` — can skip auto-download only when a *matching-language, non-forced* sub is active. |
| Preferred language | `System.Language(Subtitles)` InfoLabel + `[:2]` slicing | Upgrade: `Settings.GetSettingValue("subtitles.languages")` (the real multi-select) + `xbmc.convertLanguage(name, xbmc.ISO_639_1)`. |
| Session cleanup | `onPlayBackStopped/Ended` | Gap: `onPlayBackError` not handled → stale `active_session`. |
| Rating prompt | `dialog.yesno(...)` no autoclose | Add `autoclose` (e.g. 60000) + `defaultbutton=DLG_YESNO_YES_BTN`. |
| Result listing | per-item `addDirectoryItem`, no `offscreen` | Upgrade: `ListItem(offscreen=True)` + single `addDirectoryItems`. |
| `endOfDirectory` on failure paths | only on success | Gap: call with `succeeded=False` when search errors, else dialog spins. |
| Kodi-side auto-download overlap | detected: ours stands down when `subtitles.downloadfirst` is on (one-time notification) | done 2026-08-19 |
| `stack=1` | ignored | Rare, but contract says one item per part on download. |

Keep this table honest: when an upgrade lands, move the row to "Today".

## 9. Auto-download: Kodi native vs. this add-on's service

Kodi ships its own "Auto download first subtitle" (`subtitles.downloadfirst`). Both features
solving the same job would double downloads, burn quota twice, and race for the active
subtitle slot — so the service **detects Kodi's setting via JSON-RPC and stands down** when
it is on (one-time notification explains the trade). The user picks one; ours is off by
default, Kodi's wins ties. Where each is stronger:

| Aspect | Kodi native (`downloadfirst`) | This add-on's service auto-download |
| :--- | :--- | :--- |
| Trigger condition | only when the file has ZERO embedded subtitle streams | whenever no subtitle is actually being displayed — catches "embedded English but user wants Czech" and "subs present but switched off" |
| Languages | one file: the single first search result | **top pick per preferred language** (`subtitles.languages`), primary active, others one key-press away in the stream list |
| Selection | first item of our search results (so our ranking still applies) | same ranking, plus per-language grouping |
| Once-per-file guard | yes (in-session) | session-scoped via `active_session` |
| Notification | generic Kodi behavior | names the release + extra languages loaded |
| Rating feedback loop | none — bypasses the service, no session recorded | records session → post-playback sync rating → improves data for everyone |
| Quota awareness | none | capped at 5 downloads/file; skips cleanly on auth/quota errors with actionable alerts |
| UI noise | opens the subtitle dialog briefly on playback start | fully silent background thread |
| Storage handling | Kodi's full storagemode chain (movie folder / custom / temp) | `special://temp` only (session-scoped) |
| Conflict behavior | — | stands down automatically when Kodi's is enabled |
