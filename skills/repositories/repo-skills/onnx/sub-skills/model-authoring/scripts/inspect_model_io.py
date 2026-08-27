#!/usr/bin/env python3
"""Inspect ONNX model IO and graph structure without executing the model."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import onnx
from onnx import helper, shape_inference


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect ONNX model inputs, outputs, nodes, and initializers.")
    parser.add_argument("--model", required=True, help="Path to an ONNX model file.")
    parser.add_argument("--format", default=None, help="Optional ONNX serializer format.")
    parser.add_argument("--no-external-data", action="store_true", help="Inspect without loading external tensor bytes.")
    parser.add_argument("--infer-shapes", action="store_true", help="Run non-strict shape inference before reporting value_info.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    return parser.parse_args()


def value_info_record(value: onnx.ValueInfoProto) -> dict[str, Any]:
    return {"name": value.name, "type": helper.printable_type(value.type)}


def main() -> int:
    args = parse_args()
    model_path = Path(args.model)
    model = onnx.load_model(
        os.fspath(model_path),
        format=args.format,
        load_external_data=not args.no_external_data,
    )
    onnx.checker.check_model(model)
    if args.infer_shapes:
        model = shape_inference.infer_shapes(model)
    graph = model.graph
    result: dict[str, Any] = {
        "ir_version": model.ir_version,
        "opset_imports": {entry.domain or "": entry.version for entry in model.opset_import},
        "graph_name": graph.name,
        "inputs": [value_info_record(value) for value in graph.input],
        "outputs": [value_info_record(value) for value in graph.output],
        "value_info": [value_info_record(value) for value in graph.value_info],
        "initializers": [{"name": tensor.name, "dtype": tensor.data_type, "dims": list(tensor.dims)} for tensor in graph.initializer],
        "nodes": [{"name": node.name, "op_type": node.op_type, "domain": node.domain, "inputs": list(node.input), "outputs": list(node.output)} for node in graph.node],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    print(f"graph={result['graph_name']} ir_version={result['ir_version']} opsets={result['opset_imports']}")
    for key in ("inputs", "outputs", "value_info", "initializers", "nodes"):
        print(f"{key}:")
        for item in result[key]:
            print(f"  {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
