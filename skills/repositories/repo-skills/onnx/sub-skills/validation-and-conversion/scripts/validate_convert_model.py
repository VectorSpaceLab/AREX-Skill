#!/usr/bin/env python3
"""Validate, infer, print, and optionally convert a small ONNX model.

This script is safe by default and works with either a provided model path or a
built-in tiny Add fixture. It does not download data or mutate files unless the
caller explicitly asks for an output path.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import onnx
from onnx import TensorProto, helper, shape_inference


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and optionally convert an ONNX model.")
    parser.add_argument("--model", help="Path to an ONNX model file. If omitted, a tiny Add model is generated.")
    parser.add_argument("--format", default=None, help="Optional ONNX serializer format for the input/output model.")
    parser.add_argument("--output", help="Optional output path for the transformed model.")
    parser.add_argument("--infer-shapes", action="store_true", help="Run shape inference before reporting or saving.")
    parser.add_argument("--strict", action="store_true", help="Enable strict shape inference.")
    parser.add_argument("--data-prop", action="store_true", help="Enable data propagation during shape inference.")
    parser.add_argument("--print-text", action="store_true", help="Print compact ONNX text for the resulting model.")
    parser.add_argument("--target-opset", type=int, help="Convert the model to this default-domain opset version.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of a short text summary.")
    return parser.parse_args()


def tiny_model() -> onnx.ModelProto:
    x = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2])
    y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [2])
    z = helper.make_tensor_value_info("Z", TensorProto.FLOAT, [2])
    node = helper.make_node("Add", ["X", "Y"], ["Z"])
    graph = helper.make_graph([node], "tiny-add", [x, y], [z])
    return helper.make_model(graph, opset_imports=[helper.make_opsetid("", 14)])


def summarize(model: onnx.ModelProto) -> dict[str, Any]:
    g = model.graph
    return {
        "ir_version": model.ir_version,
        "opset_imports": {entry.domain or "": entry.version for entry in model.opset_import},
        "graph_name": g.name,
        "inputs": [value.name for value in g.input],
        "outputs": [value.name for value in g.output],
        "nodes": [node.op_type for node in g.node],
    }


def main() -> int:
    args = parse_args()
    if args.model:
        model = onnx.load_model(args.model, format=args.format)
    else:
        model = tiny_model()

    onnx.checker.check_model(model)
    if args.infer_shapes:
        model = shape_inference.infer_shapes(model, strict_mode=args.strict, data_prop=args.data_prop)
        onnx.checker.check_model(model)

    if args.target_opset is not None:
        model = onnx.version_converter.convert_version(model, args.target_opset)
        onnx.checker.check_model(model)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        onnx.save_model(model, os.fspath(output))

    if args.print_text:
        print(onnx.printer.to_text(model))

    summary = summarize(model)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"ONNX ok: ir={summary['ir_version']} opsets={summary['opset_imports']} "
            f"nodes={summary['nodes']} inputs={summary['inputs']} outputs={summary['outputs']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
