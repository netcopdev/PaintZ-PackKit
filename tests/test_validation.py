from __future__ import annotations

import json
from pathlib import Path

import pytest

from paintz_packkit.manifest import load_manifest


def test_rejects_parent_pattern_path(tmp_path: Path):
    path = tmp_path / "paints.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "generator": {},
        "paints": [{"id": "ABC", "name": "Bad", "type": "camo", "pattern": "../bad.png"}]
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="safe path"):
        load_manifest(path)
