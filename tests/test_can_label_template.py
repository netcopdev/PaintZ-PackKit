from pathlib import Path
import xml.etree.ElementTree as ET


def test_design3_curated_geometry_is_preserved():
    template = Path(__file__).resolve().parents[1] / "assets" / "templates" / "can_design3.svg"
    root = ET.parse(template).getroot()
    elements = {element.get("id"): element for element in root.iter() if element.get("id")}

    assert root.get("width") == "1000"
    assert root.get("height") == "1000"
    assert root.get("viewBox") == "0 0 1000 1000"

    assert elements["logo"].get("x") == "500"
    assert elements["logo"].get("y") == "475"
    assert elements["logo"].get("font-size") == "150"

    assert elements["paint-code"].get("y") == "595"
    assert elements["paint-code"].get("font-size") == "20"

    assert elements["paint-name"].get("y") == "665"
    assert elements["paint-name"].get("font-size") == "62"

    assert elements["divider"].get("x1") == "380"
    assert elements["divider"].get("x2") == "620"
    assert elements["divider"].get("y1") == "695"

    assert elements["badge"].get("x") == "316"
    assert elements["badge"].get("y") == "730"
    assert elements["badge"].get("width") == "368"
    assert elements["badge"].get("height") == "155"

    assert elements["series"].get("y") == "775"
    assert elements["badge-line-2"].get("y") == "815"
    assert elements["badge-line-3"].get("y") == "855"
    assert elements["footer"].get("y") == "945"

    assert (elements["logo"].text or "").strip() == "Paint"
    assert (elements["logo-z"].text or "").strip() == "Z"
