#!/usr/bin/env python3
"""Run the generated Fairlearn root install check from the installation sub-skill."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    script = root / "scripts" / "check_install.py"
    if not script.exists():
        print(f"Missing root install check script: {script}", file=sys.stderr)
        return 2
    sys.argv = [str(script), *sys.argv[1:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
