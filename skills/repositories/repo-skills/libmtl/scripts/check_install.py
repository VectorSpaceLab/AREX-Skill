#!/usr/bin/env python3
"""Check that the LibMTL runtime environment is ready for inspection.

This script is intentionally small and read-only. It verifies the installed
package set, imports the public package, and performs a tiny CUDA smoke test
when a GPU is available.
"""

from __future__ import annotations

import argparse
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version


REQUIRED_DISTS = [
    "LibMTL",
    "torch",
    "torchvision",
    "torch-geometric",
    "cvxpy",
    "qpsolvers",
    "transformers",
]


def _show_versions() -> None:
    for dist in REQUIRED_DISTS:
        try:
            print(f"{dist}: {version(dist)}")
        except PackageNotFoundError:
            raise SystemExit(f"missing distribution: {dist}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the LibMTL install")
    parser.add_argument(
        "--allow-cpu-only",
        action="store_true",
        help="Do not fail if no CUDA device is visible.",
    )
    args = parser.parse_args()

    _show_versions()

    libmtl = import_module("LibMTL")
    print(f"LibMTL.__file__: {libmtl.__file__}")

    torch = import_module("torch")
    transformers = import_module("transformers")
    print(f"torch.cuda.is_available: {torch.cuda.is_available()}")
    print(f"transformers.AdamW: {hasattr(transformers, 'AdamW')}")
    print(f"transformers.DataProcessor: {hasattr(transformers, 'DataProcessor')}")

    if torch.cuda.is_available():
        x = torch.tensor([1.0], device="cuda")
        print(f"cuda smoke tensor: {x.item()}")
    elif not args.allow_cpu_only:
        raise SystemExit("CUDA is required for the LibMTL benchmark workflows")

    print("install check: ok")


if __name__ == "__main__":
    main()
