from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .ids import class_suffix, config_token

_OFFICIAL_PREFIX = "PZ"
_OFFICIAL_OWNER_CLASS = "PZ_PaintZOfficial"


def _config_class(item: dict, prefix: str) -> str:
    return item.get("dayz_class") or prefix + class_suffix(item["name"], item["code"])


def _cpp_string(value: str) -> str:
    return value.replace('"', '\\"')


def _scale_percent(scale: float) -> int:
    percent = round(float(scale) * 100)
    if percent <= 0 or percent > 1000:
        raise ValueError(f"Invalid PaintZ pattern scale: {scale!r}")
    if abs(float(scale) - percent / 100.0) > 1e-9:
        raise ValueError(f"PaintZ pattern scale must resolve to a whole percentage: {scale!r}")
    return percent


def _local_pack_class(pack: dict) -> str:
    identity = pack.get("author") or pack["name"]
    return f"{pack['prefix']}_{config_token(identity)}_{config_token(pack['name'])}"


def _owner_class(pack: dict, dayz: dict, local_pack_class: str, *, official: bool) -> str:
    if official:
        explicit = dayz.get("owner_class")
        if explicit and explicit != _OFFICIAL_OWNER_CLASS:
            raise ValueError(f"Official PZ content must use owner class {_OFFICIAL_OWNER_CLASS}")
        return _OFFICIAL_OWNER_CLASS

    explicit = dayz.get("owner_class")
    if explicit:
        return explicit
    return local_pack_class


def _patch_class(dayz: dict, default_root: str) -> str:
    return dayz.get("patch_class") or f"{default_root}_Patch"


def _addon_root(dayz: dict, default_root: str) -> str:
    return dayz.get("addon_root") or default_root


def _class_prefix(dayz: dict, default_root: str) -> str:
    return dayz.get("class_prefix") or f"{default_root}_SprayCan_"


def _finish_config_class(registration_root: str, item: dict) -> str:
    return f"{registration_root}_{item['type_code']}_{item['id']}"


def _surface_texture_path(surface_root: str, variant: dict) -> str:
    procedural = variant.get("procedural_texture")
    if procedural:
        return procedural
    return surface_root + "\\" + variant["texture_stem"] + "_co.paa"


def emit_dayz(
    catalog: list[dict],
    pack: dict,
    dayz: dict,
    out_dir: Path,
    *,
    official: bool = False,
):
    out_dir.mkdir(parents=True, exist_ok=True)
    if not dayz.get("emit_config_fragment", True):
        return

    requested_role = dayz.get("namespace_role", "owner")
    if requested_role not in {"owner", "satellite"}:
        raise ValueError(f"Unsupported PaintZ namespace role: {requested_role!r}")

    if official:
        if pack["prefix"] != _OFFICIAL_PREFIX:
            raise ValueError(f"Official PaintZ content currently uses only the {_OFFICIAL_PREFIX} namespace")
        if requested_role == "satellite":
            raise ValueError("Official PZ content packs are independent contributors, not satellite packs")
        if dayz.get("owner_patch"):
            raise ValueError("Official PZ content packs depend directly on PaintZ and must not set dayz.owner_patch")
        namespace_role = "official"
    else:
        namespace_role = requested_role

    local_pack_class = _local_pack_class(pack)
    owner_class = _owner_class(pack, dayz, local_pack_class, official=official)
    default_root = owner_class if namespace_role == "owner" else local_pack_class
    patch_class = _patch_class(dayz, default_root)
    addon_root = _addon_root(dayz, default_root)
    base_class = dayz.get("base_class", "PaintZ_SprayCanBase")
    class_prefix = _class_prefix(dayz, default_root)
    registration_root = owner_class if namespace_role == "owner" else local_pack_class
    can_root = addon_root + "\\data\\cans"
    surface_root = addon_root + "\\data\\surfaces"

    required_addons = ["PaintZ_DynamicPaint"]
    if namespace_role == "satellite":
        owner_patch = dayz.get("owner_patch")
        if not owner_patch:
            raise ValueError("Satellite PaintZ packs require dayz.owner_patch")
        if not dayz.get("owner_class"):
            raise ValueError("Satellite PaintZ packs require dayz.owner_class")
        if owner_patch == patch_class:
            raise ValueError("Satellite PaintZ pack patch_class must differ from dayz.owner_patch")
        required_addons.append(owner_patch)

    config_classes: set[str] = set()
    finish_classes: set[str] = set()
    for item in catalog:
        config_class = _config_class(item, class_prefix)
        finish_class = _finish_config_class(registration_root, item)
        if config_class in config_classes:
            raise ValueError(f"Duplicate generated DayZ classname: {config_class}")
        if finish_class in finish_classes:
            raise ValueError(f"Duplicate generated finish config classname: {finish_class}")
        config_classes.add(config_class)
        finish_classes.add(finish_class)

    if namespace_role == "owner":
        role_label = "standalone owner"
    elif namespace_role == "satellite":
        role_label = "satellite content"
    else:
        role_label = "independent official PZ content"

    lines = [
        "// AUTO-GENERATED by PaintZ PackKit. DO NOT EDIT.",
        f"// Paint Pack API v1 {role_label} pack config.",
        "",
        "class CfgPatches",
        "{",
        f"    class {patch_class}",
        "    {",
        "        units[] =",
        "        {",
    ]
    for index, item in enumerate(catalog):
        comma = "," if index < len(catalog) - 1 else ""
        lines.append(f'            "{_config_class(item, class_prefix)}"{comma}')
    lines += [
        "        };",
        "        weapons[] = {};",
        "        requiredVersion = 0.1;",
        "        requiredAddons[] =",
        "        {",
    ]
    for index, required_addon in enumerate(required_addons):
        comma = "," if index < len(required_addons) - 1 else ""
        lines.append(f'            "{_cpp_string(required_addon)}"{comma}')
    lines += [
        "        };",
        "    };",
        "};",
        "",
    ]

    if namespace_role == "owner":
        lines += [
            "class CfgPaintZPacks",
            "{",
            f"    class {owner_class}",
            "    {",
            "        apiVersion = 1;",
            f'        prefix = "{_cpp_string(pack["prefix"])}";',
            f'        displayName = "{_cpp_string(pack["name"])}";',
            "    };",
            "};",
            "",
        ]

    lines += [
        "class CfgPaintZFinishes",
        "{",
    ]

    for item in catalog:
        finish_class = _finish_config_class(registration_root, item)
        lines += [
            f"    class {finish_class}",
            "    {",
            f'        id = "{_cpp_string(item["code"])}";',
            f'        owner = "{_cpp_string(owner_class)}";',
            f'        displayName = "{_cpp_string(item["name"])}";',
            f'        type = "{_cpp_string(item["type"])}";',
        ]
        if item.get("is_pattern"):
            lines.append("        isPattern = 1;")
        lines += ["", "        class Surfaces", "        {"]
        for variant in item["surface_variants"]:
            percent = int(variant["scale_percent"])
            texture = _surface_texture_path(surface_root, variant)
            lines += [
                f"            class S{percent:03d}",
                "            {",
                f"                scalePercent = {percent};",
                f'                texture = "{_cpp_string(texture)}";',
                "            };",
            ]
        lines += ["        };", "    };", ""]

    lines += [
        "};",
        "",
        "class CfgVehicles",
        "{",
        f"    class {base_class};",
        "",
    ]
    for item in catalog:
        config_class = _config_class(item, class_prefix)
        can_texture = can_root + "\\" + item["texture_stem"] + "_co.paa"
        lines += [
            f"    class {config_class} : {base_class}",
            "    {",
            "        scope = 2;",
            f'        displayName = "PaintZ - {_cpp_string(item["name"])}";',
            f'        descriptionShort = "{_cpp_string(item["code"])} - PaintZ {_cpp_string(item["type"])} spray coating";',
            f'        paintzFinish = "{_cpp_string(item["code"])}";',
            f'        hiddenSelectionsTextures[] = {{"{_cpp_string(can_texture)}"}};',
            "    };",
            "",
        ]
    lines += ["};", ""]
    (out_dir / "config.cpp").write_text("\n".join(lines), encoding="utf-8")

    for legacy_name in (
        "PaintZ_Paints.generated.inc",
        "PaintZ_Units.generated.inc",
        "PaintZ_PaintCatalog.generated.c",
    ):
        legacy_path = out_dir / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()

    nominal = int(dayz.get("types_nominal", 0))
    lifetime = int(dayz.get("types_lifetime", 14400))
    xml = ["<!-- AUTO-GENERATED by PaintZ PackKit. -->", "<types>"]
    for item in catalog:
        config_class = _config_class(item, class_prefix)
        xml += [
            f'  <type name="{escape(config_class)}">',
            f"    <nominal>{nominal}</nominal>",
            f"    <lifetime>{lifetime}</lifetime>",
            "    <restock>0</restock>",
            "    <min>0</min>",
            "    <quantmin>30</quantmin>",
            "    <quantmax>100</quantmax>",
            "    <cost>100</cost>",
            '    <flags count_in_cargo="0" count_in_hoarder="0" count_in_map="1" count_in_player="0" crafted="0" deloot="0"/>',
            "  </type>",
        ]
    xml.append("</types>")
    (out_dir / "types.generated.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
