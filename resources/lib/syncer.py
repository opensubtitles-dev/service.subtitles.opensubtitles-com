"""Subtitle synchronization plumbing (design: docs/subtitle_sync_plan.md).

STATUS: interface + invocation wiring only. The actual alignment ENGINE is
being developed in the separate `subsync` project and will be dropped in
behind sync_subtitle() when it is finished - nothing here may grow its own
competing implementation in the meantime.

Pure module apart from the settings read: no player state, no dialogs - the
callers (subtitle dialog row, background service nudge offer) own all UI.
"""

import xbmcaddon

from resources.lib.utilities import log as _log

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")


def log(msg):
    _log(__name__, msg)


class SyncError(Exception):
    """A synchronization attempt failed in a way worth telling the user."""


class EngineNotAvailable(SyncError):
    """The alignment engine is not bundled yet (project subsync pending)."""


def is_enabled():
    """The expert toggle gating BOTH invocation paths (row + nudge offer)."""
    val = __addon__.getSetting("subtitle_sync_enabled")
    return bool(val) and val.lower() in ("true", "1")


def engine_available():
    """True once the subsync engine is bundled. Kept as a function so the
    callers need no change on the day it lands."""
    return False


def sync_subtitle(sub_path, video_path=None, session=None, progress=None):
    """Synchronize the subtitle at `sub_path` against its video. THE socket
    for the subsync engine.

    Contract for the engine drop-in (agreed in docs/subtitle_sync_plan.md):

      - input: path of the active subtitle; optionally the video path and the
        playback session dict (moviehash, file_id, sampled subtitle_delay)
      - the corrected subtitle is written to a NEW file (never in place -
        the original stays untouched for a retry) and its path returned
      - returns {"path": <corrected file>, "offset_ms": <int>,
                 "fps_scale": <float>, "method": "hint"|"reference"|"audio"}
      - raises SyncError with a user-presentable, viewing-history-free
        message on failure; EngineNotAvailable when no rung can run
      - must honor progress.iscanceled() when a progress dialog is passed
      - NEVER touches a moviehash_match subtitle (caller enforces too)

    Until the engine lands this always raises EngineNotAvailable.
    """
    log("sync requested (engine not bundled yet - project subsync pending)")
    raise EngineNotAvailable()


# ---------------------------------------------------------------------------
# Delay-nudge detection (used by the background service).
#
# The moment a user SEES bad sync they open Kodi's own subtitle-offset dialog
# and start nudging Player.SubtitleDelay. More than NUDGE_THRESHOLD distinct
# values in one session means "struggling, not fine-tuning" - the one moment
# an automatic-sync offer is welcome instead of annoying.
# ---------------------------------------------------------------------------

NUDGE_THRESHOLD = 2


def register_delay_sample(session, delay):
    """Feeds one sampled Player.SubtitleDelay value into the session.

    Returns True exactly ONCE per session: at the moment the nudge count
    crosses the threshold and the sync offer should be made. The caller
    decides whether the offer is allowed at all (toggle, moviehash, engine).
    """
    if not isinstance(session, dict):
        return False
    delay = str(delay or "").strip()
    if not delay:
        return False
    seen = session.setdefault("_delay_values", [])
    if delay in seen:
        return False
    seen.append(delay)
    # first value is the baseline (usually "0.000 s"), not a nudge
    nudges = len(seen) - 1
    if nudges > NUDGE_THRESHOLD and not session.get("_sync_offered"):
        session["_sync_offered"] = True
        return True
    return False
