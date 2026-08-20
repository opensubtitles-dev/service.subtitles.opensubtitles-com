"""Settings-button entry point: show a QR code the user can scan with a phone.

Invoked via RunScript(...) from resources/settings.xml. Optional argv[1] selects
what to show; default is the account registration page.
"""

import sys

import xbmcaddon

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
