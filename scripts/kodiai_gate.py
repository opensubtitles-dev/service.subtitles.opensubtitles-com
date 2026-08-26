#!/usr/bin/env python3
"""The deterministic checks Team Kodi's (private) Kodiai bot runs that our
other gates do not: entry-point size and dependency availability on the
official mirrors. kodi-addon-checker covers the rest; Greptile covers the
model-backed part on the internal review PRs.

Usage: python3 scripts/kodiai_gate.py [--offline]
"""
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BRANCHES = ("matrix", "nexus", "omega", "piers")
ENTRY_MAX_LINES = 15
failures = []


def fail(msg):
    failures.append(msg)
    print(f"  FAIL: {msg}")


def check_entry_points(root):
    """Kodiai WARNs when a declared extension library exceeds ~15 lines."""
    for ext in root.findall("extension"):
        lib = ext.attrib.get("library")
        if not lib:
            continue
        path = os.path.join(REPO, lib)
        if not os.path.exists(path):
            fail(f"declared entry point {lib} does not exist")
            continue
        lines = sum(1 for l in open(path, encoding="utf-8")
                    if l.strip() and not l.strip().startswith("#"))
        print(f"  entry point {lib}: {lines} code lines (max {ENTRY_MAX_LINES})")
        if lines > ENTRY_MAX_LINES:
            fail(f"{lib} has {lines} code lines - Kodiai flags entry points over {ENTRY_MAX_LINES}")


def check_dependencies(root, offline=False):
    """Every <import> version must be satisfiable on each target branch mirror."""
    for imp in root.find("requires").findall("import"):
        dep, need = imp.attrib["addon"], imp.attrib.get("version", "0")
        if dep == "xbmc.python":
            continue
        if offline:
            print(f"  dep {dep} >= {need}: skipped (offline)")
            continue
        need_parts = [int(x) for x in re.findall(r"\d+", need)[:3]]
        for branch in BRANCHES:
            url = f"https://mirrors.kodi.tv/addons/{branch}/{dep}/"
            try:
                listing = urllib.request.urlopen(url, timeout=15).read().decode("utf-8", "replace")
            except Exception as e:
                fail(f"{dep} on {branch}: mirror listing unreachable ({e})")
                continue
            versions = re.findall(re.escape(dep) + r"-([0-9.+a-z]+?)\.zip", listing)
            ok = any([int(x) for x in re.findall(r"\d+", v)[:3]] >= need_parts for v in versions)
            print(f"  dep {dep} >= {need} on {branch}: "
                  f"{'OK' if ok else 'MISSING'} (available: {', '.join(sorted(set(versions))[-3:]) or 'none'})")
            if not ok:
                fail(f"{dep} >= {need} not available on the {branch} mirror")


def main():
    offline = "--offline" in sys.argv
    root = ET.parse(os.path.join(REPO, "addon.xml")).getroot()
    print("== kodiai-equivalent gate ==")
    check_entry_points(root)
    check_dependencies(root, offline=offline)
    if failures:
        print(f"== FAILED: {len(failures)} problem(s) ==")
        sys.exit(1)
    print("== PASSED ==")


if __name__ == "__main__":
    main()
