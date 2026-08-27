#!/usr/bin/env python3
"""Compatibility wrapper for exporting DreamVideo-style UNet key sets.

The DreamVideo sub-skill owns the detailed adapter-key selection logic. This
root helper simply forwards to that bundled implementation so other routes can
reuse the same inspection path without depending on the original repo helper.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from typing import List


def main(argv: List[str]) -> int:
    helper = Path(__file__).resolve().parents[1] / "sub-skills" / "dreamvideo" / "scripts" / "dump_adapter_keys.py"
    if not helper.is_file():
        print(f"ERROR: bundled DreamVideo key helper not found: {helper}", file=sys.stderr)
        return 1
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(helper), *argv]
        runpy.run_path(str(helper), run_name="__main__")
    finally:
        sys.argv = old_argv
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
