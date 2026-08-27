#!/usr/bin/env python3
"""Report DAMO-YOLO deployment optional dependency readiness."""

from __future__ import annotations

import argparse
import importlib.util
import json
from typing import Any


def module_status(import_name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(import_name)
    result: dict[str, Any] = {"module": import_name, "available": spec is not None}
    if spec is None:
        return result
    try:
        module = __import__(import_name)
        result["version"] = getattr(module, "__version__", "unknown")
    except Exception as exc:  # pragma: no cover - diagnostic only
        result["available"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check optional DAMO-YOLO deployment dependencies")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    modules = [
        "damo",
        "torch",
        "torchvision",
        "onnx",
        "onnxruntime",
        "onnxsim",
        "tensorrt",
        "cuda",
        "pycuda",
        "pytorch_quantization",
    ]
    report = {"modules": [module_status(name) for name in modules], "torch_cuda": {}}

    if importlib.util.find_spec("torch"):
        try:
            import torch

            report["torch_cuda"] = {
                "available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
                "torch_version": getattr(torch, "__version__", "unknown"),
                "torch_cuda_version": getattr(torch.version, "cuda", None),
            }
            if torch.cuda.is_available():
                report["torch_cuda"]["device0"] = torch.cuda.get_device_name(0)
                report["torch_cuda"]["capability0"] = list(torch.cuda.get_device_capability(0))
        except Exception as exc:  # pragma: no cover - diagnostic only
            report["torch_cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("DAMO-YOLO deployment dependency readiness")
    print("=" * 44)
    for item in report["modules"]:
        if item["available"]:
            print(f"OK   {item['module']}: {item.get('version', 'available')}")
        else:
            suffix = f" ({item['error']})" if "error" in item else ""
            print(f"MISS {item['module']}{suffix}")
    cuda = report["torch_cuda"]
    if cuda:
        print("\nTorch CUDA:")
        for key, value in cuda.items():
            print(f"  {key}: {value}")
    print("\nInterpretation:")
    print("- ONNX export needs damo, torch, torchvision, and onnx.")
    print("- ONNX inference needs onnxruntime.")
    print("- TensorRT engine build/eval needs tensorrt plus CUDA Python or PyCUDA/runtime libraries.")
    print("- Partial INT8 quantization also needs pytorch_quantization and calibration images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
