#!/usr/bin/env python3
"""Run the translation-workflows runtime smoke checker from the repo skill tree.

This wrapper exists so future agents can use a single root-level helper without
needing to know which sub-skill owns the deeper inspection script.

Example:
    python scripts/check_runtime.py --repo-root /path/to/checkout --check-cuda
"""
from __future__ import annotations

from pathlib import Path
import runpy
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "sub-skills" / "translation-workflows" / "scripts" / "check_runtime.py"
    if not target.is_file():
        raise SystemExit(f"missing runtime checker: {target}")
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
