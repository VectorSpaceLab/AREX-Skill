#!/usr/bin/env python3
"""Show the repository's main.py help output through the compatibility shim."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

from _torchvision_compat import prepare_source_runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print main.py -h after preparing the repository checkout.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to a 3D-ResNets-PyTorch checkout; defaults to the current directory.",
    )
    parser.add_argument(
        "--no-scale-shim",
        action="store_true",
        help="Disable the temporary torchvision.transforms.Scale alias.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    main_py = repo_root / "main.py"
    if not main_py.exists():
        raise SystemExit(f"main.py not found under {repo_root}")

    prepare_source_runtime(repo_root, with_scale_shim=not args.no_scale_shim)
    sys.argv = [str(main_py), "-h"]
    runpy.run_path(str(main_py), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
