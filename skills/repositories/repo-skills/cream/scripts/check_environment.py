#!/usr/bin/env python3
"""Check the shared inspection environment for the Cream monorepo.

This script is intentionally generic: it reports whether selected Python
modules import, prints version metadata when available, and optionally checks
CUDA visibility.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from typing import Iterable


def _split_modules(values: Iterable[str]) -> list[str]:
    modules: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                modules.append(part)
    return modules


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the shared inspection environment")
    parser.add_argument(
        "--modules",
        action="append",
        default=[],
        help="Comma-separated module names to import and report.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Exit non-zero if torch reports that CUDA is unavailable.",
    )
    args = parser.parse_args()

    modules = _split_modules(args.modules) if args.modules else [
        "torch",
        "torchvision",
        "timm",
        "open_clip",
        "yacs",
        "easydict",
        "ftfy",
        "regex",
        "webdataset",
        "huggingface_hub",
        "submitit",
        "fvcore",
    ]

    ok = True
    print("module,status,version,location")
    for name in modules:
        spec = importlib.util.find_spec(name)
        if spec is None:
            print(f"{name},missing,,")
            ok = False
            continue
        try:
            module = importlib.import_module(name)
            version = getattr(module, "__version__", "") or getattr(module, "version", "")
            location = getattr(module, "__file__", "") or ""
            print(f"{name},ok,{version},{location}")
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"{name},error,{type(exc).__name__}:{exc},")
            ok = False

    try:
        import torch

        cuda_ok = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda_ok else 0
        print(f"torch.cuda.available,{cuda_ok},device_count={device_count},")
        if args.require_cuda and not cuda_ok:
            ok = False
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"torch.cuda.error,{type(exc).__name__}:{exc},,")
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
