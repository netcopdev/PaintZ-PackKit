#!/usr/bin/env python3
"""Compatibility entry point for the original PaintZ generator workflow."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from paintz_packkit.cli import main

raise SystemExit(main())
