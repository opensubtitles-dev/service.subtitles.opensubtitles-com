"""What reaches users must be exactly what the manifest allows.

v1.0.15 published AGENT_INSTRUCTIONS.md, DEV_WORKFLOW.md, KODI_STANDARDS.md and TODO.md in
the add-on zip served from GitHub Pages. Two things had to go wrong at once:

  * `generate_repo.py` used a deny-list with no rule for those files, while
    `build_release_zip.py` used an allow-list that did not include them - the two packaging
    paths disagreed about what ships, and only the deny-list one was published;
  * `.gitattributes` marks them `export-ignore`, which looks like protection but applies
    only to `git archive`, not to a script walking the tree with os.walk().

`tests/test_repository_generator.py` ran the generator and checked it exited 0. Nobody
looked inside the zip. So: this file looks inside.
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

addon_manifest = pytest.importorskip("addon_manifest")


def _shipped_paths():
    return {rel for _, rel in addon_manifest.iter_addon_files(REPO_ROOT)}


# Things that exist in the working tree or the repo and must never reach a user. Some are
# gitignored (so absent from a CI checkout) but present when a maintainer builds locally,
# which DEV_WORKFLOW.md documents as a supported workflow.
FORBIDDEN_PREFIXES = ["tests", "scripts", ".github", ".git", "repo_output", "dist",
                      "three-brain-out", "tmp", ".claude", ".pytest_cache"]
FORBIDDEN_FILES = ["AGENT_INSTRUCTIONS.md", "DEV_WORKFLOW.md", "KODI_STANDARDS.md",
                   "TODO.md", "pytest.ini", ".DS_Store", ".tool-versions"]


def test_internal_docs_are_not_shipped():
    shipped = _shipped_paths()
    leaked = sorted(f for f in FORBIDDEN_FILES if f in shipped)
    assert not leaked, (
        f"internal files would be published to users: {leaked}. These are for maintainers. "
        f"Note that .gitattributes export-ignore does NOT protect against the packaging "
        f"scripts - only against `git archive`."
    )


def test_no_internal_directories_are_shipped():
    shipped = _shipped_paths()
    leaked = sorted(p for p in shipped
                    if any(p == d or p.startswith(d + os.sep) for d in FORBIDDEN_PREFIXES))
    assert not leaked, f"internal directories would be published to users: {leaked[:10]}"


def test_the_addon_still_works_when_shipped():
    """Guard the opposite failure: an allow-list that forgets something essential."""
    shipped = _shipped_paths()
    for essential in ("addon.xml", "service.py", "resources/settings.xml",
                      "resources/lib/subtitle_downloader.py",
                      "resources/lib/data_collector.py"):
        assert essential.replace("/", os.sep) in shipped, f"{essential} is missing from the zip"

    languages = [p for p in shipped if "resource.language." in p]
    assert languages, "no language files would be shipped - the add-on would be untranslated"


def test_both_packaging_scripts_use_the_shared_manifest():
    """The v1.0.15 bug was two scripts disagreeing. Keep them on one list."""
    for script in ("build_release_zip.py", "generate_repo.py"):
        with open(os.path.join(REPO_ROOT, "scripts", script), encoding="utf-8") as fh:
            source = fh.read()
        assert "from addon_manifest import" in source, (
            f"scripts/{script} does not use the shared manifest, so the two packaging paths "
            f"can drift apart again - which is exactly how internal docs shipped in v1.0.15."
        )
