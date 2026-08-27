#!/usr/bin/env python3
"""Forward to the repo-wide dataset validator from the data sub-skill."""

from __future__ import annotations

from pathlib import Path
import runpy


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    runpy.run_path(str(root / "scripts" / "validate_dataset.py"), run_name="__main__")
