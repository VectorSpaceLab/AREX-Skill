#!/usr/bin/env python3
"""Safe MONAI environment check for agents.

This script imports MONAI and selected optional dependencies, reports Torch
backend facts, and optionally checks MONAI Bundle/Auto3DSeg CLI help. It does
not download data, train, write checkpoints, or require repository source files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import subprocess
import sys
from typing import Any


OPTIONAL_MODULES = [
    "nibabel",
    "pydicom",
    "itk",
    "PIL",
    "skimage",
    "ignite",
    "fire",
    "jsonschema",
    "yaml",
    "onnx",
    "onnxruntime",
    "nni",
    "optuna",
    "mlflow",
    "clearml",
    "huggingface_hub",
]


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def import_version(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": getattr(module, "__version__", None)}


def run_help(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "first_lines": proc.stdout.splitlines()[:12],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe MONAI import, backend, optional dependency, and CLI checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a readable summary.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip MONAI Bundle and Auto3DSeg CLI help checks.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "required": {},
        "optional_modules": {},
        "torch_backend": {},
        "cli": {},
    }

    for module_name in ["monai", "torch", "numpy"]:
        report["required"][module_name] = import_version(module_name)

    try:
        import torch

        report["torch_backend"] = {
            "torch_version": getattr(torch, "__version__", None),
            "cuda_runtime": getattr(torch.version, "cuda", None),
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available():
            report["torch_backend"]["device_0"] = torch.cuda.get_device_name(0)
            report["torch_backend"]["capability_0"] = torch.cuda.get_device_capability(0)
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["torch_backend"] = {"error": f"{type(exc).__name__}: {exc}"}

    for module_name in OPTIONAL_MODULES:
        report["optional_modules"][module_name] = module_available(module_name)

    if not args.skip_cli:
        report["cli"]["monai.bundle"] = run_help([sys.executable, "-m", "monai.bundle", "--help"])
        report["cli"]["monai.apps.auto3dseg"] = run_help([sys.executable, "-m", "monai.apps.auto3dseg", "--", "--help"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        for name, info in report["required"].items():
            print(f"{name}: {info}")
        print(f"Torch backend: {report['torch_backend']}")
        available = [name for name, ok in report["optional_modules"].items() if ok]
        missing = [name for name, ok in report["optional_modules"].items() if not ok]
        print(f"Optional available: {', '.join(available) if available else 'none'}")
        print(f"Optional missing: {', '.join(missing) if missing else 'none'}")
        for name, info in report["cli"].items():
            print(f"{name} help: {info}")

    required_ok = all(info.get("ok") for info in report["required"].values())
    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
