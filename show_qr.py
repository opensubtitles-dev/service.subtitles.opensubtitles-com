"""Settings-button entry point: show a QR code the user can scan with a phone.

Invoked via RunScript(...) from resources/settings.xml. Optional argv[1] selects
what to show; default is the account registration page.
"""

import sys

import xbmcaddon

# --- addon import path guard (keep this above any `resources.*` import) ------------
# Kodi launches this file with RunScript(<file path>), which it treats as a script
# "invoked without an addon". It then appends *every* installed add-on's library
# directory to sys.path and puts ours LAST, so another add-on shipping a top-level
# `resources` package wins `import resources` and our own modules become invisible:
#   ModuleNotFoundError: No module named 'resources.lib.osclient'
# (issue #39, support ticket #168978). Deleting this block silently reintroduces that
# bug for anyone with a conflicting add-on installed - it already happened once, so
# tests/test_runscript_entrypoints.py now fails if it goes missing again.
import os
import sys

_addon_path = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.normpath(p) != _addon_path]
sys.path.insert(0, _addon_path)
# If a *foreign* `resources` was already imported, evict it so ours wins. Leave an
# already-correct one alone: re-importing it would create a second set of exception
# classes, and `except ServiceUnavailable` would stop matching the one raised.
_res = sys.modules.get("resources")
if _res is not None and not any(os.path.normpath(p).startswith(_addon_path)
                                for p in getattr(_res, "__path__", [])):
    for _module in [m for m in list(sys.modules) if m == "resources" or m.startswith("resources.")]:
        del sys.modules[_module]
# -----------------------------------------------------------------------------------

from resources.lib.qr_dialog import show_qr

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__language__ = __addon__.getLocalizedString

TARGETS = {
    "register": ("https://www.opensubtitles.com/users/sign_up", 32259),
    "vip": ("https://www.opensubtitles.com/users/vip", 32259),
    "website": ("https://www.opensubtitles.com", 32259),
}


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "register"
    url, heading_id = TARGETS.get(target, TARGETS["register"])
    show_qr(url, __language__(heading_id))


if __name__ == "__main__":
    main()
