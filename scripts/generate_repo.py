#!/usr/bin/env python3
"""
OpenSubtitles.com Kodi Repository Generator
Packages add-ons into zip archives, generates consolidated addons.xml with checksums,
and creates a user-friendly download portal page.
"""

import os
import re
import sys
import shutil
import zipfile
import hashlib
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from addon_manifest import iter_addon_files  # noqa: E402  - what ships lives in one place

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(REPO_ROOT, "repo_output")
ZIPS_DIR = os.path.join(OUTPUT_DIR, "zips")

EXCLUDE_PATTERNS = [
    r"^\.git",
    r"^\.github",
    r"^\.pytest_cache",
    r"^__pycache__",
    r"^repo_output",
    r"^tests",
    r"^scripts",
    r"^repository\.opensubtitles-com",
    r"^dist",
    r"^scratch",
    r"\.pyc$",
    r"^\.env$",
    r"^pytest\.ini$"
]

def should_exclude(rel_path):
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, rel_path):
            return True
    return False

def get_addon_metadata(addon_xml_path):
    tree = ET.parse(addon_xml_path)
    root = tree.getroot()
    addon_id = root.attrib.get("id")
    version = root.attrib.get("version")
    return addon_id, version, root

def zip_addon(repo_root, target_zip, prefix=""):
    """Zip the add-on from the shared allow-list in scripts/addon_manifest.py.

    Deliberately not a deny-list: a new internal file must be added to the manifest before
    it can reach users, rather than shipping until someone remembers to exclude it.
    """
    os.makedirs(os.path.dirname(target_zip), exist_ok=True)
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for full_path, rel_path in iter_addon_files(
                repo_root,
                on_missing=lambda e: print(f"⚠️  Notice: {e} does not exist, skipping.")):
            zf.write(full_path, os.path.join(prefix, rel_path) if prefix else rel_path)


def zip_directory(src_dir, target_zip, prefix="", filter_func=None):
    os.makedirs(os.path.dirname(target_zip), exist_ok=True)
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, src_dir)
                if filter_func and filter_func(rel_path):
                    continue
                archive_name = os.path.join(prefix, rel_path) if prefix else rel_path
                zf.write(full_path, archive_name)

def generate_checksums(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
    
    md5_hash = hashlib.md5(content).hexdigest()
    with open(file_path + ".md5", "w", encoding="utf-8") as f:
        f.write(md5_hash)
        
    sha256_hash = hashlib.sha256(content).hexdigest()
    with open(file_path + ".sha256", "w", encoding="utf-8") as f:
        f.write(sha256_hash)
        
    return md5_hash, sha256_hash

def build_index_html(addons_info):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenSubtitles.com Kodi Repository</title>
    <style>
        :root {{
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem 1rem;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 720px;
            width: 100%;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2.5rem;
        }}
        .logo {{
            width: 96px;
            height: 96px;
            margin-bottom: 1rem;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        }}
        h1 {{
            margin: 0 0 0.5rem 0;
            font-size: 2rem;
            font-weight: 700;
        }}
        p.subtitle {{
            color: var(--text-muted);
            margin: 0;
            font-size: 1.1rem;
        }}
        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }}
        .btn {{
            display: inline-block;
            background-color: var(--primary);
            color: #ffffff;
            font-weight: 600;
            padding: 0.875rem 1.75rem;
            border-radius: 8px;
            text-decoration: none;
            transition: background-color 0.2s ease;
            text-align: center;
            font-size: 1.1rem;
            margin: 1rem 0;
        }}
        .btn:hover {{
            background-color: var(--primary-dark);
        }}
        ol {{
            padding-left: 1.25rem;
            line-height: 1.7;
            color: var(--text);
        }}
        code {{
            background: #0f172a;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
            color: #38bdf8;
        }}
        .url-box {{
            background: #0b1329;
            border: 1px solid #0284c7;
            padding: 0.85rem 1rem;
            border-radius: 8px;
            font-family: monospace;
            font-size: 1.05rem;
            color: #38bdf8;
            word-break: break-all;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 0.75rem 0 1.25rem 0;
        }}
        .copy-btn {{
            background: #0284c7;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 0.4rem 0.8rem;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            margin-left: 0.5rem;
            white-space: nowrap;
        }}
        .copy-btn:hover {{
            background: #0369a1;
        }}
        .method-tag {{
            display: inline-block;
            background: #15803d;
            color: #ffffff;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}
        .addon-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
        }}
        .addon-item:last-child {{
            border-bottom: none;
        }}
        .badge {{
            background: #0369a1;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <svg class="logo" width="84" height="84" viewBox="0 0 96 96" fill="none" aria-label="OpenSubtitles" role="img">
                <rect x="8" y="14" width="80" height="58" rx="14" stroke="currentColor" stroke-width="7"/>
                <path d="M34 72 L30 86 L48 72 Z" fill="currentColor"/>
                <rect x="22" y="44" width="34" height="7" rx="3.5" fill="currentColor"/>
                <rect x="60" y="44" width="14" height="7" rx="3.5" fill="currentColor"/>
                <rect x="22" y="56" width="52" height="7" rx="3.5" fill="currentColor"/>
            </svg>
            <h1>OpenSubtitles.com Repository</h1>
            <p class="subtitle">Official Fast-Track Update Repository for Kodi</p>
        </div>

        <div class="card">
            <span class="method-tag">Recommended for Smart TVs, FireStick, Android TV & PC</span>
            <h2 style="margin-top: 0.25rem;">📱 Method 1: Install Directly in Kodi (File Manager)</h2>
            <p style="color: var(--text-muted); margin-bottom: 0.5rem;">No web browser or USB drive needed. Type or paste this URL into Kodi:</p>
            
            <div class="url-box">
                <span id="repoUrl">https://kodi.opensubtitles.com</span>
                <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('repoUrl').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy', 2000)">Copy</button>
            </div>

            <ol>
                <li>In Kodi, enable <strong>Unknown sources</strong> under <strong>Settings (⚙️) ➔ System ➔ Add-ons</strong>.</li>
                <li>Go to <strong>Settings (⚙️) ➔ File manager ➔ Add source</strong>.</li>
                <li>Click <code>&lt;None&gt;</code> and enter the URL above: <code>https://kodi.opensubtitles.com</code></li>
                <li>Set the media source name to: <strong><code>OpenSubtitles-repo</code></strong> and click <strong>OK</strong>.</li>
                <li>Go to <strong>Add-ons ➔ Install from zip file ➔ OpenSubtitles-repo</strong>.</li>
                <li>Select <strong><code>repository.opensubtitles-com.zip</code></strong> and wait for installation confirmation.</li>
                <li>Go to <strong>Install from repository ➔ OpenSubtitles.com Official Repository ➔ Subtitles ➔ OpenSubtitles.com</strong> and click <strong>Install</strong>.</li>
            </ol>
        </div>

        <div class="card">
            <h2 style="margin-top: 0.25rem;">💻 Method 2: Direct Zip Download</h2>
            <p style="color: var(--text-muted);">For offline installation, or devices that cannot reach the repository directly:</p>
            <div style="text-align: center;">
                <a class="btn" href="repository.opensubtitles-com.zip">⬇️ Download repository.opensubtitles-com.zip</a>
            </div>
            <ol>
                <li>In Kodi, go to <strong>Add-ons ➔ Install from zip file</strong> and select the downloaded file.</li>
                <li>Then choose <strong>Install from repository ➔ OpenSubtitles.com Official Repository ➔ Subtitles ➔ OpenSubtitles.com</strong>.</li>
            </ol>
        </div>

        <div class="card">
            <h3>⚙️ Configuration</h3>
            <ol>
                <li>Open add-on <strong>Settings</strong>:
                    <ul>
                        <li>Enter your OpenSubtitles.com <strong>Username</strong> and <strong>Password</strong>.</li>
                        <li>Click <strong>Test Connection</strong> to verify your account and daily quota.</li>
                    </ul>
                </li>
                <li>In Kodi <strong>Settings ➔ Player ➔ Language ➔ Subtitle Services</strong>, set both <em>Default movie service</em> and <em>Default TV show service</em> to <strong>OpenSubtitles.com</strong>.</li>
                <li>Recommended: in the same <strong>Language</strong> screen, pick your <em>Languages to download subtitles for</em> - with nothing selected, searches return subtitles in <strong>all</strong> languages.</li>
            </ol>
        </div>

        <div class="card">
            <h3>🔗 Project Links</h3>
            <p>
                <a href="https://github.com/opensubtitles-dev/service.subtitles.opensubtitles-com">Source on GitHub</a> ·
                <a href="https://github.com/opensubtitles-dev/service.subtitles.opensubtitles-com/issues">Report an issue</a> ·
                <a href="https://forum.opensubtitles.com/t/new-opensubtitles-com-kodi-subtitles-addon/1673">Forum thread</a> ·
                <a href="https://opensubtitles.stoplight.io/">API documentation</a> ·
                <a href="https://www.opensubtitles.com">OpenSubtitles.com</a>
            </p>

            <h3>📦 Available Packages</h3>
"""
    for addon_id, ver in addons_info:
        html += f"""            <div class="addon-item">
                <div>
                    <strong>{addon_id}</strong>
                </div>
                <span class="badge">v{ver}</span>
            </div>\n"""

    html += """        </div>
    </div>
</body>
</html>
"""
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

def main():
    print("=" * 60)
    print("Building OpenSubtitles.com Kodi Repository")
    print("=" * 60)

    # 1. Clean output directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(ZIPS_DIR, exist_ok=True)

    addons_info = []
    addons_root = ET.Element("addons")

    # 2. Package service.subtitles.opensubtitles-com
    sub_xml = os.path.join(REPO_ROOT, "addon.xml")
    sub_id, sub_ver, sub_root = get_addon_metadata(sub_xml)
    addons_info.append((sub_id, sub_ver))
    addons_root.append(sub_root)

    sub_zip_dir = os.path.join(ZIPS_DIR, sub_id)
    os.makedirs(sub_zip_dir, exist_ok=True)
    sub_zip_file = os.path.join(sub_zip_dir, f"{sub_id}-{sub_ver}.zip")
    
    print(f"📦 Packaging {sub_id} v{sub_ver} -> {sub_zip_file}")
    # Allow-list, shared with build_release_zip.py. This was a deny-list until v1.0.16,
    # which is how v1.0.15 published AGENT_INSTRUCTIONS.md, DEV_WORKFLOW.md,
    # KODI_STANDARDS.md and TODO.md to every user installing from the repository: no rule
    # excluded them, and .gitattributes' export-ignore does not apply here (that is
    # `git archive` only).
    zip_addon(REPO_ROOT, sub_zip_file, prefix=sub_id)

    for asset_file in ("addon.xml", "changelog.txt", "icon.png", "fanart.jpg"):
        src = os.path.join(REPO_ROOT, asset_file)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(sub_zip_dir, asset_file))

    # 3. Package repository.opensubtitles-com dynamically
    repo_id = "repository.opensubtitles-com"
    repo_ver = "1.1.0"
    # version comes from repo_ver above - a hardcoded one here once shipped a
    # bumped zip whose addon.xml still said 1.0.0, so Kodi never updated it
    repo_xml_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<addon id="repository.opensubtitles-com"
       name="OpenSubtitles.com Official Repository"
       version="{repo_ver}"
       provider-name="OpenSubtitles">
	<extension point="xbmc.addon.repository" name="OpenSubtitles.com Official Repository">
		<dir>
			<info compressed="false">https://kodi.opensubtitles.com/addons.xml</info>
			<checksum>https://kodi.opensubtitles.com/addons.xml.md5</checksum>
			<datadir zip="true">https://kodi.opensubtitles.com/zips/</datadir>
			<hashes>false</hashes>
		</dir>
	</extension>
	<extension point="xbmc.addon.metadata">
		<summary lang="en_GB">Official repository for OpenSubtitles.com Kodi add-ons</summary>
		<description lang="en_GB">Download and automatically receive instant updates for OpenSubtitles.com subtitle add-ons directly from the official developer source.</description>
		<disclaimer lang="en_GB">Maintained by OpenSubtitles.com</disclaimer>
		<platform>all</platform>
		<license>GPL-2.0-only</license>
		<website>https://www.opensubtitles.com</website>
		<source>https://github.com/opensubtitles/service.subtitles.opensubtitles-com</source>
		<assets>
			<icon>icon.png</icon>
			<fanart>fanart.jpg</fanart>
		</assets>
	</extension>
</addon>
"""
    repo_root_xml = ET.fromstring(repo_xml_content)
    addons_info.append((repo_id, repo_ver))
    addons_root.append(repo_root_xml)

    repo_zip_dir = os.path.join(ZIPS_DIR, repo_id)
    os.makedirs(repo_zip_dir, exist_ok=True)
    repo_zip_file = os.path.join(repo_zip_dir, f"{repo_id}-{repo_ver}.zip")
    
    print(f"📦 Packaging {repo_id} v{repo_ver} -> {repo_zip_file}")
    
    # Create temp staging dir for repository addon
    temp_repo_stage = os.path.join(OUTPUT_DIR, "_temp_repo_stage")
    os.makedirs(temp_repo_stage, exist_ok=True)
    with open(os.path.join(temp_repo_stage, "addon.xml"), "w", encoding="utf-8") as f:
        f.write(repo_xml_content)
    shutil.copy(os.path.join(REPO_ROOT, "icon.png"), os.path.join(temp_repo_stage, "icon.png"))
    shutil.copy(os.path.join(REPO_ROOT, "fanart.jpg"), os.path.join(temp_repo_stage, "fanart.jpg"))
    
    zip_directory(temp_repo_stage, repo_zip_file, prefix=repo_id)

    # Copy files to repo_zip_dir for repository listing
    shutil.copy(os.path.join(temp_repo_stage, "addon.xml"), os.path.join(repo_zip_dir, "addon.xml"))
    shutil.copy(os.path.join(temp_repo_stage, "icon.png"), os.path.join(repo_zip_dir, "icon.png"))
    shutil.copy(os.path.join(temp_repo_stage, "fanart.jpg"), os.path.join(repo_zip_dir, "fanart.jpg"))
    
    # Cleanup temp stage
    shutil.rmtree(temp_repo_stage)

    # Also copy repository.opensubtitles-com.zip to root output for direct link
    shutil.copy(repo_zip_file, os.path.join(OUTPUT_DIR, "repository.opensubtitles-com.zip"))

    # 4. Generate addons.xml & checksums
    addons_xml_path = os.path.join(OUTPUT_DIR, "addons.xml")
    tree = ET.ElementTree(addons_root)
    tree.write(addons_xml_path, encoding="utf-8", xml_declaration=True)
    
    md5_hash, sha256_hash = generate_checksums(addons_xml_path)
    print(f"📄 Generated addons.xml (MD5: {md5_hash})")

    # 5. Generate index.html portal
    build_index_html(addons_info)
    print("🌐 Generated web download portal (index.html)")

    print("\n✅ Repository build complete in 'repo_output/'")

if __name__ == "__main__":
    main()
