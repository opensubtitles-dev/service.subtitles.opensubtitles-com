"""Single source of truth for what goes into a shipped add-on zip.

Both packaging paths import this:

  * scripts/build_release_zip.py  - a one-off zip for manual install
  * scripts/generate_repo.py      - the zip published to GitHub Pages, which is what users
                                    installing from the OpenSubtitles repository receive

They used to disagree. `build_release_zip.py` had an allow-list, `generate_repo.py` had a
deny-list, and the two drifted:

  * v1.0.15 shipped AGENT_INSTRUCTIONS.md, DEV_WORKFLOW.md, KODI_STANDARDS.md and TODO.md to
    every user installing from the repository, because the deny-list had no rule for them.
    (`.gitattributes` marks them export-ignore, but that only applies to `git archive`.)
  * check_updates.py was missing from the allow-list, so the "Check for updates" button did
    nothing in manually built zips.

An allow-list is the safer default: a new internal file is excluded until someone
deliberately adds it, rather than shipped until someone remembers to exclude it. Anything
not listed here does not reach users.
"""
import os
import re

# Repo-root files and directories that make up the add-on. Directories are included
# recursively, minus EXCLUDE_PATTERNS below.
INCLUDE_ENTRIES = {
    "addon.xml",
    "service.py",
    # every script settings.xml launches with RunScript() must be here, or the button is
    # dead in the shipped zip (tests/test_runscript_entrypoints.py enforces this)
    "test_connection.py",
    "clear_cache.py",
    "check_updates.py",
    "show_qr.py",
    "buy_credits.py",
    # background service declared in addon.xml (xbmc.service) - without it the
    # shipped add-on loses auto-download, alerts and the update check entirely
    "service_monitor.py",
    "resources",
    "icon.png",
    "fanart.jpg",
    "LICENSE.txt",
    "changelog.txt",
    "README.md",
}

# Junk that can appear *inside* an included directory - plus sensitive
# file classes that must never ride into a user-facing zip even if a build
# workspace is dirty (env files, keys, certs, logs, editor droppings).
EXCLUDE_PATTERNS = [
    r"__pycache__",
    r"\.py[cod]$",
    r"\.DS_Store$",
    r"(^|/)\.env([./]|$)",
    r"\.(log|key|pem|p12|pfx|crt|csr|sqlite|db)$",
    r"(^|/)(secrets?|credentials?)(\.|/|$)",
    r"\.(swp|swo|orig|rej|bak)$",
]


def is_excluded(rel_path):
    """True if rel_path is junk that should be dropped from an included directory."""
    return any(re.search(pattern, rel_path) for pattern in EXCLUDE_PATTERNS)


def iter_addon_files(repo_root, on_missing=None):
    """Yield (absolute_path, path_relative_to_repo_root) for everything that ships."""
    for entry in sorted(INCLUDE_ENTRIES):
        entry_path = os.path.join(repo_root, entry)
        if not os.path.exists(entry_path):
            if on_missing:
                on_missing(entry)
            continue

        if os.path.isfile(entry_path):
            yield entry_path, entry
        else:
            for dirpath, _, filenames in os.walk(entry_path):
                for filename in sorted(filenames):
                    full_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(full_path, repo_root)
                    if is_excluded(rel_path):
                        continue
                    yield full_path, rel_path
