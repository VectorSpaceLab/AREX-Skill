#!/usr/bin/env python3
"""Read-only pykitti installation diagnostic.

Run from any working directory with the target environment active:
``python scripts/check_install.py``. It checks distribution metadata, imports,
optional OpenCV availability, and public constructor signatures without reading
the source checkout or downloading data.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--distribution",
        default="pykitti",
        help="Distribution name to inspect (default: pykitti).",
    )
    args = parser.parse_args()

    try:
        print(f"distribution: {args.distribution} {metadata.version(args.distribution)}")
    except metadata.PackageNotFoundError:
        print(f"ERROR: distribution {args.distribution!r} is not installed", file=sys.stderr)
        return 2

    try:
        package = importlib.import_module("pykitti")
    except Exception as exc:  # import diagnostics should identify the actual cause
        print(f"ERROR: import pykitti failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Hint: this release imports tracking.py eagerly; cv2 may be required.", file=sys.stderr)
        return 3

    print(f"module: {getattr(package, '__file__', '<unknown>')}")
    for name in ("raw", "odometry", "tracking"):
        obj = getattr(package, name, None)
        if obj is None:
            print(f"ERROR: missing public export {name}", file=sys.stderr)
            return 4
        print(f"{name}: {inspect.signature(obj)}")

    try:
        cv2 = importlib.import_module("cv2")
        print(f"opencv: {getattr(cv2, '__version__', '<unknown>')}")
    except Exception as exc:
        print(f"opencv: unavailable ({type(exc).__name__}: {exc})")
        print("note: top-level pykitti import already succeeded in this process")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
