#!/usr/bin/env python3
"""Plan an Ultralytics YOLO export command without running export."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
from pathlib import Path

FORMAT_INFO = {
    "torchscript": {
        "name": "TorchScript",
        "suffix": ".torchscript",
        "cpu": True,
        "gpu": True,
        "args": ["batch", "optimize", "half", "nms", "dynamic"],
        "extras": ["base install"],
        "notes": ["Use for PyTorch/C++ runtime deployment when ONNX is not required."],
    },
    "onnx": {
        "name": "ONNX",
        "suffix": ".onnx or _int8.onnx",
        "cpu": True,
        "gpu": True,
        "args": ["batch", "data", "dynamic", "half", "int8", "opset", "simplify", "nms", "fraction"],
        "extras": ["ultralytics[export-base]"],
        "notes": ["Best first choice for portable CPU/server deployment and Triton model repositories."],
    },
    "openvino": {
        "name": "OpenVINO",
        "suffix": "_openvino_model/",
        "cpu": True,
        "gpu": False,
        "args": ["batch", "data", "dynamic", "half", "int8", "nms", "fraction"],
        "extras": ["ultralytics[export-base]"],
        "notes": ["Best for Intel CPU/GPU/NPU inference; use device=intel:cpu/gpu/npu when running exported models."],
    },
    "engine": {
        "name": "TensorRT",
        "suffix": ".engine",
        "cpu": False,
        "gpu": True,
        "args": ["batch", "data", "dynamic", "half", "int8", "simplify", "nms", "fraction", "workspace", "device"],
        "extras": ["TensorRT/CUDA runtime", "ultralytics[export-base]"],
        "notes": ["Requires NVIDIA GPU or supported DLA; CPU-only export is not valid."],
    },
    "coreml": {
        "name": "CoreML",
        "suffix": ".mlpackage",
        "cpu": True,
        "gpu": False,
        "args": ["batch", "dynamic", "half", "int8", "nms"],
        "extras": ["ultralytics[export-coreml]", "ultralytics[export-base]"],
        "notes": ["Export is unsupported on Windows; Ultralytics CoreML predict/val execution is macOS-only."],
    },
    "saved_model": {
        "name": "TensorFlow SavedModel",
        "suffix": "_saved_model/",
        "cpu": True,
        "gpu": True,
        "args": ["batch", "data", "fraction", "int8", "keras", "nms"],
        "extras": ["ultralytics[export-tensorflow]", "ultralytics[export-base]"],
        "notes": ["Use a fresh environment if TensorFlow/protobuf/package conflicts appear."],
    },
    "pb": {
        "name": "TensorFlow GraphDef",
        "suffix": ".pb",
        "cpu": True,
        "gpu": True,
        "args": ["batch"],
        "extras": ["ultralytics[export-tensorflow]", "ultralytics[export-base]"],
        "notes": ["Only batch is a supported export knob."],
    },
    "tflite": {
        "name": "TensorFlow Lite",
        "suffix": ".tflite",
        "cpu": True,
        "gpu": False,
        "args": ["batch", "data", "half", "int8", "nms", "fraction"],
        "extras": ["ultralytics[export-tensorflow]", "ultralytics[export-base]"],
        "notes": ["Use for mobile/embedded TensorFlow Lite deployment."],
    },
    "edgetpu": {
        "name": "TensorFlow Edge TPU",
        "suffix": "_edgetpu.tflite",
        "cpu": True,
        "gpu": False,
        "args": ["data", "fraction", "int8"],
        "extras": ["ultralytics[export-tensorflow]", "Edge TPU compiler"],
        "notes": ["Requires non-aarch64 Linux and edgetpu_compiler; batch is forced to 1."],
    },
    "tfjs": {
        "name": "TensorFlow.js",
        "suffix": "_web_model/",
        "cpu": True,
        "gpu": False,
        "args": ["batch", "data", "fraction", "half", "int8", "nms"],
        "extras": ["ultralytics[export-tensorflow]", "ultralytics[export-base]"],
        "notes": ["Not supported on ARM64 Linux."],
    },
    "mnn": {
        "name": "MNN",
        "suffix": ".mnn",
        "cpu": True,
        "gpu": True,
        "args": ["batch", "half", "int8"],
        "extras": ["MNN", "ultralytics[export-base]"],
        "notes": ["May need isolation from TensorFlow/protobuf-heavy workflows."],
    },
    "ncnn": {
        "name": "NCNN",
        "suffix": "_ncnn_model/",
        "cpu": True,
        "gpu": True,
        "args": ["batch", "half"],
        "extras": ["ncnn", "pnnx", "ultralytics[export-base]"],
        "notes": ["Common for mobile/embedded native runtimes."],
    },
    "imx": {
        "name": "IMX",
        "suffix": "_imx_model/",
        "cpu": True,
        "gpu": True,
        "args": ["data", "int8", "fraction", "nms"],
        "extras": ["isolated IMX export environment"],
        "notes": ["Requires specialized package set and supports selected tasks/model families."],
    },
    "rknn": {
        "name": "RKNN",
        "suffix": "_rknn_model/",
        "cpu": False,
        "gpu": False,
        "args": ["batch", "name", "half", "int8", "data", "fraction"],
        "extras": ["isolated RKNN export environment"],
        "notes": ["Requires name=<Rockchip target>, such as rk3588; some targets force int8."],
    },
    "executorch": {
        "name": "ExecuTorch",
        "suffix": "_executorch_model/",
        "cpu": True,
        "gpu": False,
        "args": ["batch"],
        "extras": ["ultralytics[export-executorch]", "ultralytics[export-base]"],
        "notes": ["Exports a directory containing ExecuTorch artifacts for supported runtimes."],
    },
    "axelera": {
        "name": "Axelera AI",
        "suffix": "_axelera_model/",
        "cpu": False,
        "gpu": False,
        "args": ["batch", "int8", "fraction", "data"],
        "extras": ["isolated Axelera export environment"],
        "notes": ["Requires vendor SDK and calibration data; inference requires Axelera hardware."],
    },
    "deepx": {
        "name": "DEEPX",
        "suffix": "_deepx_model/",
        "cpu": False,
        "gpu": False,
        "args": ["data", "int8", "optimize"],
        "extras": ["isolated DEEPX export environment"],
        "notes": ["Requires vendor packages and target hardware for inference."],
    },
    "qnn": {
        "name": "Qualcomm QNN",
        "suffix": "_qnn.onnx",
        "cpu": False,
        "gpu": False,
        "args": ["batch", "name", "int8", "fraction", "data"],
        "extras": ["onnxruntime QNN Execution Provider availability", "ultralytics[export-base]"],
        "notes": ["Requires name=<HTP architecture>, such as 73 or v73, for the target Snapdragon class."],
    },
}

ALIASES = {
    "tensorrt": "engine",
    "trt": "engine",
    "mlmodel": "coreml",
    "mlpackage": "coreml",
    "mlprogram": "coreml",
    "apple": "coreml",
    "ios": "coreml",
}

BOOLEAN_FLAGS = ["dynamic", "half", "int8", "nms", "simplify", "keras", "optimize"]
VALUE_ARGS = ["imgsz", "batch", "data", "fraction", "opset", "workspace", "device", "name"]
COMMON_ARGS = {"imgsz", "device"}


def normalize_format(value: str) -> str:
    normalized = value.lower().strip()
    return ALIASES.get(normalized, normalized)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan a safe Ultralytics YOLO export command without running export.")
    parser.add_argument("--model", default="yolo26n.pt", help="Model weights path or official model name to export.")
    parser.add_argument("--format", default="onnx", help="Export format, e.g. onnx, openvino, engine, coreml, tflite.")
    parser.add_argument("--task", choices=["classify", "detect", "obb", "pose", "segment", "semantic"], help="Optional CLI task prefix.")
    parser.add_argument("--benchmark", action="store_true", help="Plan yolo benchmark instead of yolo export.")
    parser.add_argument("--json-only", action="store_true", help="Emit compact JSON only.")
    for flag in BOOLEAN_FLAGS:
        parser.add_argument(f"--{flag}", action="store_true", help=f"Include {flag}=True if supported by the format.")
    for name in VALUE_ARGS:
        parser.add_argument(f"--{name}", help=f"Include {name}=<value> if supported by the format.")
    return parser.parse_args()


def build_plan(args: argparse.Namespace) -> dict:
    fmt = normalize_format(args.format)
    warnings = []
    errors = []
    if fmt not in FORMAT_INFO:
        return {
            "ok": False,
            "format": fmt,
            "errors": [f"Unsupported format '{args.format}'. Valid formats: {', '.join(sorted(FORMAT_INFO))}"],
        }

    info = FORMAT_INFO[fmt]
    requested = {}
    for flag in BOOLEAN_FLAGS:
        if getattr(args, flag):
            requested[flag] = "True"
    for name in VALUE_ARGS:
        value = getattr(args, name)
        if value not in (None, ""):
            requested[name] = str(value)

    unsupported = sorted(key for key in requested if key not in info["args"] and key not in COMMON_ARGS)
    if unsupported:
        errors.append(f"Unsupported for format={fmt}: {', '.join(unsupported)}")

    if args.half and args.int8:
        warnings.append("half=True and int8=True are mutually exclusive; exporter will disable half.")
    if args.int8 and "data" in info["args"] and not args.data:
        warnings.append("int8=True should include data=<dataset.yaml> for representative calibration.")
    if fmt == "engine":
        device = str(args.device or "0")
        if device.lower() == "cpu":
            errors.append("TensorRT format=engine requires NVIDIA GPU/DLA; use ONNX or OpenVINO for CPU deployment.")
        elif args.device is None:
            warnings.append("TensorRT export auto-selects device=0 when device is omitted.")
        if not shutil.which("nvidia-smi") and platform.system() != "Darwin":
            warnings.append("nvidia-smi was not found; verify CUDA/NVIDIA visibility before running TensorRT export.")
    if fmt == "coreml" and platform.system() == "Windows":
        errors.append("CoreML export is not supported on Windows.")
    if fmt == "edgetpu":
        machine = platform.machine().lower()
        if platform.system() != "Linux" or machine in {"aarch64", "arm64"}:
            errors.append("Edge TPU export requires non-aarch64 Linux.")
        if not shutil.which("edgetpu_compiler"):
            warnings.append("edgetpu_compiler was not found; install it before Edge TPU export.")
    if fmt == "tfjs" and platform.system() == "Linux" and platform.machine().lower() in {"aarch64", "arm64"}:
        errors.append("TF.js export is not supported on ARM64 Linux.")
    if args.benchmark and args.imgsz and "," in args.imgsz:
        warnings.append("benchmark() supports square image sizes; prefer a single integer imgsz.")

    mode = "benchmark" if args.benchmark else "export"
    command = ["yolo"]
    if args.task:
        command.append(args.task)
    command.append(mode)
    command.append(f"model={args.model}")
    command.append(f"format={fmt}")

    for key in ["imgsz", "batch", "device", "data", "fraction", "opset", "workspace", "name"]:
        if key in requested and (key in info["args"] or key in COMMON_ARGS):
            command.append(f"{key}={requested[key]}")
    for key in BOOLEAN_FLAGS:
        if key in requested and key in info["args"]:
            command.append(f"{key}=True")

    if fmt == "onnx" and any(extra == "ultralytics[export]" for extra in info["extras"]):
        warnings.append("ONNX only needs export-base; broad export extra is not required.")

    return {
        "ok": not errors,
        "mode": mode,
        "format": fmt,
        "format_name": info["name"],
        "output_suffix": info["suffix"],
        "command": " ".join(command),
        "supported_args": sorted(set(info["args"]) | COMMON_ARGS),
        "dependency_notes": info["extras"],
        "backend_notes": info["notes"],
        "warnings": warnings,
        "errors": errors,
        "side_effects_if_run": [
            "May download official model weights if not cached.",
            "Writes export artifacts near the model path or current working directory.",
            "Benchmark mode may export, validate, and time inference on data.",
        ],
    }


def main() -> int:
    args = parse_args()
    plan = build_plan(args)
    indent = None if args.json_only else 2
    print(json.dumps(plan, indent=indent, sort_keys=True))
    return 0 if plan.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
