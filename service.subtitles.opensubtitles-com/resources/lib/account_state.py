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
import time

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


class _StateLock:
    """Cross-process exclusive lock around the state file.

    update_account_state() is a read-modify-write, and Kodi runs the settings
    scripts and the service as separate processes - Test Connection saving a
    full snapshot while a download merges its fresh quota could drop one of the
    two (review: PR #92, second pass). O_CREAT|O_EXCL is the portable primitive
    here: no fcntl (Windows) and no msvcrt (POSIX) branch needed.

    A lock older than STALE_AFTER is broken: a process killed mid-write must
    never wedge account updates permanently. Failing to acquire is not fatal -
    the caller proceeds unlocked, which is exactly the old behaviour.
    """
    TIMEOUT = 5.0
    STALE_AFTER = 30.0
    POLL = 0.05

    def __init__(self, path):
        self.path = path + ".lock"
        self.fd = None

    def __enter__(self):
        deadline = time.time() + self.TIMEOUT
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > self.STALE_AFTER:
                        os.unlink(self.path)        # abandoned by a dead process
                        continue
                except OSError:
                    pass                            # vanished meanwhile: retry
                if time.time() >= deadline:
                    return self                     # unlocked, but not stuck
                time.sleep(self.POLL)
            except OSError:
                return self                         # unwritable dir: proceed

    def __exit__(self, *exc):
        if self.fd is not None:
            try:
                os.close(self.fd)
                os.unlink(self.path)
            except OSError:
                pass
        return False


def save_account_state(state):
    """Writes the full state snapshot (Test Connection's path), under the lock."""
    with _StateLock(_state_path()):
        _write_account_state(state)


def _write_account_state(state):
    """Unlocked writer - callers must already hold _StateLock."""
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


def update_account_state(partial):
    """Merges a few account fields into the persisted state file.

    The state file is authoritative: the background service reconciles settings
    back to it after every settings-dialog save. A writer that updated only the
    SETTINGS therefore saw its values reverted on the next reconciliation - a
    fresh download quota would visibly regress to an older number
    (review: PR #92). Callers that refresh any account field write through here.

    Read and write happen under _StateLock so a concurrent full snapshot from
    Test Connection cannot be interleaved with this merge.
    """
    if not partial:
        return
    with _StateLock(_state_path()):
        state = load_account_state()
        state.update({k: str(v) for k, v in partial.items() if k in ACCOUNT_KEYS})
        _write_account_state(state)      # already locked: never re-enter the lock
