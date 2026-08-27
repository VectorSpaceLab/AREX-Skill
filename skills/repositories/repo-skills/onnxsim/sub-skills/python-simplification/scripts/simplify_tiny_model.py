#!/usr/bin/env python3
"""Create a tiny ONNX model, simplify it with onnxsim, and validate the result.

The helper is deliberately self-contained: it builds a tiny synthetic model in
memory, uses only onnx / onnxsim / numpy, and never downloads anything.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

from onnxsim import backend, simplify
from onnxsim import model_checking

INPUT_NAME = "x"
OUTPUT_NAME = "y"
INPUT_SHAPE = (2, 2)
DEFAULT_OPSET = 13
DEFAULT_IR_VERSION = 10


def build_tiny_model(opset: int = DEFAULT_OPSET) -> onnx.ModelProto:
    """Build a tiny model with one foldable constant and one runtime edge."""

    a = numpy_helper.from_array(np.full(INPUT_SHAPE, 1.0, dtype=np.float32), "a")
    b = numpy_helper.from_array(np.full(INPUT_SHAPE, 2.0, dtype=np.float32), "b")
    const_add = helper.make_node("Add", ["a", "b"], ["sum"])
    identity = helper.make_node("Identity", ["sum"], ["sum_id"])
    runtime_add = helper.make_node("Add", ["sum_id", INPUT_NAME], [OUTPUT_NAME])

    graph = helper.make_graph(
        [const_add, identity, runtime_add],
        "tiny_simplify",
        [helper.make_tensor_value_info(INPUT_NAME, TensorProto.FLOAT, list(INPUT_SHAPE))],
        [helper.make_tensor_value_info(OUTPUT_NAME, TensorProto.FLOAT, list(INPUT_SHAPE))],
        [a, b],
    )
    model = helper.make_model(
        graph,
        opset_imports=[helper.make_opsetid("", opset)],
        ir_version=DEFAULT_IR_VERSION,
    )
    onnx.checker.check_model(model)
    return model


def make_input(fill: str) -> np.ndarray:
    """Create a deterministic validation input with the requested fill mode."""

    if fill == "random":
        rng = np.random.default_rng(0)
        values = rng.random(INPUT_SHAPE)
    elif fill == "ones":
        values = np.ones(INPUT_SHAPE)
    elif fill == "zeros":
        values = np.zeros(INPUT_SHAPE)
    elif fill == "arange":
        values = np.arange(int(np.prod(INPUT_SHAPE, dtype=np.int64))).reshape(INPUT_SHAPE)
    else:  # pragma: no cover - argparse already restricts the choices
        raise ValueError(f"Unknown fill mode: {fill}")
    return np.asarray(values, dtype=np.float32)


def node_types(model: onnx.ModelProto) -> list[str]:
    return [node.op_type for node in model.graph.node]


def validate_round_trip(model: onnx.ModelProto, simplified: onnx.ModelProto, fill: str) -> None:
    """Run both models on a deterministic sample input and compare outputs."""

    sample = make_input(fill)
    inputs = {INPUT_NAME: sample}
    before = backend.run_model(model, inputs)
    after = backend.run_model(simplified, inputs)
    (before_y,) = before.values()
    (after_y,) = after.values()
    np.testing.assert_allclose(after_y, before_y, rtol=1e-5, atol=1e-6)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and simplify a tiny ONNX model as a safe smoke test."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path for the simplified ONNX model.",
    )
    parser.add_argument(
        "--target-opset",
        type=int,
        default=None,
        help="Convert the model to this opset before simplifying.",
    )
    parser.add_argument(
        "--skip-optimization",
        nargs="*",
        default=None,
        metavar="PASS",
        help=(
            "Skip all optimizer passes when given with no values, or skip only "
            "the named passes when pass names are supplied."
        ),
    )
    parser.add_argument(
        "--check-n",
        type=int,
        default=1,
        help="Number of random-input checks to request from onnxsim.",
    )
    parser.add_argument(
        "--input-fill",
        choices=model_checking.INPUT_FILL_CHOICES,
        default="random",
        help="How to fill the validation input tensor.",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print a concise before/after summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Keep all random behavior reproducible.
    np.random.seed(0)

    model = build_tiny_model()

    if args.skip_optimization is None:
        perform_optimization = True
        skipped_optimizers = None
    elif len(args.skip_optimization) == 0:
        perform_optimization = False
        skipped_optimizers = None
    else:
        perform_optimization = True
        skipped_optimizers = list(args.skip_optimization)

    simplified, check_ok = simplify(
        model,
        check_n=args.check_n,
        perform_optimization=perform_optimization,
        skipped_optimizers=skipped_optimizers,
        target_opset_version=args.target_opset,
        input_fill=args.input_fill,
    )

    # Always validate the simplified graph on a deterministic sample input.
    validate_round_trip(model, simplified, args.input_fill)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        onnx.save(simplified, args.output)

    if args.print_summary:
        print("tiny ONNX simplification smoke")
        print(f"  input nodes:  {len(model.graph.node)} -> {node_types(model)}")
        print(f"  output nodes: {len(simplified.graph.node)} -> {node_types(simplified)}")
        print(f"  check_n:      {args.check_n}")
        print(f"  input_fill:   {args.input_fill}")
        print(f"  onnxsim check: {check_ok}")
        print(f"  validated:    yes")
        if args.output is not None:
            print(f"  saved:        {args.output}")
    else:
        message = (
            f"ok: {len(model.graph.node)} nodes -> {len(simplified.graph.node)} nodes; "
            f"validated with input_fill={args.input_fill}"
        )
        if args.output is not None:
            message += f"; saved to {args.output}"
        print(message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
