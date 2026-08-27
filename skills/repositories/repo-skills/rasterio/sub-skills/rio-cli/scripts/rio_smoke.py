#!/usr/bin/env python3
"""Safe Rasterio `rio` CLI smoke helper.

The helper runs version/help checks and, when --path is supplied, runs a local
`rio info` command plus optional `rio bounds` output. It requires an existing
local file, stops option parsing before the raster path, and never writes
output files.

Examples
--------
python scripts/rio_smoke.py
python scripts/rio_smoke.py --path input.tif --bounds
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path", type=Path, help="Optional local raster path for `rio info`."
    )
    parser.add_argument(
        "--bounds",
        action="store_true",
        help="Also run `rio bounds --bbox --precision 2` for --path.",
    )
    return parser.parse_args()


def require_local_file(path: Path) -> Path | None:
    if not path.exists():
        print(f"--path must point to an existing local file: {path}", file=sys.stderr)
        return None
    if not path.is_file():
        print(f"--path must point to a local file, not a directory: {path}", file=sys.stderr)
        return None
    return path


def run(args: list[str]) -> str:
    try:
        completed = subprocess.run(args, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout.rstrip())
        if exc.stderr:
            print(exc.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(exc.returncode)
    return completed.stdout.strip()


def main() -> int:
    args = parse_args()
    if shutil.which("rio") is None:
        print("rio command not found on PATH", file=sys.stderr)
        return 2

    print(f"version={run(['rio', '--version'])}")
    help_text = run(["rio", "--help"])
    print(f"help-first-line={help_text.splitlines()[0] if help_text else ''}")

    if args.bounds and not args.path:
        print("--bounds requires --path", file=sys.stderr)
        return 2

    if args.path:
        path = require_local_file(args.path)
        if path is None:
            return 2

        info = run(["rio", "info", "--", str(path)])
        parsed = json.loads(info)
        print(
            f"info-driver={parsed.get('driver')} shape={parsed.get('shape')} count={parsed.get('count')} crs={parsed.get('crs')}"
        )
        if args.bounds:
            print(
                f"bounds={run(['rio', 'bounds', '--bbox', '--precision', '2', '--', str(path)])}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
