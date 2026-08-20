import os
import xml.etree.ElementTree as ET
import subprocess
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_ADDON_DIR = os.path.join(REPO_ROOT, "repository.opensubtitles-com")
REPO_ADDON_XML = os.path.join(REPO_ADDON_DIR, "addon.xml")
GENERATE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "generate_repo.py")

def test_repository_addon_xml_validity():
    output_dir = os.path.join(REPO_ROOT, "repo_output")
    repo_xml = os.path.join(output_dir, "zips", "repository.opensubtitles-com", "addon.xml")
    if not os.path.isfile(repo_xml):
        subprocess.run(["python3", GENERATE_SCRIPT], cwd=REPO_ROOT, check=True)
    
    assert os.path.isfile(repo_xml), "Generated repository addon.xml must exist"
    tree = ET.parse(repo_xml)
    root = tree.getroot()
    assert root.tag == "addon"
    assert root.attrib.get("id") == "repository.opensubtitles-com"
    assert root.attrib.get("version") is not None
    
    # Check repository extension point
    repo_ext = root.find(".//extension[@point='xbmc.addon.repository']")
    assert repo_ext is not None
    dir_elem = repo_ext.find("dir")
    assert dir_elem is not None
    assert dir_elem.find("info") is not None
    assert dir_elem.find("checksum") is not None
    assert dir_elem.find("datadir") is not None

def test_generate_repo_script_execution():
    result = subprocess.run(["python3", GENERATE_SCRIPT], cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, f"generate_repo.py failed:\n{result.stderr}"
    
    output_dir = os.path.join(REPO_ROOT, "repo_output")
    assert os.path.isfile(os.path.join(output_dir, "addons.xml"))
    assert os.path.isfile(os.path.join(output_dir, "addons.xml.md5"))
    assert os.path.isfile(os.path.join(output_dir, "addons.xml.sha256"))
    assert os.path.isfile(os.path.join(output_dir, "index.html"))
    assert os.path.isfile(os.path.join(output_dir, "repository.opensubtitles-com.zip"))
    
    # Verify consolidated addons.xml has both addons
    addons_tree = ET.parse(os.path.join(output_dir, "addons.xml"))
    addon_ids = [a.attrib.get("id") for a in addons_tree.getroot().findall("addon")]
    assert "service.subtitles.opensubtitles-com" in addon_ids
    assert "repository.opensubtitles-com" in addon_ids
