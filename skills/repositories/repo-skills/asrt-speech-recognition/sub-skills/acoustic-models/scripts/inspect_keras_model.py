#!/usr/bin/env python3
"""Inspect an ASRT Keras acoustic model without loading data or weights."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


MODEL_CLASS_NAMES = {
    "24": "SpeechModel24",
    "25": "SpeechModel25",
    "251": "SpeechModel251",
    "251bn": "SpeechModel251BN",
}


def _parse_shape(value: str) -> tuple[int, int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("shape must have three comma-separated integers, e.g. 1600,200,1")
    try:
        shape = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("shape values must be integers") from exc
    if any(dim <= 0 for dim in shape):
        raise argparse.ArgumentTypeError("shape dimensions must be positive")
    return shape  # type: ignore[return-value]


def _shape_to_json(shape: Any) -> Any:
    if hasattr(shape, "as_list"):
        return shape.as_list()
    if isinstance(shape, tuple):
        return [_shape_to_json(item) for item in shape]
    if isinstance(shape, list):
        return [_shape_to_json(item) for item in shape]
    return shape


def _model_shapes(model: Any) -> dict[str, Any]:
    return {
        "name": getattr(model, "name", None),
        "input_shape": _shape_to_json(getattr(model, "input_shape", None)),
        "output_shape": _shape_to_json(getattr(model, "output_shape", None)),
        "parameter_count": int(model.count_params()) if hasattr(model, "count_params") else None,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Construct an ASRT TensorFlow/Keras acoustic model and print its shapes. "
            "No datasets or trained weights are loaded."
        )
    )
    parser.add_argument("--asrt-root", help="Optional ASRT project root to prepend to PYTHONPATH for imports.")
    parser.add_argument("--model", choices=sorted(MODEL_CLASS_NAMES), default="251bn", help="Acoustic model variant to instantiate.")
    parser.add_argument("--input-shape", type=_parse_shape, default=(1600, 200, 1), help="Input shape as time,bins,channels. Default: 1600,200,1.")
    parser.add_argument("--output-size", type=int, default=1428, help="Output class count. Default: 1428.")
    parser.add_argument("--cpu-only", action="store_true", help="Set CUDA_VISIBLE_DEVICES=-1 before importing TensorFlow.")
    parser.add_argument("--cuda-visible-devices", help="Set CUDA_VISIBLE_DEVICES before importing TensorFlow, e.g. 0.")
    parser.add_argument("--summary-base", action="store_true", help="Also print the base/inference Keras model summary.")
    parser.add_argument("--summary-train", action="store_true", help="Also print the CTC training Keras model summary.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only for the inspection report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.output_size <= 0:
        parser.error("--output-size must be positive")
    if args.cpu_only and args.cuda_visible_devices is not None:
        parser.error("choose either --cpu-only or --cuda-visible-devices, not both")

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    if args.cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    elif args.cuda_visible_devices is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices

    if args.asrt_root:
        sys.path.insert(0, os.path.abspath(args.asrt_root))

    try:
        import tensorflow as tf  # noqa: WPS433 - imported after device env setup
        from model_zoo.speech_model import keras_backend  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"ASRT Keras imports failed: {exc}", file=sys.stderr)
        return 2

    cls = getattr(keras_backend, MODEL_CLASS_NAMES[args.model])
    try:
        acoustic = cls(input_shape=args.input_shape, output_size=args.output_size)
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Model construction failed: {exc}", file=sys.stderr)
        return 3

    train_model, base_model = acoustic.get_model()
    devices = [
        {"type": device.device_type, "name": device.name}
        for device in tf.config.list_physical_devices()
    ]
    report = {
        "selected_variant": args.model,
        "class_name": cls.__name__,
        "model_name": acoustic.get_model_name(),
        "input_shape": list(acoustic.input_shape),
        "output_shape": list(acoustic.output_shape),
        "output_size": args.output_size,
        "tensorflow_version": tf.__version__,
        "physical_devices": devices,
        "base_model": _model_shapes(base_model),
        "training_model": _model_shapes(train_model),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ASRT Keras acoustic model inspection")
        print(json.dumps(report, indent=2, sort_keys=True))

    if args.summary_base:
        print("\nBase/inference model summary:")
        base_model.summary()
    if args.summary_train:
        print("\nCTC training model summary:")
        train_model.summary()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
