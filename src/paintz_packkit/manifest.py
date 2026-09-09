from __future__ import annotations

import json
from pathlib import Path

from .ids import TYPE_CODES, normalize_hex, normalize_suffix


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported schema_version; expected 1")
    paints = data.get("paints")
    if not isinstance(paints, list) or not paints:
        raise ValueError("Manifest must contain a non-empty paints array")

    for i, paint in enumerate(paints):
        if not isinstance(paint, dict):
            raise ValueError(f"paints[{i}] must be an object")
        name = str(paint.get("name", "")).strip()
        if not name:
            raise ValueError(f"paints[{i}].name is required")
        paint["name"] = name

        typ = str(paint.get("type", "")).casefold()
        if typ not in TYPE_CODES:
            allowed = ", ".join(sorted(TYPE_CODES))
            raise ValueError(f"Paint {name!r}: type must be one of: {allowed}")
        paint["type"] = typ

        if "id" in paint:
            paint["id"] = normalize_suffix(str(paint["id"]))

        has_color = bool(paint.get("color"))
        has_pattern = bool(paint.get("pattern"))
        if has_color and has_pattern:
            raise ValueError(f"Paint {name!r}: specify either 'color' or 'pattern', not both")
        if not has_color and not has_pattern:
            raise ValueError(f"Paint {name!r}: needs either 'color' or 'pattern' artwork data")
        if has_color:
            paint["color"] = normalize_hex(str(paint["color"]))
        if has_pattern:
            pattern = Path(str(paint["pattern"]))
            if pattern.is_absolute() or ".." in pattern.parts:
                raise ValueError(f"Paint {name!r}: pattern must be a safe path relative to the manifest")

        if "appearance_profile" in paint:
            paint["appearance_profile"] = str(paint["appearance_profile"]).strip()
            if not paint["appearance_profile"]:
                raise ValueError(f"Paint {name!r}: appearance_profile cannot be empty")

        if "dayz_class" in paint:
            dayz_class = str(paint["dayz_class"]).strip()
            if (
                not dayz_class
                or not (dayz_class[0].isalpha() or dayz_class[0] == "_")
                or not all(c.isalnum() or c == "_" for c in dayz_class)
            ):
                raise ValueError(f"Paint {name!r}: dayz_class must be a valid config classname")
            paint["dayz_class"] = dayz_class

    return data
