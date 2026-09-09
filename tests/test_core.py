from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from paintz_packkit.cli import generate
from paintz_packkit.ids import code_for_paint, normalize_hex, suggest_suffix
from paintz_packkit.manifest import load_manifest


def _write_manifest(root: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "generator": {"label_size": [256, 256], "surface_size": [256, 256], "pattern_scales": [1.0]},
        "dayz": {
            "emit_config_fragment": True,
            "base_class": "PaintZ_SprayCanBase",
            "class_prefix": "Test_SprayCan_",
            "texture_root": "TestPack\\data\\cans"
        },
        "paints": [
            {"id": "FDE", "name": "Flat Dark Earth", "type": "solid", "color": "#5A4F46"}
        ]
    }
    path = root / "paints.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_ids_are_compatible():
    assert normalize_hex("5a4f46") == "#5A4F46"
    assert suggest_suffix("Flat Dark Earth") == "FDE"
    assert code_for_paint({"id": "FDE", "name": "Flat Dark Earth", "type": "solid"}) == ("PZ-S-FDE", False)


def test_manifest_and_check(tmp_path: Path):
    path = _write_manifest(tmp_path)
    data = load_manifest(path)
    assert data["paints"][0]["color"] == "#5A4F46"
    assert generate(path, check=True) == tmp_path / "generated"


def test_full_solid_generation(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    (tmp_path / "assets" / "templates").mkdir(parents=True)
    (tmp_path / "assets" / "templates" / "can_design3.svg").write_text(
        (project_root / "assets" / "templates" / "can_design3.svg").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    path = _write_manifest(tmp_path)
    out = generate(path, clean=True)
    label = out / "labels" / "pz_s_fde_co.png"
    surface = out / "surfaces" / "pz_s_fde_co.png"
    assert label.exists()
    assert surface.exists()
    assert (out / "dayz" / "PaintZ_Paints.generated.inc").exists()
    assert (out / "dayz" / "PaintZ_PaintCatalog.generated.c").exists()
    assert (out / "catalog.json").exists()
    with Image.open(label) as image:
        assert image.size == (256, 256)
