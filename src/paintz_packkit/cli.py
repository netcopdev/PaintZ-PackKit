from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

from . import __version__
from .dayz import emit_dayz
from .ids import code_for_paint, code_to_slug, type_code
from .manifest import load_manifest
from .render import create_base, find_font, render_label, save_preview, save_preview_catalog
from .scaled_surface import render_surface_scaled


def save_png(image: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    icc_profile = image.info.get("icc_profile")
    if icc_profile:
        kwargs["icc_profile"] = icc_profile
    image.save(path, **kwargs)


def average_rgb(image: Image.Image) -> tuple[int, int, int]:
    return image.convert("RGB").resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))


def procedural_color_texture(color: str) -> str:
    value = color.lstrip("#")
    rgb = tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    normalized = tuple(component / 255.0 for component in rgb)
    return (
        "#(argb,8,8,3)color("
        f"{normalized[0]:.6f},{normalized[1]:.6f},{normalized[2]:.6f},1.0,CO)"
    )


def load_appearance_profiles(repo_root: Path) -> dict:
    candidates = [
        repo_root / "config" / "appearance_profiles.json",
        Path(__file__).resolve().parents[2] / "config" / "appearance_profiles.json",
    ]
    for path in candidates:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if "profiles" not in data or not isinstance(data["profiles"], dict) or not data["profiles"]:
                raise ValueError(f"{path}: must contain a non-empty profiles object")
            default_name = data.get("default_profile", "used")
            if default_name not in data["profiles"]:
                raise ValueError(f"Appearance default_profile {default_name!r} is not defined")
            return data
    return {
        "default_profile": "used",
        "profiles": {
            "used": {"noise": 0.07, "scratches": 0.12, "grime": 0.08, "rust": 0.0, "edgewear": 0.08}
        },
    }


def load_pattern_scales(data: dict) -> list[tuple[float, int]]:
    raw = data.get("generator", {}).get("pattern_scales", [1.0])
    if not isinstance(raw, list) or not raw:
        raise ValueError("generator.pattern_scales must be a non-empty array")
    result: list[tuple[float, int]] = []
    seen: set[int] = set()
    for index, value in enumerate(raw):
        try:
            scale = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"generator.pattern_scales[{index}] must be numeric") from error
        percent = round(scale * 100)
        if scale <= 0 or percent <= 0 or percent > 1000:
            raise ValueError(f"generator.pattern_scales[{index}] must be greater than 0 and no more than 10.0")
        if abs(scale - percent / 100.0) > 1e-9:
            raise ValueError(f"generator.pattern_scales[{index}] must resolve to a whole percentage")
        if percent in seen:
            raise ValueError(f"generator.pattern_scales contains duplicate scale {scale}")
        seen.add(percent)
        result.append((percent / 100.0, percent))
    if 100 not in seen:
        raise ValueError("generator.pattern_scales must include 1.0")
    return result


def surface_variant_stem(texture_stem: str, scale_percent: int) -> str:
    return texture_stem if scale_percent == 100 else f"{texture_stem}_s{scale_percent:03d}"


def _build_catalog(data: dict) -> tuple[list[dict], int]:
    catalog: list[dict] = []
    codes: dict[str, dict] = {}
    suggested_count = 0
    pattern_scales = load_pattern_scales(data)
    prefix = data["pack"]["prefix"]

    for paint in data["paints"]:
        code, suggested = code_for_paint(paint, prefix)
        if code in codes:
            other = codes[code]
            raise ValueError(
                "Duplicate PaintZ finish ID: "
                f"{code} is used by {other['name']!r} and {paint['name']!r}. "
                "Assign a different explicit id suffix."
            )
        codes[code] = {"name": paint["name"], "type": paint["type"]}
        suggested_count += int(suggested)
        slug = code_to_slug(code)
        is_basic = paint["type"] == "basic"
        is_pattern = bool(paint.get("pattern"))
        variants = []
        if is_basic:
            variants.append(
                {
                    "scale": 1.0,
                    "scale_percent": 100,
                    "texture_stem": slug,
                    "procedural_texture": procedural_color_texture(paint["color"]),
                }
            )
        else:
            for scale, scale_percent in (pattern_scales if is_pattern else [(1.0, 100)]):
                variants.append(
                    {
                        "scale": scale,
                        "scale_percent": scale_percent,
                        "texture_stem": surface_variant_stem(slug, scale_percent),
                    }
                )
        catalog.append(
            {
                "name": paint["name"],
                "id": code.split("-")[-1],
                "id_source": "suggested" if suggested else "explicit",
                "type": paint["type"],
                "type_code": type_code(paint["type"]),
                "code": code,
                "texture_stem": slug,
                "source": paint.get("color") or paint.get("pattern"),
                "appearance_profile": paint.get("appearance_profile"),
                "dayz_class": paint.get("dayz_class"),
                "is_basic": is_basic,
                "is_pattern": is_pattern,
                "surface_variants": variants,
            }
        )
    return catalog, suggested_count


def generate(manifest_path: Path, clean: bool = False, check: bool = False, *, official: bool = False) -> Path:
    manifest_path = manifest_path.resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    repo_root = manifest_path.parent
    data = load_manifest(manifest_path, official=official)
    appearance_cfg = load_appearance_profiles(repo_root)
    pattern_scales = load_pattern_scales(data)
    catalog, suggested_count = _build_catalog(data)

    if check:
        print(f"Pack: {data['pack']['prefix']} - {data['pack']['name']}")
        for item in catalog:
            marker = "SUGGESTED" if item["id_source"] == "suggested" else "explicit"
            print(f"{item['code']:<16} {item['type']:<12} {marker:<9} {item['name']}")
        if suggested_count:
            print(f"WARNING: {suggested_count} paint(s) use generated ID suggestions. Add explicit 'id' values before release.")
        scales_text = ", ".join(f"{scale:g}x" for scale, _ in pattern_scales)
        print(f"Pattern scales: {scales_text}")
        print(f"OK: {len(catalog)} paints; font={find_font(repo_root) or 'not found'}")
        return repo_root / "generated"

    out = repo_root / "generated"
    if clean and out.exists():
        shutil.rmtree(out)
    for directory in ("labels", "surfaces", "previews", "dayz"):
        (out / directory).mkdir(parents=True, exist_ok=True)

    base = create_base(tuple(data.get("generator", {}).get("label_size", [1024, 1024])))
    preview_items = []
    surface_size = tuple(data.get("generator", {}).get("surface_size", [1024, 1024]))

    for paint, item in zip(data["paints"], catalog):
        label = render_label(base, paint, item["code"], repo_root, appearance_cfg)
        save_png(label, out / "labels" / f"{item['texture_stem']}_co.png")

        if not item["is_basic"]:
            for variant in item["surface_variants"]:
                surface = render_surface_scaled(
                    paint,
                    item["code"],
                    repo_root,
                    surface_size,
                    appearance_cfg,
                    pattern_scale=variant["scale"],
                )
                if paint.get("color") and variant["scale_percent"] == 100:
                    avg = average_rgb(surface)
                    print(
                        f"{item['code']}: configured={str(paint['color']).upper()} "
                        f"avg_rgb=({avg[0]},{avg[1]},{avg[2]}) "
                        f"icc={'yes' if surface.info.get('icc_profile') else 'no'}"
                    )
                save_png(surface, out / "surfaces" / f"{variant['texture_stem']}_co.png")
        else:
            print(f"{item['code']}: procedural_rgb={str(paint['color']).upper()} surface_asset=none")

        preview_path = out / "previews" / f"{item['texture_stem']}_preview.png"
        save_preview(label, preview_path)
        preview_items.append((paint, item["code"], preview_path))

    save_preview_catalog(preview_items, out / "preview_catalog.png")
    (out / "catalog.json").write_text(
        json.dumps(
            {
                "generator_version": __version__,
                "paint_pack_api": 1,
                "id_scheme": "<PREFIX>-<TYPE>-<SUFFIX>",
                "pack": data["pack"],
                "appearance_profiles": appearance_cfg,
                "pattern_scales": [scale for scale, _ in pattern_scales],
                "paints": catalog,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    emit_dayz(catalog, data["pack"], data.get("dayz", {}), out / "dayz", official=official)
    if suggested_count:
        print(f"WARNING: {suggested_count} paint(s) use generated ID suggestions. Add explicit 'id' values before release.")
    print(f"Generated {len(catalog)} paints in {out}")
    print(f"Font: {find_font(repo_root) or 'not found'}")
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate PaintZ can labels, finish surfaces and Paint Pack API v1 config")
    parser.add_argument("--manifest", type=Path, default=Path("paints.json"))
    parser.add_argument("--clean", action="store_true", help="remove generated output first")
    parser.add_argument("--check", action="store_true", help="validate IDs/config without rendering")
    parser.add_argument(
        "--official",
        action="store_true",
        help="generate an independent official PZ content pack linked to the PaintZ-owned PZ namespace",
    )
    parser.add_argument("--version", action="version", version=f"PaintZ PackKit {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        generate(args.manifest, clean=args.clean, check=args.check, official=args.official)
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
