#!/usr/bin/env python3
"""Run a read-only WorldGen import, API, and CUDA smoke check."""

from __future__ import annotations

import argparse
import inspect
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check WorldGen importability, public signatures, and CUDA readiness."
    )
    parser.add_argument(
        "--demo-help",
        action="store_true",
        help="Also run the bundled worldgen_demo.py --help check.",
    )
    args = parser.parse_args()

    try:
        package_version = version("worldgen")
    except PackageNotFoundError:
        package_version = "unknown (install the package before running this check)"

    import torch
    from worldgen import WorldGen

    print(f"python: {sys.version.split()[0]}")
    print(f"worldgen: {package_version}")
    print(f"worldgen module: {WorldGen.__module__}")
    print(f"torch: {torch.__version__}")
    print(f"torch CUDA runtime: {torch.version.cuda}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"WorldGen.__init__: {inspect.signature(WorldGen)}")
    print(f"WorldGen.generate_world: {inspect.signature(WorldGen.generate_world)}")

    if torch.cuda.is_available():
        device = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        torch.empty((1,), device="cuda")
        print(f"CUDA device: {device} (compute capability {capability[0]}.{capability[1]})")
        print("CUDA allocation: passed")
    else:
        print("CUDA allocation: skipped (WorldGen generation requires a CUDA-capable torch install)")

    if args.demo_help:
        demo = Path(__file__).resolve().parent / "worldgen_demo.py"
        subprocess.run([sys.executable, str(demo), "--help"], check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
