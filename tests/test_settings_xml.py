import os
import re
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SETTINGS_XML_PATH = os.path.join(REPO_ROOT, "resources", "settings.xml")
STRINGS_PO_PATH = os.path.join(REPO_ROOT, "resources", "language", "resource.language.en_GB", "strings.po")

def test_settings_xml_syntax_and_structure():
    assert os.path.isfile(SETTINGS_XML_PATH), "resources/settings.xml must exist"
    tree = ET.parse(SETTINGS_XML_PATH)
    root = tree.getroot()
    assert root.tag == "settings"
    assert root.attrib.get("version") == "1"

    categories = root.findall(".//category")
    assert len(categories) >= 3, "settings.xml should contain 'user', 'filter', and 'debug' categories"
    
    category_ids = [c.attrib.get("id") for c in categories]
    assert "user" in category_ids
    assert "filter" in category_ids
    assert "debug" in category_ids

def test_all_expected_setting_ids_exist():
    tree = ET.parse(SETTINGS_XML_PATH)
    root = tree.getroot()
    
    settings = root.findall(".//setting")
    setting_ids = {s.attrib.get("id"): s for s in settings}
    
    expected_ids = [
        "OSuser",
        "OSpass",
        "account_status",
        "account_details",
        "account_verified_at",
        "APIKey",
        "test_connection",
        "hearing_impaired",
        "foreign_parts_only",
        "machine_translated",
        "ai_translated",
        "addon_version",
        "search_cache_duration",
        "clear_cache"
    ]
    
    for expected_id in expected_ids:
        assert expected_id in setting_ids, f"Setting '{expected_id}' is missing from settings.xml"

    # Verify account_status and account_details are non-editable
    for readonly_id in ("account_status", "account_details"):
        dep = setting_ids[readonly_id].find(".//dependencies/dependency[@type='enable']")
        assert dep is not None and dep.text == "false", f"Setting '{readonly_id}' must have enable=false dependency"

def test_debug_settings_are_expert_level():
    tree = ET.parse(SETTINGS_XML_PATH)
    root = tree.getroot()
    
    debug_category = root.find(".//category[@id='debug']")
    assert debug_category is not None

    # All settings in debug category must be level 3 (Expert level)
    for setting in debug_category.findall(".//setting"):
        level = setting.find("level")
        assert level is not None and level.text == "3", f"Setting {setting.attrib.get('id')} in debug category should be level 3 (Expert)"

def test_settings_constraints_and_options():
    tree = ET.parse(SETTINGS_XML_PATH)
    root = tree.getroot()
    
    # Filter settings should allow 'include', 'exclude', 'only'
    filter_settings = ["hearing_impaired", "foreign_parts_only", "machine_translated", "ai_translated"]
    for s_id in filter_settings:
        elem = root.find(f".//setting[@id='{s_id}']")
        assert elem is not None
        options = [opt.text for opt in elem.findall(".//options/option")]
        assert sorted(options) == ["exclude", "include", "only"], f"Invalid options for {s_id}: {options}"

    # search_cache_duration constraints
    cache_elem = root.find(".//setting[@id='search_cache_duration']")
    assert cache_elem is not None
    assert cache_elem.attrib.get("type") == "integer"
    min_val = cache_elem.find(".//constraints/minimum")
    max_val = cache_elem.find(".//constraints/maximum")
    assert min_val is not None and int(min_val.text) == 0
    assert max_val is not None and int(max_val.text) >= 60

def test_settings_labels_exist_in_strings_po():
    tree = ET.parse(SETTINGS_XML_PATH)
    root = tree.getroot()
    
    # Collect all label and heading IDs from settings.xml
    label_ids = set()
    for elem in root.iter():
        if "label" in elem.attrib and elem.attrib["label"].isdigit():
            label_ids.add(int(elem.attrib["label"]))
        heading = elem.find("heading")
        if heading is not None and heading.text and heading.text.isdigit():
            label_ids.add(int(heading.text))
            
    assert len(label_ids) > 0, "No numeric string label IDs found in settings.xml"
    
    # Parse en_GB strings.po without external dependencies
    with open(STRINGS_PO_PATH, "r", encoding="utf-8") as f:
        po_content = f.read()
    
    po_ids = set(int(x) for x in re.findall(r'msgctxt\s+"#(\d+)"', po_content))
            
    for label_id in label_ids:
        assert label_id in po_ids, f"String ID #{label_id} used in settings.xml is missing from en_GB strings.po"
