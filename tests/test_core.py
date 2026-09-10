from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from paintz_packkit.cli import generate
from paintz_packkit.ids import code_for_paint, normalize_hex, normalize_prefix, suggest_suffix
from paintz_packkit.manifest import load_manifest


def _copy_template(root: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    (root / "assets" / "templates").mkdir(parents=True, exist_ok=True)
    (root / "assets" / "templates" / "can_design3.svg").write_text(
        (project_root / "assets" / "templates" / "can_design3.svg").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _write_manifest(
    root: Path,
    paints: list[dict] | None = None,
    prefix: str = "NCP",
    dayz_overrides: dict | None = None,
) -> Path:
    dayz = {
        "emit_config_fragment": True,
        "addon_root": "NCP_TestPaints",
        "class_prefix": "NCP_Test_SprayCan_",
    }
    if dayz_overrides:
        dayz.update(dayz_overrides)
    manifest = {
        "schema_version": 1,
        "pack": {"prefix": prefix, "name": "Netcop Test Paints", "author": "netcopdev"},
        "generator": {"label_size": [256, 256], "surface_size": [256, 256], "pattern_scales": [1.0]},
        "dayz": dayz,
        "paints": paints
        or [{"id": "FDE", "name": "Flat Dark Earth", "type": "solid", "color": "#5A4F46"}],
    }
    path = root / "paints.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_ids_are_api_v1_namespaced():
    assert normalize_hex("5a4f46") == "#5A4F46"
    assert normalize_prefix("ncp") == "NCP"
    assert suggest_suffix("Flat Dark Earth") == "FDE"
    assert code_for_paint({"id": "FDE", "name": "Flat Dark Earth", "type": "solid"}, "NCP") == (
        "NCP-S-FDE",
        False,
    )
    assert code_for_paint({"id": "BLK", "name": "Basic Black", "type": "basic"}, "NCP") == (
        "NCP-B-BLK",
        False,
    )


def test_manifest_and_check(tmp_path: Path):
    path = _write_manifest(tmp_path)
    data = load_manifest(path)
    assert data["pack"]["prefix"] == "NCP"
    assert data["dayz"]["namespace_role"] == "owner"
    assert data["paints"][0]["color"] == "#5A4F46"
    assert generate(path, check=True) == tmp_path / "generated"


def test_full_solid_generation_emits_api_v1_config(tmp_path: Path):
    _copy_template(tmp_path)
    path = _write_manifest(tmp_path)
    out = generate(path, clean=True)

    label = out / "labels" / "ncp_s_fde_co.png"
    surface = out / "surfaces" / "ncp_s_fde_co.png"
    config = out / "dayz" / "config.cpp"
    assert label.exists()
    assert surface.exists()
    assert config.exists()
    assert not (out / "dayz" / "PaintZ_PaintCatalog.generated.c").exists()
    assert (out / "catalog.json").exists()

    text = config.read_text(encoding="utf-8")
    assert '"PaintZ_DynamicPaint"' in text
    assert "class CfgPaintZPacks" in text
    assert 'prefix = "NCP";' in text
    assert "class CfgPaintZFinishes" in text
    assert 'id = "NCP-S-FDE";' in text
    assert 'paintzFinish = "NCP-S-FDE";' in text
    assert "class S100" in text
    assert 'texture = "NCP_TestPaints\\data\\surfaces\\ncp_s_fde_co.paa";' in text
    assert "ActionPaintZPaint_" not in text

    with Image.open(label) as image:
        assert image.size == (256, 256)


def test_basic_generation_uses_procedural_texture_and_no_surface_asset(tmp_path: Path):
    _copy_template(tmp_path)
    path = _write_manifest(
        tmp_path,
        paints=[{"id": "BLK", "name": "Basic Black", "type": "basic", "color": "#262827"}],
    )
    out = generate(path, clean=True)

    label = out / "labels" / "ncp_b_blk_co.png"
    surface = out / "surfaces" / "ncp_b_blk_co.png"
    config = (out / "dayz" / "config.cpp").read_text(encoding="utf-8")

    assert label.exists()
    assert not surface.exists()
    assert 'id = "NCP-B-BLK";' in config
    assert 'type = "basic";' in config
    assert '#(argb,8,8,3)color(0.149020,0.156863,0.152941,1.0,CO)' in config
    assert "NCP_TestPaints\\data\\surfaces\\ncp_b_blk_co.paa" not in config


def test_satellite_generation_reuses_owner_without_redeclaring_namespace(tmp_path: Path):
    _copy_template(tmp_path)
    path = _write_manifest(
        tmp_path,
        dayz_overrides={
            "namespace_role": "satellite",
            "owner_class": "NCP_NetcopOwnerPack",
            "owner_patch": "NCP_Owner_Patch",
            "patch_class": "NCP_Camo_Satellite",
            "addon_root": "NCP_Camo_Satellite",
            "class_prefix": "NCP_Camo_SprayCan_",
        },
    )
    out = generate(path, clean=True)
    text = (out / "dayz" / "config.cpp").read_text(encoding="utf-8")

    assert "class CfgPaintZPacks" not in text
    assert '"PaintZ_DynamicPaint",' in text
    assert '"NCP_Owner_Patch"' in text
    assert 'owner = "NCP_NetcopOwnerPack";' in text
    assert 'id = "NCP-S-FDE";' in text
    assert 'paintzFinish = "NCP-S-FDE";' in text
    assert "class NCP_NETCOPDEV_NETCOP_TEST_PAINTS_S_FDE" in text
    assert 'texture = "NCP_Camo_Satellite\\data\\surfaces\\ncp_s_fde_co.paa";' in text


def test_official_pack_uses_core_owner_without_content_pack_dependency(tmp_path: Path):
    _copy_template(tmp_path)
    path = _write_manifest(
        tmp_path,
        prefix="PZ",
        dayz_overrides={
            "patch_class": "PaintZ_Official_Military_Pack",
            "addon_root": "PaintZ_Official_Military_Pack",
            "class_prefix": "PaintZ_Military_SprayCan_",
        },
    )
    out = generate(path, clean=True, official=True)
    text = (out / "dayz" / "config.cpp").read_text(encoding="utf-8")

    assert "class CfgPaintZPacks" not in text
    assert "official = 1;" not in text
    assert 'owner = "PZ_PaintZOfficial";' in text
    assert 'id = "PZ-S-FDE";' in text
    assert text.count('"PaintZ_DynamicPaint"') == 1
    assert "PaintZ_Standard_Pack" not in text
    assert "class PZ_NETCOPDEV_NETCOP_TEST_PAINTS_S_FDE" in text
    assert 'texture = "PaintZ_Official_Military_Pack\\data\\surfaces\\pz_s_fde_co.paa";' in text


def test_official_pack_may_repeat_canonical_owner_class_explicitly(tmp_path: Path):
    _copy_template(tmp_path)
    path = _write_manifest(
        tmp_path,
        prefix="PZ",
        dayz_overrides={
            "owner_class": "PZ_PaintZOfficial",
            "patch_class": "PaintZ_Official_Pastel_Pack",
            "addon_root": "PaintZ_Official_Pastel_Pack",
        },
    )
    out = generate(path, clean=True, official=True)
    text = (out / "dayz" / "config.cpp").read_text(encoding="utf-8")

    assert "class CfgPaintZPacks" not in text
    assert 'owner = "PZ_PaintZOfficial";' in text
    assert '"PaintZ_DynamicPaint"' in text


def test_pattern_generation_declares_only_generated_scales(tmp_path: Path):
    _copy_template(tmp_path)
    pattern_dir = tmp_path / "assets" / "pattern_sources"
    pattern_dir.mkdir(parents=True)
    Image.new("RGB", (64, 64), (10, 20, 30)).save(pattern_dir / "test.png")

    path = _write_manifest(
        tmp_path,
        paints=[{"id": "PAT", "name": "Test Pattern", "type": "camo", "pattern": "assets/pattern_sources/test.png"}],
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    data["generator"]["pattern_scales"] = [0.5, 1.0, 1.5]
    path.write_text(json.dumps(data), encoding="utf-8")

    out = generate(path, clean=True)
    config = (out / "dayz" / "config.cpp").read_text(encoding="utf-8")
    assert "isPattern = 1;" in config
    assert "class S050" in config
    assert "class S100" in config
    assert "class S150" in config
    assert "class S075" not in config
    assert "ncp_c_pat_s050_co.paa" in config
    assert "ncp_c_pat_co.paa" in config
    assert "ncp_c_pat_s150_co.paa" in config
