"""Guards the glyph rendering test harness used by the test_flag_interceptor setting.

The harness only works if the printed codepoint really names the printed glyph -
otherwise a blank rectangle on screen is attributed to the wrong character and the
compatibility matrix in docs/kodi_ui_font_compatibility.md records a wrong result.
"""
from resources.lib.subtitle_downloader import GLYPH_TEST_ROWS, _mock_subtitle


def test_every_codepoint_label_matches_its_glyph():
    for tag, _color, glyphs in GLYPH_TEST_ROWS:
        for glyph, codepoint in glyphs:
            assert f"{ord(glyph):04X}" == codepoint.upper(), \
                f"{tag} row: {glyph!r} is U+{ord(glyph):04X}, labelled {codepoint}"


def test_no_glyph_is_tested_twice():
    seen = {}
    for _tag, _color, glyphs in GLYPH_TEST_ROWS:
        for glyph, codepoint in glyphs:
            assert glyph not in seen, f"{glyph!r} ({codepoint}) already tested as {seen[glyph]}"
            seen[glyph] = codepoint


def test_tiers_stay_grouped_ok_then_try_then_fail():
    order = {"OK": 0, "TRY": 1, "FAIL": 2}
    tiers = [order[tag] for tag, _color, _glyphs in GLYPH_TEST_ROWS]
    assert tiers == sorted(tiers), "confirmed-good rows must render above untested and failing rows"


def test_mock_subtitle_matches_provider_result_shape():
    sub = _mock_subtitle("mock_x", "en", "GLYPH 01 OK", 990001, title="GLYPH")
    attributes = sub["attributes"]

    assert sub["id"] == "mock_x"
    assert attributes["files"][0]["file_id"] == 990001
    assert attributes["feature_details"]["title"] == "GLYPH"
    # Flags default off so glyph rows render without extra badges appended to the label.
    for flag in ("from_trusted", "moviehash_match", "hearing_impaired",
                 "ai_translated", "machine_translated", "foreign_parts_only"):
        assert attributes[flag] is False
