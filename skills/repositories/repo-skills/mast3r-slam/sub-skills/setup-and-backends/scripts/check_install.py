#!/usr/bin/env python3
"""Delegate to the root MASt3R-SLAM install checker.

This wrapper exists so the setup sub-skill can point to a local script path
while the implementation stays shared at the repo root.
"""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check_install.py"

if __name__ == "__main__":
    runpy.run_path(str(ROOT_SCRIPT), run_name="__main__")
