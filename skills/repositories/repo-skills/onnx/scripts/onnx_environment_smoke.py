#!/usr/bin/env python3
"""Safe ONNX environment smoke test.

This script uses only the installed `onnx` package and temporary in-memory data.
It does not require the ONNX source checkout, network access, credentials, or GPU
hardware.

Example:
    python scripts/onnx_environment_smoke.py
    python scripts/onnx_environment_smoke.py --skip-reference
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny ONNX import/API smoke test.")
    parser.add_argument(
        "--skip-reference",
        action="store_true",
        help="Skip ReferenceEvaluator execution and only check model construction/validation/shape inference.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of a short text summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        import numpy as np
        import onnx
        from onnx import TensorProto, checker, helper, shape_inference
    except Exception as exc:  # noqa: BLE001
        print(f"ONNX import smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    summary: dict[str, object] = {
        "python": sys.version.split()[0],
        "onnx_version": getattr(onnx, "__version__", "unknown"),
        "onnx_distribution": None,
        "ir_version": getattr(onnx, "IR_VERSION", None),
        "default_opset": onnx.defs.onnx_opset_version(),
        "onnx_ml_opset": onnx.defs.onnx_ml_opset_version(),
        "checks": [],
    }
    try:
        summary["onnx_distribution"] = metadata.version("onnx")
    except metadata.PackageNotFoundError:
        summary["onnx_distribution"] = "metadata-not-found"

    x = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2])
    y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [2])
    z = helper.make_tensor_value_info("Z", TensorProto.FLOAT, [2])
    node = helper.make_node("Add", ["X", "Y"], ["Z"])
    graph = helper.make_graph([node], "tiny-add", [x, y], [z])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 14)])
    checker.check_model(model)
    summary["checks"].append("checker.check_model")

    inferred = shape_inference.infer_shapes(model)
    checker.check_model(inferred)
    summary["checks"].append("shape_inference.infer_shapes")

    serialized = inferred.SerializeToString()
    round_trip = onnx.load_from_string(serialized)
    checker.check_model(round_trip)
    summary["checks"].append("serialize/load_from_string")

    if not args.skip_reference:
        try:
            from onnx.reference import ReferenceEvaluator

            sess = ReferenceEvaluator(round_trip)
            out = sess.run(
                None,
                {
                    "X": np.array([1, 2], dtype=np.float32),
                    "Y": np.array([3, 4], dtype=np.float32),
                },
            )[0]
            if out.tolist() != [4.0, 6.0]:
                raise AssertionError(f"unexpected ReferenceEvaluator output: {out!r}")
            summary["checks"].append("ReferenceEvaluator")
            summary["reference_output"] = out.tolist()
        except Exception as exc:  # noqa: BLE001
            print(
                "ReferenceEvaluator smoke failed. If the task only needs model validation, rerun with --skip-reference. "
                f"Error: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return 1

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "ONNX smoke ok: "
            f"onnx={summary['onnx_version']} ir={summary['ir_version']} "
            f"opset={summary['default_opset']} checks={', '.join(summary['checks'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
