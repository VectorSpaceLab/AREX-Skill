#!/usr/bin/env python3
"""Smoke-test onnxsim FunctionProto rewrite rules without a source checkout.

Builds a deterministic MatMul+Add model, defines a pure-data FunctionProto rule
MatMul+Add -> Gemm, skips onnxsim's built-in Gemm fusion, and asserts the Gemm
appears in the simplified model. Requires only installed onnx/onnxsim runtime
dependencies.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import onnxsim
from onnx import TensorProto, helper, numpy_helper, parser

GEMM_FUSION_PASS = "fuse_matmul_add_bias_into_gemm"


def _value_info(name: str, shape: list[int]) -> onnx.ValueInfoProto:
    return helper.make_tensor_value_info(name, TensorProto.FLOAT, shape)


def build_model(opset: int, ir_version: int) -> onnx.ModelProto:
    """Return x @ W + B with one dynamic-free graph input."""
    weights = (np.arange(20, dtype=np.float32).reshape(4, 5) + 1.0) / 10.0
    bias = np.linspace(-0.2, 0.2, 5, dtype=np.float32)
    nodes = [
        helper.make_node("MatMul", ["x", "W"], ["mm"], name="mm"),
        helper.make_node("Add", ["mm", "B"], ["y"], name="add"),
    ]
    graph = helper.make_graph(
        nodes,
        "matmul_add_smoke",
        [_value_info("x", [3, 4])],
        [_value_info("y", [3, 5])],
        [numpy_helper.from_array(weights, "W"), numpy_helper.from_array(bias, "B")],
    )
    model = helper.make_model(
        graph,
        opset_imports=[helper.make_opsetid("", opset)],
        producer_name="onnxsim-advanced-graph-control-smoke",
        ir_version=ir_version,
    )
    onnx.checker.check_model(model)
    return model


def build_rule(opset: int) -> tuple[onnx.FunctionProto, onnx.FunctionProto]:
    """Return the pure-data MatMul+Add -> Gemm rule."""
    pattern = parser.parse_function(
        f'''
<domain: "com.onnxsim.smoke", opset_import: ["" : {opset}]>
matmul_add_pattern (x, w, b) => (y)
{{
    t = MatMul(x, w)
    y = Add(t, b)
}}
'''
    )
    replacement = parser.parse_function(
        f'''
<domain: "com.onnxsim.smoke", opset_import: ["" : {opset}]>
gemm_replacement (x, w, b) => (y)
{{
    y = Gemm(x, w, b)
}}
'''
    )
    return pattern, replacement


def op_counts(model: onnx.ModelProto) -> dict[str, int]:
    return dict(collections.Counter(node.op_type for node in model.graph.node))


def run(args: argparse.Namespace) -> dict[str, Any]:
    model = build_model(args.opset, args.ir_version)
    pattern, replacement = build_rule(args.opset)

    if args.no_run:
        return {
            "status": "not-run",
            "reason": "--no-run was set",
            "input_op_counts": op_counts(model),
            "rule": "MatMul+Add -> Gemm",
            "skipped_optimizers": [GEMM_FUSION_PASS],
        }

    simplify_stdout = io.StringIO()
    with contextlib.redirect_stdout(simplify_stdout):
        simplified, check_ok = onnxsim.simplify(
            model,
            check_n=args.check_n,
            skipped_optimizers=[GEMM_FUSION_PASS],
            function_rewrite_rules=[(pattern, replacement)],
            input_fill=args.input_fill,
        )
    captured_stdout = simplify_stdout.getvalue()
    if captured_stdout and args.show_simplify_output:
        print(captured_stdout, file=sys.stderr, end="")
    onnx.checker.check_model(simplified)
    counts = op_counts(simplified)

    if counts.get("Gemm", 0) < 1:
        raise AssertionError(f"expected Gemm after FunctionProto rule, got {counts}")
    if counts.get("MatMul", 0) or counts.get("Add", 0):
        raise AssertionError(f"expected MatMul/Add to be gone, got {counts}")
    if args.check_n and not check_ok:
        raise AssertionError("onnxsim correctness check failed")

    output_model = None
    if args.output_model:
        output_path = Path(args.output_model)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        onnx.save(simplified, output_path)
        output_model = str(output_path)

    return {
        "status": "ok",
        "input_op_counts": op_counts(model),
        "output_op_counts": counts,
        "check_n": args.check_n,
        "check_ok": bool(check_ok),
        "skipped_optimizers": [GEMM_FUSION_PASS],
        "output_model": output_model,
        "captured_simplify_stdout": bool(captured_stdout),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build a tiny MatMul+Add ONNX model and prove an onnxsim "
            "FunctionProto rule rewrites it to Gemm."
        )
    )
    p.add_argument("--opset", type=int, default=18, help="ONNX default-domain opset for the model and rule (default: 18).")
    p.add_argument("--ir-version", type=int, default=10, help="ONNX IR version for the generated model (default: 10).")
    p.add_argument("--check-n", type=int, default=1, help="onnxsim correctness-check repetitions (default: 1; use 0 for structural only).")
    p.add_argument(
        "--input-fill",
        choices=["random", "ones", "zeros", "arange"],
        default="ones",
        help="Input fill mode used when --check-n is positive (default: ones).",
    )
    p.add_argument("--output-model", help="Optional path to save the rewritten model.")
    p.add_argument("--show-simplify-output", action="store_true", help="Forward onnxsim's progress output to stderr; JSON summary remains on stdout.")
    p.add_argument("--no-run", action="store_true", help="Only build the model/rule and print the planned smoke test; do not call simplify().")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
