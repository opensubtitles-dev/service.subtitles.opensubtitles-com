import xml.etree.ElementTree as ET
import os

def test_addon_xml_exists_and_valid():
    addon_xml_path = os.path.join(os.path.dirname(__file__), "..", "addon.xml")
    assert os.path.isfile(addon_xml_path), "addon.xml must exist in repository root"
    tree = ET.parse(addon_xml_path)
    root = tree.getroot()
    assert root.tag == "addon"
    assert root.attrib.get("id") == "service.subtitles.opensubtitles-com"

def test_addon_xml_news_tag_length():
    addon_xml_path = os.path.join(os.path.dirname(__file__), "..", "addon.xml")
    tree = ET.parse(addon_xml_path)
    root = tree.getroot()
    news_elem = root.find("./extension/news")
    if news_elem is not None and news_elem.text:
        news_text = news_elem.text.strip()
        assert len(news_text) <= 1500, f"addon.xml news tag length {len(news_text)} exceeds Kodi schema limit of 1500 chars"

def test_addon_xml_metadata_urls():
    addon_xml_path = os.path.join(os.path.dirname(__file__), "..", "addon.xml")
    tree = ET.parse(addon_xml_path)
    root = tree.getroot()
    forum = root.find("./extension/forum")
    website = root.find("./extension/website")
    source = root.find("./extension/source")

    assert forum is not None and forum.text.startswith("https://")
    assert website is not None and website.text.startswith("https://")
    assert source is not None and source.text.startswith("https://")

def test_addon_xml_declared_assets_exist():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tree = ET.parse(os.path.join(base_dir, "addon.xml"))
    root = tree.getroot()
    assets = root.find("./extension/assets")
    assert assets is not None, "<assets> element must exist in addon.xml"
    
    for child in assets:
        asset_rel_path = child.text.strip()
        asset_full_path = os.path.join(base_dir, asset_rel_path)
        assert os.path.isfile(asset_full_path), f"Declared asset {asset_rel_path} does not exist on disk"
