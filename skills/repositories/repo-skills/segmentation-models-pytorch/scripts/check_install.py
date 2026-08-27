#!/usr/bin/env python3
"""Diagnose a segmentation_models_pytorch installation.

This helper is safe by default: it imports packages, reads metadata, inspects
architecture names, and optionally reports CUDA visibility. It does not download
weights, train models, contact the Hugging Face Hub, or mutate the environment.

Example:
    python check_install.py --check-cuda
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import sys
from typing import Any


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - diagnostic surface
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "version": getattr(module, "__version__", None),
        "module": module.__name__,
    }


def distribution_status(distribution_name: str) -> dict[str, Any]:
    try:
        version = metadata.version(distribution_name)
        requires = metadata.requires(distribution_name) or []
    except metadata.PackageNotFoundError:
        return {"ok": False, "error": "distribution metadata not found"}
    return {"ok": True, "version": version, "requires_count": len(requires)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SMP import, metadata, dependencies, and optional CUDA visibility.")
    parser.add_argument("--check-cuda", action="store_true", help="Also report torch CUDA availability and one tiny allocation when possible.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "distribution": distribution_status("segmentation_models_pytorch"),
        "imports": {},
        "architecture_count": None,
        "architectures": [],
        "cuda": None,
    }

    for module_name in [
        "segmentation_models_pytorch",
        "torch",
        "torchvision",
        "timm",
        "huggingface_hub",
        "safetensors",
    ]:
        result["imports"][module_name] = import_status(module_name)

    smp_status = result["imports"]["segmentation_models_pytorch"]
    if smp_status["ok"]:
        import segmentation_models_pytorch as smp

        architectures = sorted(getattr(smp, "MODEL_ARCHITECTURES_MAPPING", {}).keys())
        result["architecture_count"] = len(architectures)
        result["architectures"] = architectures

    if args.check_cuda and result["imports"]["torch"]["ok"]:
        import torch

        cuda: dict[str, Any] = {
            "torch_version": torch.__version__,
            "torch_cuda_version": getattr(torch.version, "cuda", None),
            "is_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available():
            cuda["device_name_0"] = torch.cuda.get_device_name(0)
            cuda["capability_0"] = torch.cuda.get_device_capability(0)
            try:
                torch.empty((1,), device="cuda")
                cuda["tiny_allocation"] = "ok"
            except Exception as exc:  # pragma: no cover - hardware diagnostic
                cuda["tiny_allocation"] = f"failed: {type(exc).__name__}: {exc}"
        result["cuda"] = cuda

    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if smp_status["ok"] and result["distribution"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
