#!/usr/bin/env python3
"""Create and validate a deterministic tiny ONNX Add model.

The script writes only the explicitly requested output path and performs no
network access. It is useful for checker, serialization, external-data, and
reference-evaluator smoke tests.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a tiny checked ONNX Add model.")
    parser.add_argument("--output", required=True, help="Output model path.")
    parser.add_argument(
        "--format",
        choices=["protobuf", "textproto", "json", "onnxtxt"],
        default=None,
        help="Serializer format; defaults to the output extension or protobuf.",
    )
    parser.add_argument(
        "--external-data",
        action="store_true",
        help="Write the initializer as external data when the selected serializer supports it.",
    )
    parser.add_argument(
        "--location",
        default="tiny_add.weights",
        help="Relative external-data filename when --external-data is used.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output file.")
    return parser.parse_args()


def build_model() -> onnx.ModelProto:
    x = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2])
    y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [2])
    bias = numpy_helper.from_array(np.array([1.0, 2.0], dtype=np.float32), name="B")
    node = helper.make_node("Add", ["X", "B"], ["Y"])
    graph = helper.make_graph([node], "tiny-add", [x], [y], initializer=[bias])
    return helper.make_model(
        graph,
        producer_name="disco-onnx-skill",
        opset_imports=[helper.make_opsetid("", 14)],
    )


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite existing output: {output}; pass --overwrite to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    model = build_model()
    onnx.checker.check_model(model)
    text_like_suffixes = {".json", ".onnxjson", ".txtpb", ".textproto", ".prototxt", ".pbtxt", ".onnxtxt", ".onnxtext"}
    inferred_text_like = args.format is None and output.suffix.lower() in text_like_suffixes
    use_external = args.external_data and args.format not in {"json", "textproto", "onnxtxt"} and not inferred_text_like
    onnx.save_model(
        model,
        os.fspath(output),
        format=args.format,
        save_as_external_data=use_external,
        all_tensors_to_one_file=True,
        location=args.location if use_external else None,
        size_threshold=0 if use_external else 1024,
    )
    loaded = onnx.load_model(os.fspath(output), format=args.format)
    onnx.checker.check_model(loaded)
    print(f"wrote checked ONNX model: {output} format={args.format or 'inferred/protobuf'} external_data={use_external}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
