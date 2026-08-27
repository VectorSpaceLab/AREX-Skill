#!/usr/bin/env python3
"""Import-check the core source modules from a checkout of 3D-ResNets-PyTorch."""

from __future__ import annotations

import argparse
import importlib
import inspect
from pathlib import Path

from _torchvision_compat import prepare_source_runtime

MODULES = [
    "opts",
    "model",
    "dataset",
    "utils",
    "training",
    "validation",
    "inference",
    "mean",
    "spatial_transforms",
    "temporal_transforms",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import the core 3D-ResNets-PyTorch modules.")
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
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    prepare_source_runtime(repo_root, with_scale_shim=not args.no_scale_shim)

    imported = []
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        imported.append(module_name)
        print(f"imported {module_name}: {getattr(module, '__file__', '<built-in>')}")

    model = importlib.import_module("model")
    print("generate_model signature:", inspect.signature(model.generate_model))
    print("load_pretrained_model signature:", inspect.signature(model.load_pretrained_model))
    print("make_data_parallel signature:", inspect.signature(model.make_data_parallel))
    print("imported modules:", ", ".join(imported))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
