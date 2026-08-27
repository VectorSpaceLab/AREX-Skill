#!/usr/bin/env python3
"""Print or validate YOLOv3 export format choices without exporting weights."""
from __future__ import annotations

import argparse
import json

ROWS = [
    {"format": "PyTorch", "argument": "-", "suffix": ".pt", "cpu": True, "gpu": True, "implemented_export": False},
    {"format": "TorchScript", "argument": "torchscript", "suffix": ".torchscript", "cpu": True, "gpu": True, "implemented_export": True},
    {"format": "ONNX", "argument": "onnx", "suffix": ".onnx", "cpu": True, "gpu": True, "implemented_export": True},
    {"format": "OpenVINO", "argument": "openvino", "suffix": "_openvino_model", "cpu": True, "gpu": False, "implemented_export": True},
    {"format": "TensorRT", "argument": "engine", "suffix": ".engine", "cpu": False, "gpu": True, "implemented_export": True},
    {"format": "CoreML", "argument": "coreml", "suffix": ".mlmodel", "cpu": True, "gpu": False, "implemented_export": True},
    {"format": "TensorFlow SavedModel", "argument": "saved_model", "suffix": "_saved_model", "cpu": True, "gpu": True, "implemented_export": False},
    {"format": "TensorFlow GraphDef", "argument": "pb", "suffix": ".pb", "cpu": True, "gpu": True, "implemented_export": False},
    {"format": "TensorFlow Lite", "argument": "tflite", "suffix": ".tflite", "cpu": True, "gpu": False, "implemented_export": False},
    {"format": "TensorFlow Edge TPU", "argument": "edgetpu", "suffix": "_edgetpu.tflite", "cpu": False, "gpu": False, "implemented_export": False},
    {"format": "TensorFlow.js", "argument": "tfjs", "suffix": "_web_model", "cpu": False, "gpu": False, "implemented_export": False},
    {"format": "PaddlePaddle", "argument": "paddle", "suffix": "_paddle_model", "cpu": True, "gpu": True, "implemented_export": True},
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect YOLOv3 export formats and validate --include choices.")
    parser.add_argument("--include", nargs="*", help="format arguments to validate")
    parser.add_argument("--strict", action="store_true", help="fail for known but non-implemented export rows")
    parser.add_argument("--format", choices=("table", "json"), default="table")
    args = parser.parse_args()
    rows = ROWS
    status = 0
    errors = []
    if args.include:
        by_arg = {row["argument"]: row for row in ROWS}
        rows = []
        for item in args.include:
            row = by_arg.get(item)
            if row is None:
                errors.append(f"unknown include value: {item}")
                status = 2
                continue
            if args.strict and not row["implemented_export"]:
                errors.append(f"not implemented by export.py: {item}")
                status = 2
            rows.append(row)
    payload = {"rows": rows, "errors": errors}
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print("argument\tformat\tsuffix\tcpu\tgpu\timplemented_export")
        for row in rows:
            print(f"{row['argument']}\t{row['format']}\t{row['suffix']}\t{row['cpu']}\t{row['gpu']}\t{row['implemented_export']}")
        for error in errors:
            print(f"ERROR: {error}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
