#!/usr/bin/env python3
"""Read-only IR-SIM installation and optional-dependency diagnostic.

Run from any working directory with the interpreter that will execute the
simulation. This script does not install packages, open a GUI, or run a scene.
"""
from __future__ import annotations

import argparse
import importlib.metadata
from importlib.util import find_spec
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check IR-SIM metadata, core imports, and optional modules."
    )
    parser.add_argument(
        "--distribution",
        default="ir-sim",
        help="Distribution metadata name (default: ir-sim).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        version = importlib.metadata.version(args.distribution)
    except importlib.metadata.PackageNotFoundError:
        print(f"distribution not installed: {args.distribution}", file=sys.stderr)
        return 1

    try:
        import irsim
    except ImportError as exc:
        print(f"distribution metadata found ({version}) but import failed: {exc}", file=sys.stderr)
        return 1

    print(f"distribution={args.distribution} version={version}")
    print(f"python={sys.executable} version={sys.version.split()[0]}")
    print(f"irsim_version={getattr(irsim, '__version__', '<missing>')}")
    for module in ("pynput", "pyrvo", "imageio_ffmpeg"):
        print(f"optional_{module}={'available' if find_spec(module) else 'absent'}")
    print("core_import=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
