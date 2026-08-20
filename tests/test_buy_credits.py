"""Covers the AI credit purchase flow (buy_credits.py)."""
from unittest.mock import MagicMock, patch

import xbmcaddon

import buy_credits


OFFERS = [
    {"name": "500 credits", "value": "5 USD", "discount_percent": 0, "checkout_url": "https://x/1"},
    {"name": "5500 credits", "value": "50 USD", "discount_percent": 10, "checkout_url": "https://x/2"},
]


def test_offer_labels_show_price_and_discount_only_when_granted():
    assert buy_credits.format_offer(OFFERS[0]) == "500 credits - 5 USD"
    assert buy_credits.format_offer(OFFERS[1]) == "5500 credits - 50 USD (-10%)"


def _creds():
    addon = xbmcaddon.Addon()
    addon.setSetting("OSuser", "user")
    addon.setSetting("OSpass", "pass")
    addon.setSetting("APIKey", "key")


def test_selected_offer_opens_its_checkout_qr():
    _creds()
    dialog = MagicMock()
    dialog.select.return_value = 1  # picks the 5500 pack

    with patch("buy_credits.xbmcgui.Dialog", return_value=dialog), \
         patch("buy_credits.OpenSubtitlesProvider") as provider_class, \
         patch("buy_credits.show_qr") as qr:
        provider_class.return_value.get_ai_credit_offers.return_value = OFFERS
        buy_credits.main()

    labels = dialog.select.call_args[0][1]
    assert labels == ["500 credits - 5 USD", "5500 credits - 50 USD (-10%)"]
    qr.assert_called_once()
    assert qr.call_args[0][0] == "https://x/2"


def test_cancelling_the_package_list_shows_no_qr():
    _creds()
    dialog = MagicMock()
    dialog.select.return_value = -1

    with patch("buy_credits.xbmcgui.Dialog", return_value=dialog), \
         patch("buy_credits.OpenSubtitlesProvider") as provider_class, \
         patch("buy_credits.show_qr") as qr:
        provider_class.return_value.get_ai_credit_offers.return_value = OFFERS
        buy_credits.main()

    qr.assert_not_called()


def test_offers_are_fetched_fresh_on_every_click():
    _creds()
    dialog = MagicMock()
    dialog.select.return_value = 0

    with patch("buy_credits.xbmcgui.Dialog", return_value=dialog), \
         patch("buy_credits.OpenSubtitlesProvider") as provider_class, \
         patch("buy_credits.show_qr"):
        provider = provider_class.return_value
        provider.get_ai_credit_offers.return_value = OFFERS
        buy_credits.main()
        buy_credits.main()

    assert provider.login.call_count == 2
    assert provider.get_ai_credit_offers.call_count == 2
