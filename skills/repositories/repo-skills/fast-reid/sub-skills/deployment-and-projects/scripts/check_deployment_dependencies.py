#!/usr/bin/env python3
"""Probe FastReID deployment optional dependencies without downloads or training."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from typing import Any, Dict, List, Optional

DEPENDENCIES = [
    {
        "id": "torch",
        "module": "torch",
        "role": "Core FastReID model construction and PyTorch-side export",
        "backend_note": "Required for any PyTorch model build/export. CUDA availability depends on the installed torch build and host driver.",
    },
    {
        "id": "cv2",
        "module": "cv2",
        "role": "OpenCV image loading/preprocessing for deployment inference helpers",
        "backend_note": "Needed for image-based ONNX/Caffe/TensorRT inference preprocessing.",
    },
    {
        "id": "onnx",
        "module": "onnx",
        "role": "ONNX graph export/load/save",
        "backend_note": "Optional; ONNX export entrypoints may fail before --help if this is missing.",
    },
    {
        "id": "onnxoptimizer",
        "module": "onnxoptimizer",
        "role": "ONNX graph optimization passes",
        "backend_note": "Optional but expected by FastReID v1.3 ONNX export workflow.",
    },
    {
        "id": "onnxsim",
        "module": "onnxsim",
        "role": "ONNX graph simplification/validation",
        "backend_note": "Optional but expected by FastReID v1.3 ONNX export workflow.",
    },
    {
        "id": "onnxruntime",
        "module": "onnxruntime",
        "role": "ONNX Runtime feature inference and PyTorch-vs-ONNX comparison",
        "backend_note": "Optional; required for ONNX Runtime inference, separate from ONNX export.",
    },
    {
        "id": "caffe",
        "module": "caffe",
        "role": "Caffe model inference/conversion runtime",
        "backend_note": "Optional external runtime; generated protobuf/conversion helper code is not bundled by this skill.",
    },
    {
        "id": "tensorrt",
        "module": "tensorrt",
        "role": "TensorRT engine build/runtime APIs",
        "backend_note": "Optional NVIDIA/CUDA runtime; TensorRT entrypoints may fail before --help if this is missing.",
    },
]


def import_probe(dep: Dict[str, str]) -> Dict[str, Any]:
    module_name = dep["module"]
    result: Dict[str, Any] = {
        "id": dep["id"],
        "module": module_name,
        "role": dep["role"],
        "backend_note": dep["backend_note"],
        "status": "missing",
        "version": None,
        "details": {},
        "error": None,
    }
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # import may fail due package absence or missing shared libs
        result["status"] = "missing"
        result["error"] = f"{exc.__class__.__name__}: {exc}"
        return result

    result["status"] = "installed"
    version = getattr(module, "__version__", None)
    if version is None and module_name == "caffe":
        version = getattr(getattr(module, "__dict__", {}), "get", lambda _k, _d=None: None)("TEST", None)
    result["version"] = str(version) if version is not None else "unknown"

    if module_name == "torch":
        try:
            result["details"]["cuda_available"] = bool(module.cuda.is_available())
            result["details"]["cuda_device_count"] = int(module.cuda.device_count()) if module.cuda.is_available() else 0
            result["details"]["torch_cuda_version"] = getattr(module.version, "cuda", None)
        except Exception as exc:
            result["details"]["cuda_probe_error"] = f"{exc.__class__.__name__}: {exc}"
    elif module_name == "onnxruntime":
        try:
            result["details"]["providers"] = list(module.get_available_providers())
        except Exception as exc:
            result["details"]["provider_probe_error"] = f"{exc.__class__.__name__}: {exc}"
    elif module_name == "tensorrt":
        result["details"]["requires_cuda_runtime"] = True
    elif module_name == "caffe":
        result["details"]["mode_not_changed"] = True
        result["details"]["note"] = "Imported caffe without setting CPU/GPU mode."

    return result


def build_report() -> Dict[str, Any]:
    results = [import_probe(dep) for dep in DEPENDENCIES]
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "results": results,
        "summary": {
            "installed": [r["id"] for r in results if r["status"] == "installed"],
            "missing": [r["id"] for r in results if r["status"] != "installed"],
        },
        "backend_notes": {
            "onnx_export": "Needs torch, onnx, onnxoptimizer, and onnxsim; model weights/config are still required separately.",
            "onnx_inference": "Needs onnxruntime plus image preprocessing packages such as cv2/numpy.",
            "caffe": "Requires an external Caffe/PyCaffe/protobuf/conversion-helper environment; no generated protobuf is bundled here.",
            "tensorrt": "Requires TensorRT, CUDA/NVIDIA target runtime, and compatible serialized engines.",
        },
    }


def print_text(report: Dict[str, Any]) -> None:
    print(f"Python: {report['python']}")
    print(f"Platform: {report['platform']}")
    print("\nDependency status:")
    for item in report["results"]:
        status = item["status"].upper()
        version = item["version"] or "-"
        print(f"- {item['id']:<14} {status:<9} version={version}")
        print(f"  role: {item['role']}")
        print(f"  note: {item['backend_note']}")
        if item["details"]:
            print(f"  details: {json.dumps(item['details'], sort_keys=True)}")
        if item["error"]:
            print(f"  error: {item['error']}")
    print("\nBackend notes:")
    for key, value in report["backend_notes"].items():
        print(f"- {key}: {value}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe optional FastReID deployment dependencies without downloads, training, or writes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a JSON report instead of human-readable text",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any probed dependency is missing",
    )
    parser.add_argument(
        "--require",
        action="append",
        choices=[dep["id"] for dep in DEPENDENCIES],
        default=[],
        help="require a specific dependency; may be repeated. Missing required dependencies make the command exit non-zero.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    missing = set(report["summary"]["missing"])
    if args.strict and missing:
        return 1
    if args.require and any(dep in missing for dep in args.require):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
