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


@pytest.mark.parametrize("prefix", ["PZ", "PZA", "PZ9"])
def test_rejects_reserved_pz_prefix_by_default(tmp_path: Path, prefix: str):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest(prefix)), encoding="utf-8")
    with pytest.raises(ValueError, match="reserved"):
        load_manifest(path)


def test_official_mode_allows_pz_prefix(tmp_path: Path):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest("PZ")), encoding="utf-8")
    data = load_manifest(path, official=True)
    assert data["pack"]["prefix"] == "PZ"
    assert generate(path, check=True, official=True) == tmp_path / "generated"


def test_official_mode_rejects_non_reserved_prefix(tmp_path: Path):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest("NCP")), encoding="utf-8")
    with pytest.raises(ValueError, match="--official"):
        load_manifest(path, official=True)


def test_rejects_invalid_prefix(tmp_path: Path):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps(_manifest("TOOLONG")), encoding="utf-8")
    with pytest.raises(ValueError, match="pack prefix"):
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
