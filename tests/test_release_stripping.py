"""Guarantees no release package ever ships the Development settings tab."""
import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from release_lib import DEV_SETTING_IDS, strip_development_settings

SETTINGS = os.path.join(os.path.dirname(__file__), "..", "resources", "settings.xml")


def test_strip_removes_the_whole_development_category():
    stripped = strip_development_settings(open(SETTINGS, encoding="utf-8").read())
    root = ET.fromstring(stripped)

    ids = [c.attrib.get("id") for c in root.findall(".//category")]
    assert "development" not in ids
    assert ids == ["user", "filter", "automation", "debug"], "only the dev tab may vanish"
    for setting_id in DEV_SETTING_IDS:
        assert setting_id not in stripped


def test_strip_is_idempotent():
    once = strip_development_settings(open(SETTINGS, encoding="utf-8").read())
    assert strip_development_settings(once) == once


def test_every_dev_setting_lives_inside_the_development_category():
    """A dev toggle placed in another tab would survive the strip - forbidden."""
    root = ET.parse(SETTINGS).getroot()
    dev = root.find(".//category[@id='development']")
    dev_ids = {s.attrib.get("id") for s in dev.findall(".//setting")}
    assert set(DEV_SETTING_IDS) == dev_ids


def test_stray_dev_setting_outside_category_fails_the_build():
    doctored = open(SETTINGS, encoding="utf-8").read().replace(
        '<category id="debug"',
        '<category id="debug"><!-- x --></category><category id="debug2"',
        1)  # keep parse valid but move nothing - now inject a stray id
    doctored = doctored.replace("</settings>",
                                "<!-- test_flag_interceptor -->\n</settings>")
    with pytest.raises(ValueError):
        strip_development_settings(doctored)


def test_release_default_for_interceptor_is_off():
    """Even if a strip failed, a shipped default must never inject mock results."""
    root = ET.parse(SETTINGS).getroot()
    setting = root.find(".//setting[@id='test_flag_interceptor']")
    assert setting.find("default").text == "false"
