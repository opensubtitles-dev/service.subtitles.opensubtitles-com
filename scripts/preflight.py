"""One-command release gate. Run before every push; wired as the pre-push hook.

    python3 scripts/preflight.py            # full gate
    python3 scripts/preflight.py --fast     # tests + consistency only (no checker)

Exists because of the v1.0.15 lesson (PR #42 review): every historical escape -
the lost RunScript guard, the zip missing check_updates.py, internal docs shipped
to users, the semantically-broken merge - passed the then-current test suite.
Each gate below guards one of those classes:

  1. pytest                - unit/behavior regressions
  2. version consistency   - addon.xml == changelog == settings version row
  3. built-zip inspection  - build the REAL artifact and look inside it
  4. kodi-addon-checker    - Kodi repo compliance (matrix + omega)
"""

import io
import os
import re
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILURES = []


def gate(name):
    print(f"\n=== preflight: {name} ===")


def fail(msg):
    FAILURES.append(msg)
    print(f"  FAIL: {msg}")


def run_pytest():
    gate("pytest")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=REPO)
    if r.returncode != 0:
        fail("pytest suite failed")


def check_version_consistency():
    gate("version consistency")
    addon_xml = open(os.path.join(REPO, "addon.xml"), encoding="utf-8").read()
    version = re.search(r'id="service\.subtitles\.opensubtitles-com"[^>]*?version="([\d.]+)"',
                        addon_xml, re.DOTALL).group(1)
    print(f"  addon.xml: {version}")

    changelog_head = open(os.path.join(REPO, "changelog.txt"), encoding="utf-8").readline()
    if f"v{version}" not in changelog_head:
        fail(f"changelog.txt first line ({changelog_head.strip()!r}) is not v{version}")

    # No translation string may hardcode a version number (1.0.16 shipped a row
    # saying "Version 1.0.15" because the .po was forgotten at bump time).
    po = open(os.path.join(REPO, "resources/language/resource.language.en_GB/strings.po"),
              encoding="utf-8").read()
    hardcoded = re.findall(r'msgid "[^"]*\b\d+\.\d+\.\d+[^"]*"', po)
    if hardcoded:
        fail(f"version number hardcoded in translation strings: {hardcoded}")

    news = re.search(r"<news>(.*?)</news>", addon_xml, re.DOTALL).group(1)
    if len(news) >= 1500:
        fail(f"addon.xml <news> is {len(news)} chars (schema limit 1500)")


def inspect_built_zip():
    gate("built-zip inspection (the artifact users actually get)")
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    from addon_manifest import iter_addon_files
    from release_lib import DEV_SETTING_IDS, strip_development_settings

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for full_path, rel_path in iter_addon_files(REPO, on_missing=lambda e: fail(f"manifest entry missing on disk: {e}")):
            if rel_path.replace(os.sep, "/") == "resources/settings.xml":
                z.writestr(rel_path, strip_development_settings(open(full_path, encoding="utf-8").read()))
            else:
                z.write(full_path, rel_path)
    z = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
    names = z.namelist()

    # Every RunScript target + the service must ship, each with the #39 guard
    for entry in ("service.py", "service_monitor.py", "test_connection.py",
                  "clear_cache.py", "check_updates.py", "show_qr.py", "buy_credits.py"):
        if entry not in names:
            fail(f"{entry} missing from shipped zip")
        elif entry != "service.py" and entry != "service_monitor.py":
            if "_addon_path" not in z.read(entry).decode():
                fail(f"{entry} ships without the RunScript import guard (issue #39)")

    # Nothing internal may reach users
    for banned in ("AGENT_INSTRUCTIONS", "DEV_WORKFLOW", "KODI_STANDARDS", "TODO.md",
                   "HANDOVER", "tests/", "scripts/", ".github", "CLAUDE.md"):
        hits = [n for n in names if banned in n]
        if hits:
            fail(f"internal file shipped: {hits[:3]}")

    # Development settings must be stripped
    settings = z.read("resources/settings.xml").decode()
    for dev_id in DEV_SETTING_IDS:
        if dev_id in settings:
            fail(f"dev setting {dev_id} shipped in settings.xml")

    # No credential-looking strings anywhere in shipped python
    for name in names:
        if name.endswith(".py"):
            text = z.read(name).decode(errors="replace")
            if re.search(r"(password|passwd)\s*=\s*['\"][^'\"]{4,}['\"]", text, re.IGNORECASE):
                fail(f"possible hardcoded credential in {name}")
    print(f"  ok: {len(names)} files inspected")


def run_addon_checker():
    gate("kodi-addon-checker (matrix, omega)")
    if not shutil_which("kodi-addon-checker"):
        fail("kodi-addon-checker not installed (pipx install kodi-addon-checker)")
        return
    for branch in ("matrix", "omega"):
        r = subprocess.run(["kodi-addon-checker", "--branch", branch, "."],
                           cwd=REPO, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()[-1:]
        print(f"  {branch}: {tail[0] if tail else '?'}")
        if "we found no problems" not in (r.stdout + r.stderr).lower():
            fail(f"kodi-addon-checker ({branch}) reports problems")


def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)


def main():
    fast = "--fast" in sys.argv
    run_pytest()
    check_version_consistency()
    inspect_built_zip()
    if not fast:
        run_addon_checker()

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"PREFLIGHT FAILED - {len(FAILURES)} problem(s):")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("PREFLIGHT PASSED - safe to push")


if __name__ == "__main__":
    main()
