from __future__ import annotations

import json
from pathlib import Path

import pytest

from paintz_packkit.cli import generate
from paintz_packkit.manifest import load_manifest


def _manifest(prefix: str = "NCP") -> dict:
    return {
        "schema_version": 1,
        "pack": {"prefix": prefix, "name": "Validation Pack", "author": "tester"},
        "generator": {"pattern_scales": [1.0]},
        "paints": [{"id": "ABC", "name": "Test", "type": "solid", "color": "#112233"}],
    }


def test_rejects_parent_pattern_path(tmp_path: Path):
    data = _manifest()
    data["paints"] = [{"id": "ABC", "name": "Bad", "type": "camo", "pattern": "../bad.png"}]
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="safe path"):
        load_manifest(path)


def test_rejects_missing_pattern_file(tmp_path: Path):
    data = _manifest()
    data["paints"] = [{"id": "ABC", "name": "Missing", "type": "camo", "pattern": "assets/missing.png"}]
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="does not exist"):
        load_manifest(path)


def test_basic_requires_color(tmp_path: Path):
    data = _manifest()
    data["paints"] = [{"id": "ABC", "name": "Basic", "type": "basic", "pattern": "assets/basic.png"}]
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "basic.png").write_bytes(b"not-an-image")
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="basic finishes require"):
        load_manifest(path)


def test_basic_rejects_appearance_profile(tmp_path: Path):
    data = _manifest()
    data["paints"] = [
        {
            "id": "ABC",
            "name": "Basic",
            "type": "basic",
            "color": "#112233",
            "appearance_profile": "clean",
        }
    ]
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="plain RGB only"):
        load_manifest(path)


@pytest.mark.parametrize("prefix", ["PZ", "PZA", "PZ9"])
def test_rejects_reserved_pz_prefix_by_default(tmp_path: Path, prefix: str):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest(prefix)), encoding="utf-8")
    with pytest.raises(ValueError, match="reserved"):
        load_manifest(path)


def test_official_mode_allows_core_owned_pz_prefix(tmp_path: Path):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest("PZ")), encoding="utf-8")
    data = load_manifest(path, official=True)
    assert data["pack"]["prefix"] == "PZ"
    assert generate(path, check=True, official=True) == tmp_path / "generated"


@pytest.mark.parametrize("prefix", ["PZA", "PZ9"])
def test_official_mode_rejects_unassigned_reserved_namespace(tmp_path: Path, prefix: str):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest(prefix)), encoding="utf-8")
    with pytest.raises(ValueError, match="only the PaintZ-owned PZ namespace"):
        load_manifest(path, official=True)


def test_official_mode_rejects_non_reserved_prefix(tmp_path: Path):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest("NCP")), encoding="utf-8")
    with pytest.raises(ValueError, match="--official"):
        load_manifest(path, official=True)


def test_official_mode_rejects_satellite_role(tmp_path: Path):
    data = _manifest("PZ")
    data["dayz"] = {
        "namespace_role": "satellite",
        "owner_class": "PZ_PaintZOfficial",
        "owner_patch": "PaintZ_DynamicPaint",
    }
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="independent contributors"):
        load_manifest(path, official=True)


def test_official_mode_rejects_content_pack_owner_dependency(tmp_path: Path):
    data = _manifest("PZ")
    data["dayz"] = {"owner_patch": "PaintZ_Standard_Pack"}
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="depend directly on PaintZ"):
        load_manifest(path, official=True)


def test_official_mode_rejects_wrong_owner_class(tmp_path: Path):
    data = _manifest("PZ")
    data["dayz"] = {"owner_class": "PZ_PaintZStandardPack"}
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="PZ_PaintZOfficial"):
        load_manifest(path, official=True)


def test_rejects_invalid_prefix(tmp_path: Path):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest("TOOLONG")), encoding="utf-8")
    with pytest.raises(ValueError, match="pack prefix"):
        load_manifest(path)


def test_satellite_requires_owner_class(tmp_path: Path):
    data = _manifest()
    data["dayz"] = {"namespace_role": "satellite", "owner_patch": "NCP_Owner_Patch"}
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="owner_class is required"):
        load_manifest(path)


def test_satellite_requires_owner_patch(tmp_path: Path):
    data = _manifest()
    data["dayz"] = {"namespace_role": "satellite", "owner_class": "NCP_Owner"}
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="owner_patch is required"):
        load_manifest(path)


def test_owner_pack_rejects_owner_patch(tmp_path: Path):
    data = _manifest()
    data["dayz"] = {"owner_patch": "NCP_Owner_Patch"}
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="only valid"):
        load_manifest(path)


def test_rejects_unknown_namespace_role(tmp_path: Path):
    data = _manifest()
    data["dayz"] = {"namespace_role": "child"}
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="namespace_role"):
        load_manifest(path)


def test_duplicate_complete_finish_id_is_rejected(tmp_path: Path):
    data = _manifest()
    data["paints"] = [
        {"id": "ABC", "name": "First", "type": "solid", "color": "#112233"},
        {"id": "ABC", "name": "Second", "type": "solid", "color": "#445566"},
    ]
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate PaintZ finish ID"):
        generate(path, check=True)
