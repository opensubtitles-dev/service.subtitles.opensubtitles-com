"""Covers the background service warning the user about a misconfigured account.

The rule the tests protect: a problem only the user can fix (no credentials, wrong
password, email in the username field) is reported, transient service trouble is not,
and the same problem is not repeated more than once a day.
"""
from unittest.mock import MagicMock, patch

import pytest

import resources.lib.background_service as service_monitor
from resources.lib.background_service import (
    ACCOUNT_ALERT_REPEAT_AFTER,
    clear_account_alert,
    notify_account_problem,
)

# NOTE: the service no longer validates or writes account state (single-writer
# architecture: test_connection.py owns account_* settings). Only the
# notification contract lives here now; the write path is covered by
# tests/test_connection_flow.py.


class FakeAddon:
    """Minimal settings store standing in for xbmcaddon.Addon."""
    def __init__(self, **settings):
        self._settings = dict(settings)

    def getSetting(self, key):
        return self._settings.get(key, "")

    def setSetting(self, key, value):
        self._settings[key] = str(value)

    def getAddonInfo(self, key):
        return {"path": "/mock/path"}.get(key, "")




@pytest.fixture
def dialog():
    with patch("resources.lib.background_service.xbmcgui.Dialog") as dialog_class:
        yield dialog_class.return_value


@pytest.mark.parametrize("problem", ["missing", "invalid", "bad_username"])
def test_each_account_problem_notifies_the_user(problem, dialog):
    addon = FakeAddon()

    notify_account_problem(problem, addon)

    assert dialog.notification.call_count == 1
    assert addon.getSetting("account_alert_state").startswith(f"{problem}|")


def test_same_problem_is_not_repeated_within_a_day(dialog):
    addon = FakeAddon()

    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0):
        notify_account_problem("missing", addon)
    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0 + ACCOUNT_ALERT_REPEAT_AFTER - 60):
        notify_account_problem("missing", addon)

    assert dialog.notification.call_count == 1


def test_same_problem_warns_again_after_a_day(dialog):
    addon = FakeAddon()

    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0):
        notify_account_problem("missing", addon)
    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0 + ACCOUNT_ALERT_REPEAT_AFTER + 1):
        notify_account_problem("missing", addon)

    assert dialog.notification.call_count == 2


def test_a_different_problem_warns_straight_away(dialog):
    addon = FakeAddon()

    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0):
        notify_account_problem("missing", addon)
        notify_account_problem("invalid", addon)

    assert dialog.notification.call_count == 2


def test_successful_login_clears_the_alert_so_a_relapse_warns_again(dialog):
    addon = FakeAddon()

    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0):
        notify_account_problem("invalid", addon)
        clear_account_alert(addon)
        notify_account_problem("invalid", addon)

    assert addon.getSetting("account_alert_state").startswith("invalid|")
    assert dialog.notification.call_count == 2






def test_a_second_wrong_password_warns_again_despite_the_daily_hold(dialog):
    """Someone retyping a password is waiting for a verdict - silence would read as success."""
    addon = FakeAddon(OSuser="user", OSpass="wrong-one", APIKey="key")

    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0):
        notify_account_problem("invalid", addon)
        addon.setSetting("OSpass", "wrong-again")
        notify_account_problem("invalid", addon)

    assert dialog.notification.call_count == 2


def test_unchanged_credentials_stay_on_the_daily_hold(dialog):
    addon = FakeAddon(OSuser="user", OSpass="wrong-one", APIKey="key")

    with patch("resources.lib.background_service.time.time", return_value=1_000_000.0):
        notify_account_problem("invalid", addon)
        notify_account_problem("invalid", addon)

    assert dialog.notification.call_count == 1




def test_fingerprint_never_stores_the_credentials_themselves():
    fingerprint = service_monitor.credentials_fingerprint("brano", "hunter2")

    assert "brano" not in fingerprint and "hunter2" not in fingerprint
    assert len(fingerprint) == 64
    assert fingerprint != service_monitor.credentials_fingerprint("brano", "hunter3")
    assert service_monitor.credentials_fingerprint("brano", "") == ""






