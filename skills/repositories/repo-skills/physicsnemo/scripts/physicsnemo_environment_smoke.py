#!/usr/bin/env python3
"""Minimal PhysicsNeMo smoke for installed-package inspection.

This script is safe to run in a small CPU or CUDA environment. It prints
package and backend facts without downloading data or running training.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from pathlib import Path

MODULES = [
    "physicsnemo",
    "physicsnemo.core",
    "physicsnemo.models",
    "physicsnemo.datapipes",
    "physicsnemo.distributed",
    "physicsnemo.domain_parallel",
    "physicsnemo.diffusion",
    "physicsnemo.mesh",
    "physicsnemo.metrics",
    "physicsnemo.optim",
    "physicsnemo.utils",
    "physicsnemo.deploy",
    "physicsnemo.active_learning",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    payload: dict[str, object] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "cwd": str(Path.cwd()),
        "modules": {},
    }

    for name in MODULES:
        try:
            mod = importlib.import_module(name)
            payload["modules"][name] = getattr(mod, "__file__", None)
        except Exception as exc:  # pragma: no cover - smoke path only
            payload["modules"][name] = f"ERROR: {type(exc).__name__}: {exc}"

    for dist_name in ["nvidia-physicsnemo", "torch", "pytest"]:
        try:
            payload[dist_name] = metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            payload[dist_name] = None

    try:
        import torch

        cuda = {
            "available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
        }
        if torch.cuda.is_available():
            x = torch.ones(2, device="cuda")
            cuda["tensor_smoke"] = float((x + x).sum().cpu())
        payload["cuda"] = cuda
    except Exception as exc:  # pragma: no cover - smoke path only
        payload["cuda"] = f"ERROR: {type(exc).__name__}: {exc}"

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
