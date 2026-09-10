from __future__ import annotations

import json
import re
from pathlib import Path

from .ids import TYPE_CODES, normalize_hex, normalize_prefix, normalize_suffix

_CONFIG_CLASS_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NAMESPACE_ROLES = {"owner", "satellite"}
_OFFICIAL_PREFIX = "PZ"
_OFFICIAL_OWNER_CLASS = "PZ_PaintZOfficial"


def _require_config_class(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not _CONFIG_CLASS_RE.fullmatch(text):
        raise ValueError(f"{label} must be a valid DayZ config classname")
    return text


def load_manifest(path: Path, *, official: bool = False) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported schema_version; expected 1")

    pack = data.get("pack")
    if not isinstance(pack, dict):
        raise ValueError("Manifest must contain a pack object")

    pack_name = str(pack.get("name", "")).strip()
    if not pack_name:
        raise ValueError("pack.name is required")
    pack["name"] = pack_name
    pack["prefix"] = normalize_prefix(str(pack.get("prefix", "")), allow_reserved_pz=official)
    if official and pack["prefix"] != _OFFICIAL_PREFIX:
        raise ValueError("--official currently supports only the PaintZ-owned PZ namespace")

    if "author" in pack:
        author = str(pack["author"]).strip()
        if not author:
            raise ValueError("pack.author cannot be empty")
        pack["author"] = author

    generator = data.get("generator", {})
    if not isinstance(generator, dict):
        raise ValueError("generator must be an object")
    data["generator"] = generator

    dayz = data.get("dayz", {})
    if not isinstance(dayz, dict):
        raise ValueError("dayz must be an object when present")
    data["dayz"] = dayz

    namespace_role = str(dayz.get("namespace_role", "owner")).strip().casefold()
    if namespace_role not in _NAMESPACE_ROLES:
        allowed = ", ".join(sorted(_NAMESPACE_ROLES))
        raise ValueError(f"dayz.namespace_role must be one of: {allowed}")
    dayz["namespace_role"] = namespace_role

    if "addon_root" in dayz:
        dayz["addon_root"] = _require_config_class(dayz["addon_root"], "dayz.addon_root")
    if "patch_class" in dayz:
        dayz["patch_class"] = _require_config_class(dayz["patch_class"], "dayz.patch_class")
    if "owner_class" in dayz:
        dayz["owner_class"] = _require_config_class(dayz["owner_class"], "dayz.owner_class")
    if "owner_patch" in dayz:
        dayz["owner_patch"] = _require_config_class(dayz["owner_patch"], "dayz.owner_patch")
    if "class_prefix" in dayz:
        dayz["class_prefix"] = _require_config_class(dayz["class_prefix"], "dayz.class_prefix")
    if "base_class" in dayz:
        dayz["base_class"] = _require_config_class(dayz["base_class"], "dayz.base_class")

    if official:
        if namespace_role == "satellite":
            raise ValueError("Official PZ content packs are independent contributors; do not use dayz.namespace_role='satellite'")
        if "owner_patch" in dayz:
            raise ValueError("Official PZ content packs depend directly on PaintZ and must not set dayz.owner_patch")
        if "owner_class" in dayz and dayz["owner_class"] != _OFFICIAL_OWNER_CLASS:
            raise ValueError(f"Official PZ content must use the PaintZ-owned namespace owner {_OFFICIAL_OWNER_CLASS!r}")
    elif namespace_role == "satellite":
        if "owner_class" not in dayz:
            raise ValueError("dayz.owner_class is required when dayz.namespace_role is 'satellite'")
        if "owner_patch" not in dayz:
            raise ValueError("dayz.owner_patch is required when dayz.namespace_role is 'satellite'")
    elif "owner_patch" in dayz:
        raise ValueError("dayz.owner_patch is only valid when dayz.namespace_role is 'satellite'")

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

        if official and typ == "basic" and name.casefold().startswith("basic "):
            raise ValueError(
                f"Paint {name!r}: official Basic finish display names must contain only the color name; "
                "do not prefix them with 'Basic '"
            )

        if "id" in paint:
            paint["id"] = normalize_suffix(str(paint["id"]))

        has_color = bool(paint.get("color"))
        has_pattern = bool(paint.get("pattern"))
        if has_color and has_pattern:
            raise ValueError(f"Paint {name!r}: specify either 'color' or 'pattern', not both")
        if not has_color and not has_pattern:
            raise ValueError(f"Paint {name!r}: needs either 'color' or 'pattern' artwork data")

        if typ == "basic" and not has_color:
            raise ValueError(f"Paint {name!r}: basic finishes require a 'color' and cannot use pattern artwork")
        if typ == "solid" and not has_color:
            raise ValueError(f"Paint {name!r}: solid finishes require a single base 'color'")
        if typ in {"camo", "pattern"} and not has_pattern:
            raise ValueError(f"Paint {name!r}: {typ} finishes require 'pattern' artwork")

        if has_color:
            paint["color"] = normalize_hex(str(paint["color"]))
        if has_pattern:
            pattern = Path(str(paint["pattern"]))
            if pattern.is_absolute() or ".." in pattern.parts:
                raise ValueError(f"Paint {name!r}: pattern must be a safe path relative to the manifest")
            if not (path.parent / pattern).is_file():
                raise ValueError(f"Paint {name!r}: pattern file does not exist: {pattern}")
            paint["pattern"] = pattern.as_posix()

        if "appearance_profile" in paint:
            paint["appearance_profile"] = str(paint["appearance_profile"]).strip()
            if not paint["appearance_profile"]:
                raise ValueError(f"Paint {name!r}: appearance_profile cannot be empty")
            if typ == "basic":
                raise ValueError(f"Paint {name!r}: basic finishes are plain RGB only and cannot use appearance_profile")

        if "dayz_class" in paint:
            paint["dayz_class"] = _require_config_class(paint["dayz_class"], f"Paint {name!r}: dayz_class")

    return data
