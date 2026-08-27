#!/usr/bin/env python3
"""Print a non-rendering summary for a robosuite demo.hdf5 file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from inspect_demo_hdf5 import build_report, render_human_report, resolve_demo_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a robosuite demo.hdf5 file without opening a viewer.")
    parser.add_argument("demo_path", help="Path to demo.hdf5 or the directory that contains it")
    parser.add_argument("--check-lengths", action="store_true", help="Require states and actions to have matching lengths")
    args = parser.parse_args(argv)

    demo_path = resolve_demo_file(args.demo_path)
    if not demo_path.exists():
        print(f"error: demo file not found: {demo_path}", file=sys.stderr)
        return 2

    report = build_report(Path(demo_path), check_lengths=args.check_lengths)
    print(render_human_report(report, include_playback_note=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
