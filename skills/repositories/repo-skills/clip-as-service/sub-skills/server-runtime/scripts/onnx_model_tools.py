#!/usr/bin/env python3
"""Optional ONNX model conversion helpers for CLIP-as-service workflows.

These helpers require optional ONNX dependencies and user-supplied model files.
They do not download models or start a CLIP server.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"input model does not exist or is not a file: {path}")


def convert_fp16(input_model: Path, output_model: Path) -> None:
    try:
        import onnx
        from onnxmltools.utils.float16_converter import convert_float_to_float16_model_path
    except ImportError as exc:
        raise SystemExit("Install ONNX optional dependencies first: pip install 'clip-server[onnx]' onnx onnxmltools") from exc
    require_file(input_model)
    output_model.parent.mkdir(parents=True, exist_ok=True)
    model_fp16 = convert_float_to_float16_model_path(str(input_model))
    onnx.save(model_fp16, str(output_model))


def quantize_dynamic(input_model: Path, output_model: Path) -> None:
    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic as ort_quantize_dynamic
    except ImportError as exc:
        raise SystemExit("Install onnxruntime quantization dependencies first: pip install 'clip-server[onnx]'") from exc
    require_file(input_model)
    output_model.parent.mkdir(parents=True, exist_ok=True)
    ort_quantize_dynamic(
        model_input=str(input_model),
        model_output=str(output_model),
        per_channel=True,
        reduce_range=True,
        activation_type=QuantType.QUInt8,
        weight_type=QuantType.QInt8,
        op_types_to_quantize=["MatMul", "Attention", "Mul", "Add"],
        extra_options={"WeightSymmetric": False, "MatMulConstBOnly": True},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="CLIP-as-service ONNX helper tools.")
    sub = parser.add_subparsers(dest="command", required=True)

    fp16 = sub.add_parser("fp16", help="Convert an ONNX model from fp32 to fp16.")
    fp16.add_argument("input_model", type=Path)
    fp16.add_argument("output_model", type=Path)

    quant = sub.add_parser("quantize", help="Apply dynamic ONNX quantization for CPU-oriented serving experiments.")
    quant.add_argument("input_model", type=Path)
    quant.add_argument("output_model", type=Path)

    args = parser.parse_args()
    if args.command == "fp16":
        convert_fp16(args.input_model, args.output_model)
    elif args.command == "quantize":
        quantize_dynamic(args.input_model, args.output_model)
    print(f"wrote {args.output_model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
