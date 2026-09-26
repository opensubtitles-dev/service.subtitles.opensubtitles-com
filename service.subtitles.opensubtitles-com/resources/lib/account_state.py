"""Authoritative account state, immune to settings-dialog snapshot saves.

Kodi's add-on settings dialog snapshots every value when it opens and saves
that snapshot back when it closes - including across a RunScript launched from
a <close>true</close> button. Anything a script writes to settings can
therefore be silently reverted by a dialog the user still has in play
(observed live: a passed Test Connection reverting to a stale 401 state).

Test Connection writes the truth HERE (single writer, atomic replace); the
background service mirrors this file back into settings whenever a dialog
save drifts them. Settings are just the display cache.
"""

import json
import os

import xbmcaddon
import xbmcvfs

ACCOUNT_KEYS = (
    "account_status", "account_details", "account_checked_at",
    "account_verified_at", "account_logged_in", "account_is_vip", "ai_credits",
)


def _state_path():
    addon = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
    profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
    return os.path.join(profile, "account_state.json")


def save_account_state(state):
    try:
        path = _state_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({k: str(v) for k, v in state.items() if k in ACCOUNT_KEYS}, f)
        os.replace(tmp_path, path)
    except Exception:
        # Resilience layer only - an unwritable profile dir must never break
        # the probe itself. Settings still carry the values for this session.
        pass


def load_account_state():
    try:
        with open(_state_path(), "r", encoding="utf-8") as f:
            return {k: str(v) for k, v in json.load(f).items() if k in ACCOUNT_KEYS}
    except Exception:
        return {}
