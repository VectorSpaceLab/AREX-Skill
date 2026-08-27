#!/usr/bin/env python3
"""Inspect or build EasyOCR's DBNet DCN operator inside the installed package."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect or build the EasyOCR DBNet DCN operator.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--build", action="store_true", help="Run the DCN build in the installed package.")
    mode.add_argument("--check-only", action="store_true", help="Only report the current compiled artifacts.")
    return parser.parse_args()


def locate_dcn_dir() -> Path:
    import easyocr

    package_dir = Path(easyocr.__file__).resolve().parent
    dcn_dir = package_dir / "DBNet" / "assets" / "ops" / "dcn"
    if not dcn_dir.exists():
        raise SystemExit(f"Could not find DBNet DCN directory: {dcn_dir}")
    return dcn_dir


def shared_objects(dcn_dir: Path) -> list[Path]:
    return sorted(dcn_dir.glob("deform_*_*.so"))


def print_status(dcn_dir: Path) -> int:
    so_files = shared_objects(dcn_dir)
    print(f"dcn_dir: {dcn_dir}")
    if so_files:
        print("shared_objects:")
        for path in so_files:
            print(f"  - {path.name}")
        return 0
    print("shared_objects: none found")
    return 1


def build(dcn_dir: Path) -> int:
    import torch

    if torch.cuda.is_available() and shutil.which("nvcc") is None:
        print("CUDA is available in the current torch wheel, but nvcc is missing.")
        print("Install the CUDA toolkit/NVCC or switch to a CPU-only torch wheel before building the DBNet operator.")
        return 1

    result = subprocess.run(
        [sys.executable, "setup.py", "build_ext", "--inplace"],
        cwd=dcn_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.rstrip())
        return result.returncode

    status = print_status(dcn_dir)
    if status == 0:
        print("DBNet DCN build looks complete.")
    else:
        print("DBNet DCN build finished, but the expected shared objects were not found.")
    return status


def main() -> int:
    args = parse_args()
    dcn_dir = locate_dcn_dir()

    if args.build:
        return build(dcn_dir)

    # Default to a safe inspection mode.
    return print_status(dcn_dir)


if __name__ == "__main__":
    raise SystemExit(main())
