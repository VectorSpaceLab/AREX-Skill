#!/usr/bin/env python3
"""Check RFdiffusion imports, optional backend visibility, and model-weight files.

This diagnostic is read-only. It does not download weights or run diffusion.
Example:
  python check_rfdiffusion_environment.py --models /path/to/models --require Base_ckpt.pt
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
from pathlib import Path

MODULES = [
    "rfdiffusion",
    "rfdiffusion.contigs",
    "rfdiffusion.diffusion",
    "rfdiffusion.inference.utils",
    "rfdiffusion.inference.symmetry",
    "rfdiffusion.potentials.manager",
    "rfdiffusion.potentials.potentials",
]

DEFAULT_WEIGHTS = [
    "Base_ckpt.pt",
    "Complex_base_ckpt.pt",
    "Complex_Fold_base_ckpt.pt",
    "InpaintSeq_ckpt.pt",
    "InpaintSeq_Fold_ckpt.pt",
    "ActiveSite_ckpt.pt",
    "Base_epoch8_ckpt.pt",
]


def check_imports() -> int:
    failures = 0
    for module_name in MODULES:
        try:
            importlib.import_module(module_name)
            print(f"PASS import {module_name}")
        except Exception as exc:  # pragma: no cover - diagnostic surface
            failures += 1
            print(f"FAIL import {module_name}: {type(exc).__name__}: {exc}")
    for dist_name in ("rfdiffusion", "se3-transformer"):
        try:
            print(f"INFO dist {dist_name} {metadata.version(dist_name)}")
        except metadata.PackageNotFoundError:
            print(f"WARN dist {dist_name} metadata not found")
    return failures


def check_torch() -> None:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - optional dependency check
        print(f"WARN torch import failed: {type(exc).__name__}: {exc}")
        return
    print(f"INFO torch {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"INFO torch.cuda.is_available {cuda_available}")
    if cuda_available:
        print(f"INFO cuda device {torch.cuda.get_device_name(torch.cuda.current_device())}")
    else:
        print("WARN no CUDA device visible; real RFdiffusion inference may be slow or impractical")


def check_models(model_dir: str | None, required: list[str], check_defaults: bool) -> int:
    if not model_dir:
        if required or check_defaults:
            print("FAIL --models is required when checking model files")
            return 1
        print("INFO no --models directory supplied; skipping model-weight checks")
        return 0
    root = Path(model_dir).expanduser()
    if not root.exists() or not root.is_dir():
        print(f"FAIL models directory does not exist or is not a directory: {root}")
        return 1
    names = list(required)
    if check_defaults:
        names.extend(name for name in DEFAULT_WEIGHTS if name not in names)
    failures = 0
    for name in names:
        path = root / name
        if path.exists() and path.is_file():
            print(f"PASS model {name}")
        else:
            failures += 1
            print(f"FAIL missing model {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", help="Directory containing RFdiffusion checkpoint files")
    parser.add_argument("--require", action="append", default=[], help="Required checkpoint filename; may be repeated")
    parser.add_argument("--check-default-weights", action="store_true", help="Check the common documented checkpoint filenames")
    args = parser.parse_args()

    failures = 0
    failures += check_imports()
    check_torch()
    failures += check_models(args.models, args.require, args.check_default_weights)
    if failures:
        print(f"SUMMARY failed checks: {failures}")
        return 1
    print("SUMMARY RFdiffusion environment preflight passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
