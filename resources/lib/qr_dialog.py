"""Full-screen QR code dialog.

The only way a Kodi add-on can show an arbitrary picture is a custom
xbmcgui.WindowDialog with a ControlImage - settings dialogs and toast
notifications have no usable image slot. Coordinates are in Kodi's 1280x720
skin coordinate system; skins scale them to the real resolution.
"""

import os

import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib.qr import generate_qr_png
from resources.lib.utilities import log

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_SELECT_ITEM = 7
ACTION_STOP = 13

QR_SIZE = 420  # px in the 1280x720 skin grid


class QRWindow(xbmcgui.WindowDialog):
    """Centered QR image with a heading above and the raw URL below."""

    def __init__(self, png_path, heading, caption):
        super().__init__()
        x = (1280 - QR_SIZE) // 2
        y = (720 - QR_SIZE) // 2

        # Dim the whole screen behind the code so video/UI noise cannot bleed
        # through - a busy background makes phone cameras slow to lock on.
        self.addControl(xbmcgui.ControlImage(
            0, 0, 1280, 720, os.path.join(_media_path(), "os_fanart.jpg"),
            colorDiffuse="DD000000"))
        self.addControl(xbmcgui.ControlLabel(
            0, y - 70, 1280, 40, heading, textColor="0xFFFFFFFF",
            alignment=2, font="font14"))  # alignment 2 = center X
        # The PNG already carries the white quiet-zone border required by the
        # QR spec, so it can sit directly on the dimmed background.
        self.addControl(xbmcgui.ControlImage(x, y, QR_SIZE, QR_SIZE, png_path))
        self.addControl(xbmcgui.ControlLabel(
            0, y + QR_SIZE + 20, 1280, 36, caption, textColor="0xFFAAAAAA",
            alignment=2, font="font12"))
        self.addControl(xbmcgui.ControlLabel(
            0, y + QR_SIZE + 56, 1280, 30, "Press BACK or OK to close",
            textColor="0xFF666666", alignment=2, font="font10"))

    def onAction(self, action):
        if action.getId() in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK,
                              ACTION_SELECT_ITEM, ACTION_STOP):
            self.close()


def _media_path():
    return xbmcvfs.translatePath(
        os.path.join(__addon__.getAddonInfo("path"), "resources", "media"))


def show_qr(url, heading):
    """Generates a QR PNG for `url` and shows it modally. Blocks until closed."""
    profile = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
    png_path = os.path.join(profile, "temp", "qr.png")
    try:
        generate_qr_png(url, png_path)
    except Exception as e:
        # No picture is still better served than nothing: fall back to text.
        log(__name__, f"QR generation failed ({e}), showing plain URL instead")
        xbmcgui.Dialog().ok(heading, url)
        return

    log(__name__, f"Showing QR dialog for {url}")
    window = QRWindow(png_path, heading, url)
    window.doModal()
    del window
