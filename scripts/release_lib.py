"""Shared release-packaging helpers.

The Development settings tab (mock search interceptor, rating-dialog preview,
auto-upload dry run) exists ONLY in the source tree. Both packagers -
build_release_zip.py and generate_repo.py - route resources/settings.xml
through strip_development_settings() so no shipped ZIP ever contains it.

The runtime needs no build flag for this: every dev feature is read through
getSetting(), and a setting whose definition is absent returns "" - the
features are inert in release builds by construction.
"""

import re
import xml.etree.ElementTree as ET

# Setting ids that must never appear in a shipped package. Extend this tuple
# when adding a new Development-tab setting; the release test enforces it.
DEV_SETTING_IDS = (
    "test_flag_interceptor",
    "test_rating_preview",
    "auto_upload_subtitles",
    "test_nocache",
    "test_disable_query_fallback",
    "test_show_search_debug",
    "test_override_language",
)

_DEV_CATEGORY_RE = re.compile(
    r"[ \t]*<category id=\"development\".*?</category>\r?\n?", re.DOTALL)


def strip_development_settings(settings_xml_text):
    """Returns settings.xml content with the whole Development category removed.

    Raises ValueError when the result is not well-formed XML or still carries a
    dev setting id - a packaging bug must fail the build, not ship.
    """
    stripped = _DEV_CATEGORY_RE.sub("", settings_xml_text)

    try:
        ET.fromstring(stripped)
    except ET.ParseError as e:
        raise ValueError(f"settings.xml no longer parses after dev-strip: {e}")

    for setting_id in DEV_SETTING_IDS:
        if setting_id in stripped:
            raise ValueError(
                f"dev setting '{setting_id}' survived outside the development "
                f"category - move it there or extend strip_development_settings()")

    return stripped
