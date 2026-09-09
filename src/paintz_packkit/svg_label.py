from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os
import xml.etree.ElementTree as ET

from PIL import Image, ImageFont

from .finish import DEFAULT_APPEARANCE, render_surface

FRONT_WIDTH = 0.40
VIEWBOX_SIZE = 1000.0
DARK_HEX = "#1D1F1B"
LIGHT_HEX = "#EFEEDC"
CREAM_HEX = "#E0DABF"
RED_HEX = "#992D26"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def _candidate_roots(repo_root: Path | None = None):
    seen: set[Path] = set()
    if repo_root is not None:
        resolved = Path(repo_root).resolve()
        seen.add(resolved)
        yield resolved
    cwd = Path.cwd().resolve()
    if cwd not in seen:
        seen.add(cwd)
        yield cwd
    for parent in Path(__file__).resolve().parents:
        if parent not in seen:
            seen.add(parent)
            yield parent


def _find_asset(relative: Path, repo_root: Path | None = None) -> Path | None:
    for root in _candidate_roots(repo_root):
        candidate = root / relative
        if candidate.exists():
            return candidate
    return None


def find_font(repo_root: Path | None = None) -> Path | None:
    env = os.environ.get("PAINTZ_PACKKIT_FONT") or os.environ.get("PAINTZ_FONT") or os.environ.get("PAINTZ_FONT_DISPLAY")
    if env and Path(env).exists():
        return Path(env)

    bundled = _find_asset(Path("assets/fonts/BarlowCondensed-Black.ttf"), repo_root)
    if bundled:
        return bundled

    fallbacks = [
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for path in fallbacks:
        if path.exists():
            return path
    return None


def find_text_font(repo_root: Path | None = None) -> Path | None:
    env = os.environ.get("PAINTZ_PACKKIT_FONT_TEXT") or os.environ.get("PAINTZ_FONT_TEXT")
    if env and Path(env).exists():
        return Path(env)
    bundled = _find_asset(Path("assets/fonts/BarlowCondensed-SemiBold.ttf"), repo_root)
    if bundled:
        return bundled
    return find_font(repo_root)


def _require_fonts(repo_root: Path) -> tuple[Path, Path]:
    display = find_font(repo_root)
    text = find_text_font(repo_root)
    if not display or not text:
        raise FileNotFoundError(
            "No usable label font found. Install/copy Barlow Condensed into assets/fonts, "
            "set PAINTZ_PACKKIT_FONT/PAINTZ_PACKKIT_FONT_TEXT, or use a normal Windows/Linux font install."
        )
    return display, text


def _require_template(repo_root: Path) -> Path:
    template = _find_asset(Path("assets/templates/can_design3.svg"), repo_root)
    if not template:
        raise FileNotFoundError("PaintZ can SVG template not found: assets/templates/can_design3.svg")
    return template


def _font_family(path: Path) -> str:
    name = path.name.casefold()
    if "barlow" in name:
        return "Barlow Condensed"
    if "dejavu" in name:
        return "DejaVu Sans"
    if "arial" in name:
        return "Arial"
    return "sans-serif"


def _fit_font_size(text: str, font_path: Path, max_width: float, start_size: int, min_size: int) -> int:
    for size in range(int(start_size), int(min_size) - 1, -1):
        font = ImageFont.truetype(str(font_path), size=size)
        box = font.getbbox(text)
        if box[2] - box[0] <= max_width:
            return size
    return int(min_size)


def _sample_front_luminance(surface: Image.Image) -> float:
    width, height = surface.size
    front_px = max(1, int(width * FRONT_WIDTH))
    x1 = (width - front_px) // 2
    x2 = x1 + front_px
    y1 = int(height * 0.12)
    y2 = int(height * 0.95)
    sample = surface.crop((x1, y1, x2, y2)).resize((1, 1), Image.Resampling.BOX).convert("RGB").getpixel((0, 0))
    return (0.2126 * sample[0] + 0.7152 * sample[1] + 0.0722 * sample[2]) / 255.0


def _elements_by_id(root: ET.Element) -> dict[str, ET.Element]:
    return {element_id: element for element in root.iter() if (element_id := element.get("id"))}


def _set_text(element: ET.Element, value: str):
    for child in list(element):
        element.remove(child)
    element.text = value


def _prepare_svg(surface: Image.Image, paint: dict, code: str, repo_root: Path) -> tuple[str, list[str]]:
    template_path = _require_template(repo_root)
    display_font, text_font = _require_fonts(repo_root)
    tree = ET.parse(template_path)
    root = tree.getroot()
    root.set("viewBox", f"0 0 {VIEWBOX_SIZE:g} {VIEWBOX_SIZE:g}")
    root.set("width", str(surface.width))
    root.set("height", str(surface.height))

    elements = _elements_by_id(root)
    required = {"logo", "logo-z", "paint-code", "paint-name", "divider", "badge", "series", "badge-line-2", "badge-line-3", "footer"}
    missing = required - set(elements)
    if missing:
        raise ValueError("PaintZ SVG missing elements: " + ", ".join(sorted(missing)))

    name = str(paint["name"]).upper()
    code_text = str(code).upper()
    paint_type = str(paint.get("type", "")).lower()
    if paint_type == "camo":
        series = "CAMO SERIES"
    elif paint.get("pattern"):
        series = "PATTERN SERIES"
    else:
        series = "SOLID SERIES"
    badge_line_2 = str(paint.get("badge_text") or "TACTICAL SURFACES").upper()
    badge_line_3 = str(paint.get("field_text") or "FIELD PROVEN").upper()
    footer = str(paint.get("footer_text") or "SPRAY • CUSTOMIZE • SURVIVE").upper()

    for key, value in {
        "paint-code": code_text,
        "paint-name": name,
        "series": series,
        "badge-line-2": badge_line_2,
        "badge-line-3": badge_line_3,
        "footer": footer,
    }.items():
        _set_text(elements[key], value)

    _set_text(elements["logo"], "Paint")
    _set_text(elements["logo-z"], "Z")
    elements["logo-z"].set("fill", RED_HEX)

    center_x = VIEWBOX_SIZE / 2.0
    front_width = VIEWBOX_SIZE * FRONT_WIDTH
    badge_width = front_width * 0.92
    badge_x = center_x - badge_width / 2.0
    elements["badge"].set("x", f"{badge_x:.2f}")
    elements["badge"].set("width", f"{badge_width:.2f}")
    divider_width = front_width * 0.60
    elements["divider"].set("x1", f"{center_x - divider_width / 2.0:.2f}")
    elements["divider"].set("x2", f"{center_x + divider_width / 2.0:.2f}")

    sizes = {
        "logo": _fit_font_size("PaintZ", display_font, front_width * 0.92, int(front_width * 0.38), 55),
        "paint-code": _fit_font_size(code_text, display_font, front_width * 0.92, int(front_width * 0.12), 16),
        "paint-name": _fit_font_size(name, display_font, front_width * 0.94, int(front_width * 0.15), 25),
        "series": _fit_font_size(series, display_font, badge_width * 0.84, int(front_width * 0.085), 18),
        "badge-line-2": _fit_font_size(badge_line_2, text_font, badge_width * 0.86, int(front_width * 0.067), 16),
        "badge-line-3": _fit_font_size(badge_line_3, text_font, badge_width * 0.86, int(front_width * 0.067), 16),
        "footer": _fit_font_size(footer, text_font, front_width * 0.96, int(front_width * 0.064), 14),
    }
    display_family = _font_family(display_font)
    text_family = _font_family(text_font)
    for key, size in sizes.items():
        elements[key].set("font-size", str(size))
        elements[key].set("font-family", text_family if key in {"badge-line-2", "badge-line-3", "footer"} else display_family)

    logo_size = sizes["logo"]
    logo_font = ImageFont.truetype(str(display_font), size=logo_size)
    paint_box = logo_font.getbbox("Paint")
    z_box = logo_font.getbbox("Z")
    paint_width = paint_box[2] - paint_box[0]
    z_width = z_box[2] - z_box[0]
    logo_start = center_x - (paint_width + z_width) / 2.0
    elements["logo"].set("text-anchor", "start")
    elements["logo"].set("x", f"{logo_start:.2f}")
    elements["logo-z"].set("text-anchor", "start")
    elements["logo-z"].set("x", f"{logo_start + paint_width:.2f}")
    elements["logo-z"].set("font-size", str(logo_size))
    elements["logo-z"].set("font-family", display_family)

    luminance = _sample_front_luminance(surface)
    ink, halo = (DARK_HEX, LIGHT_HEX) if luminance >= 0.50 else (LIGHT_HEX, DARK_HEX)
    for element_id in ("logo", "paint-code", "paint-name", "footer"):
        elements[element_id].set("fill", ink)
        elements[element_id].set("stroke", halo)
    elements["logo-z"].set("fill", RED_HEX)
    elements["logo-z"].set("stroke", halo)
    elements["divider"].set("stroke", ink)
    elements["series"].set("fill", LIGHT_HEX)
    elements["badge-line-2"].set("fill", CREAM_HEX)
    elements["badge-line-3"].set("fill", CREAM_HEX)

    return ET.tostring(root, encoding="unicode"), [str(display_font), str(text_font)]


def _rasterize_svg(svg_string: str, font_files: list[str], width: int, height: int) -> Image.Image:
    try:
        import resvg_py

        png_bytes = resvg_py.svg_to_bytes(
            svg_string=svg_string,
            width=width,
            height=height,
            skip_system_fonts=False,
            font_files=font_files,
            shape_rendering="geometric_precision",
            text_rendering="geometric_precision",
            image_rendering="optimize_quality",
        )
    except ImportError:
        try:
            import cairosvg
        except ImportError as exc:
            raise RuntimeError(
                "PaintZ PackKit needs an SVG renderer. Install resvg_py (preferred) or CairoSVG."
            ) from exc
        png_bytes = cairosvg.svg2png(
            bytestring=svg_string.encode("utf-8"),
            output_width=width,
            output_height=height,
        )

    with Image.open(BytesIO(png_bytes)) as image:
        return image.convert("RGBA")


def render_label(
    base: Image.Image,
    paint: dict,
    code: str,
    repo_root: Path,
    appearance_cfg: dict | None = None,
) -> Image.Image:
    appearance_cfg = appearance_cfg or DEFAULT_APPEARANCE
    surface = render_surface(
        paint=paint,
        code=code,
        repo_root=repo_root,
        size=base.size,
        appearance_cfg=appearance_cfg,
    )
    svg_string, fonts = _prepare_svg(surface, paint, code, repo_root)
    overlay = _rasterize_svg(svg_string, fonts, surface.width, surface.height)
    surface.alpha_composite(overlay)
    return surface
