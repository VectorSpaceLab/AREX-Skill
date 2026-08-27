#!/usr/bin/env python3
"""Smoke-test onnxsim ModelInfo, metadata annotation, and graph diff APIs.

Builds deterministic tiny ONNX models in memory, prints static metrics, records
which metadata keys annotate_metadata() writes, and summarizes a MatMul+Add ->
Gemm graph diff. Requires only installed onnx/onnxsim runtime dependencies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper
from onnxsim.model_info import ModelInfo, annotate_metadata, diff_graphs, print_graph_diff


def _value_info(name: str, shape: list[int]) -> onnx.ValueInfoProto:
    return helper.make_tensor_value_info(name, TensorProto.FLOAT, shape)


def _weights() -> tuple[onnx.TensorProto, onnx.TensorProto]:
    weight = (np.arange(20, dtype=np.float32).reshape(4, 5) + 1.0) / 10.0
    bias = np.linspace(-0.2, 0.2, 5, dtype=np.float32)
    return numpy_helper.from_array(weight, "W"), numpy_helper.from_array(bias, "B")


def build_matmul_add_model(opset: int, ir_version: int) -> onnx.ModelProto:
    w, b = _weights()
    nodes = [
        helper.make_node("MatMul", ["x", "W"], ["mm"], name="mm"),
        helper.make_node("Add", ["mm", "B"], ["y"], name="add"),
    ]
    graph = helper.make_graph(
        nodes,
        "matmul_add_metrics",
        [_value_info("x", [3, 4])],
        [_value_info("y", [3, 5])],
        [w, b],
    )
    model = helper.make_model(
        graph,
        opset_imports=[helper.make_opsetid("", opset)],
        producer_name="onnxsim-advanced-graph-control-smoke",
        ir_version=ir_version,
    )
    onnx.checker.check_model(model)
    return model


def build_manual_gemm_model(opset: int, ir_version: int) -> onnx.ModelProto:
    w, b = _weights()
    node = helper.make_node("Gemm", ["x", "W", "B"], ["y"], name="gemm")
    graph = helper.make_graph(
        [node],
        "gemm_metrics",
        [_value_info("x", [3, 4])],
        [_value_info("y", [3, 5])],
        [w, b],
    )
    model = helper.make_model(
        graph,
        opset_imports=[helper.make_opsetid("", opset)],
        producer_name="onnxsim-advanced-graph-control-smoke",
        ir_version=ir_version,
    )
    onnx.checker.check_model(model)
    return model


def metric_value(value: Any) -> str | int | float:
    if isinstance(value, (int, float, str)):
        return value
    return str(value)


def model_info_summary(model: onnx.ModelProto) -> dict[str, Any]:
    info = ModelInfo(model)
    return {
        "op_nums": dict(sorted(info.op_nums.items())),
        "model_size": metric_value(info.model_size),
        "macs": metric_value(info.macs),
        "flops": metric_value(info.flops),
        "mem_access": metric_value(info.mem_access),
        "memory_footprint": metric_value(info.memory_footprint),
        "compute_density": metric_value(info.compute_density),
    }


def metadata_keys(proto: Any) -> list[str]:
    return sorted(entry.key for entry in getattr(proto, "metadata_props", []))


def annotation_summary(model: onnx.ModelProto, prefix: str) -> tuple[onnx.ModelProto, dict[str, Any]]:
    annotated = annotate_metadata(model, prefix=prefix)
    onnx.checker.check_model(annotated)
    first_node = annotated.graph.node[0] if annotated.graph.node else None
    first_input = annotated.graph.input[0] if annotated.graph.input else None
    first_output = annotated.graph.output[0] if annotated.graph.output else None
    first_initializer = annotated.graph.initializer[0] if annotated.graph.initializer else None
    return annotated, {
        "model_keys": metadata_keys(annotated),
        "graph_keys": metadata_keys(annotated.graph),
        "first_node_keys": metadata_keys(first_node) if first_node is not None else [],
        "first_input_keys": metadata_keys(first_input) if first_input is not None else [],
        "first_output_keys": metadata_keys(first_output) if first_output is not None else [],
        "first_initializer_keys": metadata_keys(first_initializer) if first_initializer is not None else [],
        "prefix": prefix,
    }


def node_label(entry: Any) -> str:
    name = entry.name or "/".join(entry.outputs)
    return f"{entry.op_type}:{name}"


def diff_summary(original: onnx.ModelProto, optimized: onnx.ModelProto) -> dict[str, Any]:
    diff = diff_graphs(original, optimized)
    return {
        "removed_nodes": [node_label(n) for n in diff.removed_nodes],
        "added_nodes": [node_label(n) for n in diff.added_nodes],
        "changed_nodes": [
            {
                "outputs": list(after.outputs),
                "before_op": before.op_type,
                "after_op": after.op_type,
                "before_inputs": list(before.inputs),
                "after_inputs": list(after.inputs),
            }
            for before, after in diff.changed_nodes
        ],
        "removed_values": diff.removed_values,
        "added_values": diff.added_values,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    original = build_matmul_add_model(args.opset, args.ir_version)
    fused = build_manual_gemm_model(args.opset, args.ir_version)

    if args.no_run:
        return {
            "status": "not-run",
            "reason": "--no-run was set",
            "models_built": ["MatMul+Add", "Gemm"],
        }

    annotated, annotation = annotation_summary(original, args.metadata_prefix)
    summary = {
        "status": "ok",
        "model_info": model_info_summary(original),
        "annotation_keys": annotation,
        "graph_diff": diff_summary(original, fused),
    }

    if args.output_annotated:
        path = Path(args.output_annotated)
        path.parent.mkdir(parents=True, exist_ok=True)
        onnx.save(annotated, path)
        summary["output_annotated"] = str(path)

    if args.output_fused:
        path = Path(args.output_fused)
        path.parent.mkdir(parents=True, exist_ok=True)
        onnx.save(fused, path)
        summary["output_fused"] = str(path)

    if args.print_graph_diff:
        print_graph_diff(original, fused, limit=args.diff_limit)

    return summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build tiny ONNX models and smoke-test onnxsim ModelInfo, "
            "annotate_metadata, and diff_graphs APIs."
        )
    )
    p.add_argument("--opset", type=int, default=18, help="ONNX default-domain opset for generated models (default: 18).")
    p.add_argument("--ir-version", type=int, default=10, help="ONNX IR version for generated models (default: 10).")
    p.add_argument("--metadata-prefix", default="onnxsim.", help="Metadata key prefix for annotate_metadata() (default: onnxsim.).")
    p.add_argument("--output-annotated", help="Optional path to save the metadata-annotated model.")
    p.add_argument("--output-fused", help="Optional path to save the manual Gemm comparison model.")
    p.add_argument("--print-graph-diff", action="store_true", help="Also print the rich graph diff report before the JSON summary.")
    p.add_argument("--diff-limit", type=int, default=50, help="Entry limit for --print-graph-diff (default: 50).")
    p.add_argument("--no-run", action="store_true", help="Only build/check the tiny models; skip ModelInfo, metadata, and diff APIs.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
