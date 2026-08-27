#!/usr/bin/env python3
"""Root wrapper for the install/backend smoke checker."""
from __future__ import annotations

import runpy
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "sub-skills" / "install-and-inspect" / "scripts" / "check_open3d_ml.py"
runpy.run_path(str(SCRIPT), run_name="__main__")
