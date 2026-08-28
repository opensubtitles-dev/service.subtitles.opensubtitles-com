"""Best-effort 'open URL in browser' across Kodi platforms.

Kodi has NO cross-platform browser API - what exists differs per platform:

- Android: the StartAndroidActivity() builtin fires an ACTION_VIEW intent;
  the system opens its default browser.
- Desktop (macOS / Windows / Linux with a desktop): Python's stdlib
  webbrowser module reaches the OS default browser.
- Everything else (LibreELEC/CoreELEC, tvOS, embedded boxes): there is no
  browser at all. open_url() returns False and the caller keeps its QR code
  on screen - the phone IS the browser there.
"""

import xbmc

from resources.lib.utilities import log, redact_path


def can_open_browser():
    return bool(
        xbmc.getCondVisibility("System.Platform.Android")
        or xbmc.getCondVisibility("System.Platform.OSX")
        or xbmc.getCondVisibility("System.Platform.Windows")
        or xbmc.getCondVisibility("System.Platform.Linux")
    )


def open_url(url):
    """Opens the URL in the platform's default browser. True when launched."""
    try:
        if xbmc.getCondVisibility("System.Platform.Android"):
            xbmc.executebuiltin(f"StartAndroidActivity(,android.intent.action.VIEW,,{url})")
            log(__name__, f"Opened in Android browser: {redact_path(url)}")
            return True
        if can_open_browser():
            import webbrowser
            if webbrowser.open(url):
                log(__name__, f"Opened in desktop browser: {redact_path(url)}")
                return True
    except Exception as e:
        log(__name__, f"Browser launch failed ({type(e).__name__}), QR remains the way")
    return False
