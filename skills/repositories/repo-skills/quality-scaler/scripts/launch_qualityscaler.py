#!/usr/bin/env python3
"""Preflight and optionally launch QualityScaler.

Purpose:
- Check the expected QualityScaler layout from any working directory.
- Fail with a readable message when the runtime is missing packages, assets,
  or the Windows-specific launch surface.
- Launch the app only when --launch is supplied.

Example:
  python launch_qualityscaler.py --repo-root /path/to/QualityScaler --launch
"""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from inspect_qualityscaler_layout import inspect_layout  # type: ignore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight or launch the QualityScaler GUI app.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the QualityScaler repository root (default: current directory).",
    )
    parser.add_argument(
        "--launch",
        action="store_true",
        help="Run the app after the preflight checks pass.",
    )
    parser.add_argument(
        "--skip-layout-check",
        action="store_true",
        help="Skip the asset/model layout preflight.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()

    if not args.skip_layout_check:
        result = inspect_layout(repo_root)
        if not result["ok"]:
            print("QualityScaler layout check failed.")
            print(f"Missing files: {result['required_files_missing']}")
            print(f"Missing directories: {result['required_dirs_missing']}")
            print(f"Missing runtime assets: {result['runtime_assets_missing']}")
            print(f"Missing model files: {result['model_files_missing']}")
            return 2
        print("QualityScaler layout check passed.")

    if not args.launch:
        print("Preflight only. Re-run with --launch to start the GUI.")
        return 0

    if sys.platform != "win32":
        print("QualityScaler launch requires Windows; the GUI source is Windows-specific.")
        return 2

    entry = repo_root / "QualityScaler.py"
    if not entry.exists():
        print(f"Missing app entry file: {entry}")
        return 2

    os.chdir(repo_root)
    try:
        runpy.run_path(str(entry), run_name="__main__")
    except ImportError as exc:
        print(f"QualityScaler launch failed because a runtime dependency or backend is missing: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - launch-time diagnostics
        print(f"QualityScaler launch failed: {exc}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
