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
    assert len(categories) >= 5, "settings.xml should contain 'user', 'filter', 'automation', 'development', and 'debug' categories"

    category_ids = [c.attrib.get("id") for c in categories]
    assert "user" in category_ids
    assert "filter" in category_ids
    assert "automation" in category_ids
    assert "development" in category_ids
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
        "account_checked_at",
        "account_verified_at",
        "APIKey",
        "test_connection",
        "show_register_qr",
        "show_vip_qr",
        "account_is_vip",
        "ai_credits",
        "account_logged_in",
        "smart_ranking",
        "hearing_impaired",
        "foreign_parts_only",
        "machine_translated",
        "ai_translated",
        "auto_download",
        "prompt_rating",
        "test_flag_interceptor",
        "test_rating_preview",
        "auto_upload_subtitles",
        "test_nocache",
        "test_disable_query_fallback",
        "test_show_search_debug",
        "test_override_language",
        "addon_version",
        "update_last_checked",
        "update_checked_at",
        "search_cache_duration",
        "cache_stats",
        "clear_cache"
    ]
    
    for expected_id in expected_ids:
        assert expected_id in setting_ids, f"Setting '{expected_id}' is missing from settings.xml"

    # Verify account_status, account_details, account_checked_at, and cache_stats have disabled dependencies
    for readonly_id in ("account_status", "account_details", "account_checked_at", "cache_stats"):
        dep = setting_ids[readonly_id].find(".//dependencies/dependency[@type='enable']")
        assert dep is not None, f"Setting '{readonly_id}' must have an enable dependency"
        assert dep.attrib.get("operator") == "is" and dep.text == "__disabled__"

def test_debug_settings_are_expert_level():
    tree = ET.parse(SETTINGS_XML_PATH)
    root = tree.getroot()
    
    debug_category = root.find(".//category[@id='debug']")
    assert debug_category is not None

    # Debug settings are Expert (3) or hidden internal (4); the read-only
    # "Update last checked" display row is basic (0) so everyone can see it.
    for setting in debug_category.findall(".//setting"):
        s_id = setting.attrib.get("id")
        level = setting.find("level")
        expected = {"update_checked_at": ("4",)}.get(s_id, ("3", "4"))
        assert level is not None and level.text in expected, \
            f"Setting {s_id} in debug category has level {level.text if level is not None else None}, expected {expected}"

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

def test_development_category_is_last_and_expert_only():
    tree = ET.parse(SETTINGS_XML_PATH)
    root = tree.getroot()

    category_ids = [c.attrib.get("id") for c in root.findall(".//category")]
    assert category_ids[-1] == "development", f"development must be the last tab, got {category_ids}"

    # Every setting in it must be Expert level (3) so Kodi hides the whole
    # category below the Expert settings level.
    dev = root.find(".//category[@id='development']")
    for setting in dev.findall(".//setting"):
        level = setting.find("level")
        assert level is not None and level.text == "3", \
            f"{setting.attrib.get('id')} must be level 3 (Expert) to keep the tab expert-only"

def test_dependency_targets_are_defined_before_their_dependents():
    """Kodi resolves setting dependencies in definition order: a condition that
    references a LATER-defined setting silently evaluates against its default
    (observed live: Register shown despite account_logged_in=true on disk)."""
    tree = ET.parse(SETTINGS_XML_PATH)
    settings = tree.getroot().findall(".//setting")
    order = {s.attrib.get("id"): i for i, s in enumerate(settings)}

    for setting in settings:
        sid = setting.attrib.get("id")
        for dep in setting.findall(".//dependency") + setting.findall(".//condition"):
            target = dep.attrib.get("setting")
            if target and target != sid:
                assert order[target] < order[sid], \
                    f"'{sid}' depends on '{target}' which is defined later"


def test_every_option_has_a_non_empty_value():
    """Kodi SIGSEGVs (CSettingString::Deserialize null deref) on <option></option>
    with no text - crashed the whole app at startup on 2026-08-20."""
    tree = ET.parse(SETTINGS_XML_PATH)
    for option in tree.getroot().findall(".//option"):
        assert option.text and option.text.strip(), \
            f"empty option value under label={option.attrib.get('label')!r} - crashes Kodi"
