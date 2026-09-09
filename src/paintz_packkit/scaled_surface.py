from __future__ import annotations

from pathlib import Path
from PIL import Image

from .color_management import tag_srgb
from .finish import (
    DEFAULT_APPEARANCE,
    _apply_finish_stack,
    _resolve_profile,
    pattern_fill,
    render_surface,
)


def scale_pattern_fill(path: Path, size: tuple[int, int], pattern_scale: float) -> Image.Image:
    if pattern_scale <= 0:
        raise ValueError("pattern_scale must be greater than zero")
    base = pattern_fill(path, size)
    if abs(pattern_scale - 1.0) < 1e-9:
        return base

    target_width, target_height = size
    scaled_width = max(1, round(target_width * pattern_scale))
    scaled_height = max(1, round(target_height * pattern_scale))
    scaled = base.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    if pattern_scale > 1.0:
        left = (scaled_width - target_width) // 2
        top = (scaled_height - target_height) // 2
        return tag_srgb(
            scaled.crop((left, top, left + target_width, top + target_height)).convert("RGBA")
        )

    output = tag_srgb(Image.new("RGBA", size))
    for y in range(0, target_height, scaled_height):
        for x in range(0, target_width, scaled_width):
            output.alpha_composite(scaled, (x, y))
    return output


def render_surface_scaled(
    paint: dict,
    code: str,
    repo_root: Path,
    size: tuple[int, int],
    appearance_cfg: dict | None = None,
    pattern_scale: float = 1.0,
) -> Image.Image:
    if not paint.get("pattern") or abs(pattern_scale - 1.0) < 1e-9:
        return render_surface(paint, code, repo_root, size, appearance_cfg)

    appearance_cfg = appearance_cfg or DEFAULT_APPEARANCE
    pattern_path = (repo_root / paint["pattern"]).resolve()
    surface = scale_pattern_fill(pattern_path, size, pattern_scale)
    profile_name, profile = _resolve_profile(paint, appearance_cfg)
    _apply_finish_stack(surface, code, repo_root, profile)
    tag_srgb(surface)
    surface.info["appearance_profile"] = profile_name
    return surface
