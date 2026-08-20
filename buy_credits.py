"""Settings-button entry point: buy AI credits.

Fetches the live package list from the API on EVERY click (prices and discounts
change server-side), lets the user pick one, then shows the package's checkout
URL as a QR code to finish the purchase on a phone.
"""

import xbmcaddon
import xbmcgui

from resources.lib.osclient.provider import OpenSubtitlesProvider
from resources.lib.qr_dialog import show_qr
from resources.lib.utilities import log

__addon__ = xbmcaddon.Addon("service.subtitles.opensubtitles-com")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def format_offer(offer):
    """'5500 credits - 50 USD (-10%)' - discount only when the API grants one."""
    label = f"{offer.get('name', '?')} - {offer.get('value', '?')}"
    discount = offer.get("discount_percent") or 0
    if discount:
        label += f" (-{discount}%)"
    return label


def main():
    dialog = xbmcgui.Dialog()
    username = __addon__.getSetting("OSuser")
    password = __addon__.getSetting("OSpass")
    api_key = __addon__.getSetting("APIKey")
    if not username or not password:
        dialog.ok(__addon_name__, __language__(32252))
        return

    provider = OpenSubtitlesProvider(api_key, username, password)
    try:
        provider.login()
    except Exception as e:
        log(__name__, f"Buy credits: login failed ({e})")
        dialog.ok(__addon_name__, __language__(32253))
        return

    offers = provider.get_ai_credit_offers()
    if not offers:
        dialog.ok(__addon_name__, "Credit packages are unavailable right now. Please try again later.")
        return

    choice = dialog.select(__language__(32267), [format_offer(o) for o in offers])
    if choice < 0:
        return

    selected = offers[choice]
    log(__name__, f"Buy credits: selected {selected.get('name')}")
    show_qr(selected["checkout_url"], f"{__language__(32267)}: {format_offer(selected)}")


if __name__ == "__main__":
    main()
