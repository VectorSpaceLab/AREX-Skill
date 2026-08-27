#!/usr/bin/env python3
"""Forward the repository skill's OpenMM environment probe."""
from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "sub-skills" / "system-preparation" / "scripts" / "check_openmm_env.py"
    runpy.run_path(str(target), run_name="__main__")
