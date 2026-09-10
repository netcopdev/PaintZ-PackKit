from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

from paintz_packkit.svg_label import CAN_LABEL_ROTATION_DEG, RED_HEX, _prepare_svg, _rotate_label_around_can


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


def test_prepared_svg_preserves_red_z_logo_child():
    repo_root = Path(__file__).resolve().parents[1]
    surface = Image.new("RGBA", (1000, 1000), (64, 64, 64, 255))
    paint = {
        "name": "Flecktarn",
        "type": "camo",
        "pattern": "assets/pattern_sources/ftn.png",
    }

    svg_string, _ = _prepare_svg(surface, paint, "PZ-C-FTN", repo_root)
    root = ET.fromstring(svg_string)
    elements = {element.get("id"): element for element in root.iter() if element.get("id")}

    assert "logo" in elements
    assert "logo-z" in elements
    assert (elements["logo"].text or "").strip() == "Paint"
    assert (elements["logo-z"].text or "").strip() == "Z"
    assert elements["logo-z"].get("fill") == RED_HEX


def test_default_can_label_rotation_is_eight_degrees_with_wraparound():
    assert CAN_LABEL_ROTATION_DEG == 8.0

    image = Image.new("RGBA", (360, 2), (0, 0, 0, 0))
    marker = (255, 0, 0, 255)
    image.putpixel((358, 0), marker)

    rotated = _rotate_label_around_can(image)

    # At 360 px wide, 8 degrees is exactly an 8 px shift to the right.
    # ImageChops.offset wraps across the horizontal seam, as a cylindrical label must.
    assert rotated.getpixel((6, 0)) == marker
    assert rotated.getpixel((358, 0)) != marker


def test_can_label_rotation_scales_with_texture_width():
    image = Image.new("RGBA", (1024, 1), (0, 0, 0, 0))
    marker = (255, 255, 255, 255)
    image.putpixel((100, 0), marker)

    rotated = _rotate_label_around_can(image)

    # round(1024 * 8 / 360) == 23
    assert rotated.getpixel((123, 0)) == marker
