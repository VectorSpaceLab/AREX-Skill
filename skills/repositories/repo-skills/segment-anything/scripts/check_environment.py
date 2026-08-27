#!/usr/bin/env python3
"""
Safe Segment Anything environment diagnostic.

This script checks importability, model registry keys, PyTorch backend status,
and optional workflow dependencies. It does not download checkpoints or run SAM
inference.

Example:
  python scripts/check_environment.py --check-optional
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


def check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic surface
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Segment Anything runtime dependencies.")
    parser.add_argument(
        "--check-optional",
        action="store_true",
        help="Also check optional OpenCV, pycocotools, ONNX, and ONNXRuntime packages.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    args = parser.parse_args()

    report: dict[str, Any] = {"python": sys.version.split()[0], "imports": {}}
    report["imports"]["segment_anything"] = check_import("segment_anything")
    report["imports"]["torch"] = check_import("torch")
    report["imports"]["torchvision"] = check_import("torchvision")

    if report["imports"]["segment_anything"]["ok"]:
        from segment_anything import sam_model_registry

        report["sam_model_registry"] = sorted(sam_model_registry.keys())

    if report["imports"]["torch"]["ok"]:
        import torch

        report["torch_backend"] = {
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
            "cuda_version": getattr(torch.version, "cuda", None),
        }

    if args.check_optional:
        for module_name in ["cv2", "pycocotools", "matplotlib", "onnx", "onnxruntime"]:
            report["imports"][module_name] = check_import(module_name)

    required_ok = all(
        report["imports"][name]["ok"] for name in ["segment_anything", "torch", "torchvision"]
    )
    report["ok"] = required_ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if not required_ok:
            print("\nRequired imports failed. Install segment_anything, torch, and torchvision.")

    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
