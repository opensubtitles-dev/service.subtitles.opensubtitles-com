#!/usr/bin/env python3
"""
Clean Release Packaging Script for service.subtitles.opensubtitles-com
Packages only production runtime files into a clean Kodi installable ZIP.
"""

import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from addon_manifest import iter_addon_files  # noqa: E402  - what ships lives in one place
from release_lib import strip_development_settings  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def check_credentials_leak(root_dir):
    """Safety check: Scans files for potential sensitive information."""
    print("🔒 Performing sensitive data scan...")
    suspicious_patterns = [
        re.compile(r'password\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
        re.compile(r'bearer\s+[a-zA-Z0-9_\-\.]{30,}', re.IGNORECASE),
    ]
    for root, _, files in os.walk(root_dir):
        # Skip tests and scripts from this check
        if any(p in root for p in ["tests", "scripts", ".git", "venv", ".system_generated"]):
            continue
        for file in files:
            if file.endswith((".py", ".xml", ".json", ".txt")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_idx, line in enumerate(f, 1):
                            # Ignore settings.xml defaults or function signatures
                            if "setting id=" in line or "def " in line:
                                continue
                            for pattern in suspicious_patterns:
                                if pattern.search(line):
                                    print(f"⚠️ Warning: Possible credential leak in {file}:{line_idx} -> {line.strip()[:60]}")
                except Exception:
                    pass
    print(" Sensitive data scan complete.")

def build_zip():
    addon_xml_path = os.path.join(REPO_ROOT, "addon.xml")
    if not os.path.isfile(addon_xml_path):
        print(f"Error: {addon_xml_path} not found.")
        sys.exit(1)

    tree = ET.parse(addon_xml_path)
    root = tree.getroot()
    addon_id = root.attrib.get("id", "service.subtitles.opensubtitles-com")
    addon_version = root.attrib.get("version", "1.0.0")

    check_credentials_leak(REPO_ROOT)

    out_dir = os.path.join(REPO_ROOT, "dist")
    os.makedirs(out_dir, exist_ok=True)
    zip_filename = f"{addon_id}-{addon_version}.zip"
    zip_path = os.path.join(out_dir, zip_filename)

    print(f"\n📦 Building release archive: {zip_filename} ...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for full_path, rel_path in iter_addon_files(
                REPO_ROOT,
                on_missing=lambda e: print(f"⚠️ Notice: Entry {e} does not exist, skipping.")):
            arcname = f"{addon_id}/{rel_path}"
            if rel_path.replace(os.sep, "/") == "resources/settings.xml":
                with open(full_path, "r", encoding="utf-8") as fh:
                    zipf.writestr(arcname, strip_development_settings(fh.read()))
            else:
                zipf.write(full_path, arcname)
            print(f"  + {arcname}")

    zip_size_kb = os.path.getsize(zip_path) / 1024
    print(f"\n Successfully built: {zip_path} ({zip_size_kb:.1f} KB)")
    print(" Ready for Kodi distribution or GitHub Releases!")

if __name__ == "__main__":
    build_zip()
