"""Guard the standalone scripts that settings.xml launches with RunScript().

Kodi runs `RunScript(<file path>)` as a script "invoked without an addon": it appends
*every* installed add-on's library directory to sys.path and puts ours LAST. Any other
add-on shipping a top-level `resources` package then wins `import resources` and our own
modules become invisible - `ModuleNotFoundError: No module named 'resources.lib.osclient'`.

That bug hit real users twice (issue #39, support ticket #168978). It was fixed in v1.0.11
by adding an import-path guard to test_connection.py, then silently reintroduced in v1.0.15
when commit f6af61de rewrote that file and dropped the block along with its comment - with
all 62 tests still passing, because nothing checked for it.

These tests exist so a third occurrence fails here instead of on a user's TV.
"""
import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_XML = os.path.join(REPO_ROOT, "resources", "settings.xml")
BUILD_SCRIPT = os.path.join(REPO_ROOT, "scripts", "build_release_zip.py")


def _runscript_targets():
    """Every add-on script settings.xml launches via RunScript(), as bare filenames."""
    with open(SETTINGS_XML, encoding="utf-8") as fh:
        settings = fh.read()
    targets = re.findall(r"RunScript\(\s*([^)\s,]+)", settings)
    return sorted({os.path.basename(t) for t in targets if t.endswith(".py")})


def test_settings_xml_declares_runscript_entrypoints():
    """Sanity: the extraction works, so the tests below are not vacuously passing."""
    targets = _runscript_targets()
    assert targets, "no RunScript() targets found in settings.xml - has the format changed?"
    assert "test_connection.py" in targets


@pytest.mark.parametrize("script", _runscript_targets())
def test_runscript_entrypoint_exists(script):
    assert os.path.isfile(os.path.join(REPO_ROOT, script)), (
        f"settings.xml runs {script} but it is not in the add-on root"
    )


@pytest.mark.parametrize("script", _runscript_targets())
def test_runscript_entrypoint_has_import_path_guard(script):
    """The guard must be present, and above the first `resources.*` import."""
    with open(os.path.join(REPO_ROOT, script), encoding="utf-8") as fh:
        source = fh.read()

    assert "sys.path.insert(0, _addon_path)" in source, (
        f"{script} is launched via RunScript() but has no import-path guard. Without it, "
        f"another add-on's top-level `resources` package shadows ours and the script dies "
        f"with ModuleNotFoundError. Copy the block from test_connection.py. See issue #39."
    )

    guard_at = source.index("sys.path.insert(0, _addon_path)")
    first_resources_import = min(
        (m.start() for m in re.finditer(r"^\s*(?:from|import)\s+resources\b", source, re.M)),
        default=None,
    )
    if first_resources_import is not None:
        assert guard_at < first_resources_import, (
            f"{script} imports `resources` at offset {first_resources_import} but the "
            f"import-path guard only runs at {guard_at} - too late to have any effect."
        )


@pytest.mark.parametrize("script", _runscript_targets())
def test_runscript_entrypoint_is_shipped(script):
    """A settings button that runs a file missing from the zip is a dead button."""
    if not os.path.isfile(BUILD_SCRIPT):
        pytest.skip("scripts/build_release_zip.py not present")
    with open(BUILD_SCRIPT, encoding="utf-8") as fh:
        build_src = fh.read()
    include_block = re.search(r"INCLUDE_ENTRIES\s*=\s*\{(.*?)\}", build_src, re.S)
    assert include_block, "could not find INCLUDE_ENTRIES in build_release_zip.py"
    assert f'"{script}"' in include_block.group(1), (
        f"{script} is launched from settings.xml but is not in INCLUDE_ENTRIES, so release "
        f"zips will not contain it and the button will do nothing."
    )
