#!/usr/bin/env python3
"""Probe the Diffusion Planner runtime without downloading or launching work."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Diffusion Planner imports, versions, and optional CUDA availability."
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="return non-zero unless torch reports a usable CUDA device",
    )
    args = parser.parse_args()

    distributions = [
        "diffusion_planner",
        "torch",
        "torchvision",
        "timm",
        "mmengine",
        "nuplan-devkit",
    ]
    for name in distributions:
        try:
            print(f"{name}: {importlib.metadata.version(name)}")
        except importlib.metadata.PackageNotFoundError:
            print(f"{name}: MISSING")

    modules = [
        "diffusion_planner",
        "diffusion_planner.model.diffusion_planner",
        "diffusion_planner.model.guidance.guidance_wrapper",
        "diffusion_planner.planner.planner",
    ]
    failures = []
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"import {name}: OK")
        except Exception as exc:  # diagnostic output should identify the module
            failures.append(name)
            print(f"import {name}: FAIL ({type(exc).__name__}: {exc})")

    cuda_ok = False
    try:
        import torch

        cuda_ok = bool(torch.cuda.is_available())
        print(f"torch CUDA: {'available' if cuda_ok else 'unavailable'}; devices={torch.cuda.device_count()}")
        if cuda_ok:
            print(f"device[0]: {torch.cuda.get_device_name(0)}")
            print(f"capability[0]: {torch.cuda.get_device_capability(0)}")
            # A tiny allocation is the backend smoke; no model/data is loaded.
            print(f"device allocation: {torch.ones(1, device='cuda').item()}")
    except Exception as exc:
        print(f"torch CUDA probe: FAIL ({type(exc).__name__}: {exc})")

    if failures or (args.require_cuda and not cuda_ok):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
