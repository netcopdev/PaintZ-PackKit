from pathlib import Path
import xml.etree.ElementTree as ET


SVG_NS = "{http://www.w3.org/2000/svg}"


def test_design3_logo_stays_in_visible_can_label_area():
    template = Path(__file__).resolve().parents[1] / "assets" / "templates" / "can_design3.svg"
    root = ET.parse(template).getroot()
    elements = {element.get("id"): element for element in root.iter() if element.get("id")}

    assert elements["logo"].get("y") == "235"
    assert elements["logo-z"].get("y") == "235"
    assert (elements["logo"].text or "").strip() == "Paint"
    assert (elements["logo-z"].text or "").strip() == "Z"
