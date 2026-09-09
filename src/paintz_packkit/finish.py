from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import hashlib
import random

from PIL import Image

from .color_management import normalize_to_srgb, tag_srgb

DEFAULT_TEXTURE_SIZE = 1024
DEFAULT_APPEARANCE = {
    "default_profile": "used",
    "profiles": {
        "used": {
            "noise": 0.07,
            "scratches": 0.12,
            "grime": 0.08,
            "rust": 0.0,
            "edgewear": 0.08,
        }
    },
}


@lru_cache(maxsize=32)
def _load_overlay(path: str) -> Image.Image:
    with Image.open(path) as image:
        return normalize_to_srgb(image, "RGBA")


def _seed_for_label(code: str) -> int:
    digest = hashlib.sha256(f"paintz-finish-v1|{code}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _luminance(rgb: tuple[int, int, int]) -> float:
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255.0


def _resolve_profile(paint: dict, appearance_cfg: dict) -> tuple[str, dict]:
    profiles = appearance_cfg.get("profiles", {})
    default_name = appearance_cfg.get("default_profile", "used")
    name = paint.get("appearance_profile") or default_name
    if name not in profiles:
        raise ValueError(f"Unknown appearance profile {name!r} for paint {paint.get('name')!r}")
    return name, profiles[name]


def _subtle_grain(image: Image.Image, seed: int, strength: float):
    rng = random.Random(seed)
    pixels = image.load()
    hits = max(1, int(image.width * image.height * (0.010 + 0.014 * strength)))
    spread = max(1, int(18 * max(0.25, strength)))
    for _ in range(hits):
        x = rng.randrange(image.width)
        y = rng.randrange(image.height)
        r, g, b = pixels[x, y][:3]
        delta = rng.randint(-spread, spread)
        pixels[x, y] = (
            max(0, min(255, r + delta)),
            max(0, min(255, g + delta)),
            max(0, min(255, b + delta)),
            255,
        )


def _alpha_scaled(image: Image.Image, factor: float) -> Image.Image:
    if factor <= 0:
        return tag_srgb(Image.new("RGBA", image.size, (0, 0, 0, 0)))
    output = image.copy()
    r, g, b, a = output.split()
    a = a.point(lambda value: max(0, min(255, int(value * factor))))
    output.putalpha(a)
    return tag_srgb(output)


def _composite_optional_overlay(
    surface: Image.Image,
    path: Path,
    factor: float,
):
    """Preserve legacy overlay support without requiring an external asset bundle."""
    if factor <= 0 or not path.exists():
        return
    overlay = _load_overlay(str(path)).resize(surface.size, Image.Resampling.LANCZOS)
    surface.alpha_composite(_alpha_scaled(overlay, factor))


def pattern_fill(path: Path, size: tuple[int, int]) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Pattern source not found: {path}")
    with Image.open(path) as source:
        source = normalize_to_srgb(source, "RGBA")
        target_width, target_height = size
        ratio = max(target_width / source.width, target_height / source.height)
        new_width = max(1, int(source.width * ratio))
        new_height = max(1, int(source.height * ratio))
        source = source.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        return tag_srgb(
            source.crop((left, top, left + target_width, top + target_height)).convert("RGBA")
        )


def _apply_finish_stack(surface: Image.Image, code: str, repo_root: Path, profile: dict):
    seed = _seed_for_label(code)
    rng = random.Random(seed)
    average = surface.resize((1, 1), Image.Resampling.BOX).convert("RGB").getpixel((0, 0))
    lum = _luminance(average)

    _subtle_grain(surface, seed ^ 0xA91F, float(profile.get("noise", 0.07)))

    overlay_dir = repo_root / "assets" / "overlays"
    grime_factor = float(profile.get("grime", 0.08)) * (1.10 if lum > 0.72 else 1.0)
    _composite_optional_overlay(
        surface,
        overlay_dir / f"grime_{rng.choice([1, 2]):02d}.png",
        grime_factor * (0.80 + 0.40 * rng.random()),
    )

    scratch_factor = float(profile.get("scratches", 0.12)) * (1.18 if lum < 0.35 else 1.0)
    _composite_optional_overlay(
        surface,
        overlay_dir / f"scratches_{rng.choice([1, 2, 3]):02d}.png",
        scratch_factor * (0.80 + 0.35 * rng.random()),
    )

    rust_amount = float(profile.get("rust", 0.0))
    if rust_amount > 0:
        _composite_optional_overlay(
            surface,
            overlay_dir / f"rust_{rng.choice([1, 2]):02d}.png",
            rust_amount * (0.85 + 0.30 * rng.random()),
        )

    edge_factor = float(profile.get("edgewear", 0.08)) * (1.10 if lum < 0.45 else 0.95)
    _composite_optional_overlay(surface, overlay_dir / "edgewear_01.png", edge_factor)


def create_base(size: tuple[int, int] | None = None) -> Image.Image:
    if size is None:
        size = (DEFAULT_TEXTURE_SIZE, DEFAULT_TEXTURE_SIZE)
    return tag_srgb(Image.new("RGBA", size, (0, 0, 0, 0)))


def render_surface(
    paint: dict,
    code: str,
    repo_root: Path,
    size: tuple[int, int],
    appearance_cfg: dict | None = None,
) -> Image.Image:
    appearance_cfg = appearance_cfg or DEFAULT_APPEARANCE
    if paint.get("color"):
        value = paint["color"].lstrip("#")
        rgb = tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
        surface = tag_srgb(Image.new("RGBA", size, rgb + (255,)))
    else:
        pattern_path = (repo_root / paint["pattern"]).resolve()
        surface = pattern_fill(pattern_path, size)

    if paint.get("type") == "basic":
        surface.info["appearance_profile"] = "none"
        return tag_srgb(surface)

    profile_name, profile = _resolve_profile(paint, appearance_cfg)
    _apply_finish_stack(surface, code, repo_root, profile)
    tag_srgb(surface)
    surface.info["appearance_profile"] = profile_name
    return surface
