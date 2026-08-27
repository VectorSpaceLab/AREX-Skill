#!/usr/bin/env python3
"""Run the repository's main.py entry point with a repo-root wrapper.

This wrapper keeps the generated skill self-contained: it adds the checkout to
``sys.path`` and applies the temporary legacy torchvision Scale alias before
handing off to ``main.py``.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

from _torchvision_compat import prepare_source_runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Forward to the repository main.py after preparing the checkout and a "
            "temporary torchvision Scale compatibility alias."
        )
    )
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
    args, passthrough = parser.parse_known_args(argv)
    repo_root = args.repo_root.resolve()
    main_py = repo_root / "main.py"
    if not main_py.exists():
        raise SystemExit(f"main.py not found under {repo_root}")

    prepare_source_runtime(repo_root, with_scale_shim=not args.no_scale_shim)

    if passthrough[:1] == ["--"]:
        passthrough = passthrough[1:]
    sys.argv = [str(main_py), *passthrough]
    runpy.run_path(str(main_py), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
