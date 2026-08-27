#!/usr/bin/env python3
"""Read-only MedMNIST installation and registry diagnostic.

Run from any directory after installing the public package. It does not create
roots, download data, import notebooks, or touch default MedMNIST files.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check medmnist import, version, registry, and CPU torch availability."
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="also require torch.cuda.is_available(); not needed by MedMNIST itself",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        import medmnist
        import torch
        import torchvision
    except ImportError as exc:
        print(f"CHECK FAILED: missing runtime dependency: {exc}", file=sys.stderr)
        return 2

    try:
        package_version = importlib.metadata.version("medmnist")
    except importlib.metadata.PackageNotFoundError:
        package_version = "unknown"

    print(f"medmnist.__version__: {medmnist.__version__}")
    print(f"distribution version: {package_version}")
    print(f"registry entries: {len(medmnist.INFO)}")
    print(f"torch: {torch.__version__}")
    print(f"torchvision: {torchvision.__version__}")
    print(f"torch CPU tensor sum: {torch.zeros(2, 3).add(1).sum().item():.1f}")
    print(f"torch CUDA available: {torch.cuda.is_available()}")

    if args.require_cuda and not torch.cuda.is_available():
        print("CHECK FAILED: --require-cuda requested but CUDA is unavailable", file=sys.stderr)
        return 2
    if len(medmnist.INFO) != 18:
        print("CHECK WARNING: registry size differs from the inspected 3.0.2 baseline")
    print("CHECK PASS: import and read-only package diagnostics completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
