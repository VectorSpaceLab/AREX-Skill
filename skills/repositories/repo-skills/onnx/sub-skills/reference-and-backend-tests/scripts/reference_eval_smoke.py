#!/usr/bin/env python3
"""Run a tiny ONNX ReferenceEvaluator smoke test.

This helper is safe, deterministic, and uses only a tiny in-memory Add model.
It is suitable for verifying that the installed ONNX package can execute a
simple graph without requiring the original repository checkout.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import onnx
from onnx import TensorProto, checker, helper, shape_inference


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny ReferenceEvaluator smoke test.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of text.")
    return parser.parse_args()


def build_model() -> onnx.ModelProto:
    x = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2])
    y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [2])
    z = helper.make_tensor_value_info("Z", TensorProto.FLOAT, [2])
    node = helper.make_node("Add", ["X", "Y"], ["Z"])
    graph = helper.make_graph([node], "tiny-add", [x, y], [z])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 14)])
    checker.check_model(model)
    return shape_inference.infer_shapes(model)


def main() -> int:
    args = parse_args()
    from onnx.reference import ReferenceEvaluator

    model = build_model()
    sess = ReferenceEvaluator(model)
    out = sess.run(
        None,
        {
            "X": np.array([1, 2], dtype=np.float32),
            "Y": np.array([3, 4], dtype=np.float32),
        },
    )[0]
    summary = {"output": out.tolist(), "onnx_version": onnx.__version__}
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"ReferenceEvaluator ok: output={summary['output']} onnx={summary['onnx_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
