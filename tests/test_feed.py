import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

spec = importlib.util.spec_from_file_location("build_feed", Path(__file__).resolve().parents[1] / "posts" / "build_feed.py")
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)


def test_feed_is_valid_xml_newest_first_and_escaped():
    xml = bf.build([{"title": "A & B", "slug": "a", "date": "2026-01-01", "summary": "<x>"},
                    {"title": "C", "slug": "c", "date": "2026-02-01", "summary": "s"}])
    items = ET.fromstring(xml).findall("./channel/item")
    assert [i.find("title").text for i in items] == ["C", "A & B"]
    assert items[1].find("description").text == "<x>"
    assert items[0].find("link").text.endswith("/posts/c.html")
