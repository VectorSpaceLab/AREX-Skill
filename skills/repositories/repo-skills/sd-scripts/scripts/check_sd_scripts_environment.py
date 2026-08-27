#!/usr/bin/env python3
"""Check common sd-scripts Python dependencies and optional backend facts."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from typing import Any

CORE_MODULES = [
    "torch",
    "accelerate",
    "transformers",
    "diffusers",
    "safetensors",
    "toml",
    "voluptuous",
    "PIL",
    "cv2",
    "numpy",
]

OPTIONAL_MODULES = [
    "xformers",
    "bitsandbytes",
    "lion_pytorch",
    "schedulefree",
    "prodigyopt",
    "sentencepiece",
    "onnxruntime",
]


def module_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": getattr(module, "__version__", None)}


def torch_backend() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"torch_imported": False, "error": f"{type(exc).__name__}: {exc}"}
    result: dict[str, Any] = {
        "torch_imported": True,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
    }
    if result["cuda_available"]:
        result["cuda_device_0"] = torch.cuda.get_device_name(0)
        result["cuda_capability_0"] = torch.cuda.get_device_capability(0)
    mps = getattr(torch.backends, "mps", None)
    if mps is not None:
        result["mps_available"] = bool(mps.is_available())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "core_modules": {name: module_status(name) for name in CORE_MODULES},
        "optional_modules": {name: module_status(name) for name in OPTIONAL_MODULES},
        "backend": torch_backend(),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"Python: {sys.version.split()[0]} on {platform.platform()}")
        print("\nCore modules:")
        for name, status in report["core_modules"].items():
            detail = status.get("version") if status["ok"] else status.get("error")
            print(f"  {name}: {'OK' if status['ok'] else 'MISSING/ERROR'} {detail or ''}")
        print("\nOptional modules:")
        for name, status in report["optional_modules"].items():
            detail = status.get("version") if status["ok"] else status.get("error")
            print(f"  {name}: {'OK' if status['ok'] else 'missing'} {detail or ''}")
        print("\nBackend:")
        for key, value in report["backend"].items():
            print(f"  {key}: {value}")
    missing_core = [name for name, status in report["core_modules"].items() if not status["ok"]]
    if missing_core:
        print("\nMissing core modules for many sd-scripts workflows: " + ", ".join(missing_core), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
