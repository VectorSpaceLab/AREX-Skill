#!/usr/bin/env python3
"""Convert a tiny local Keras fixture and validate a TFLite artifact.

The helper is intentionally independent of DeepDanbooru. It uses an already
installed CPU TensorFlow, creates no network traffic, and never downloads a
model or dataset. The fixture is small enough for routine CI or preflight use.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a deterministic tiny CPU TensorFlow Lite conversion smoke test."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for the temporary Keras fixture and TFLite artifact.",
    )
    parser.add_argument(
        "--keep-fixture",
        action="store_true",
        help="Keep the temporary Keras fixture after a successful conversion.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    # Make the CPU-first choice explicit before TensorFlow initializes devices.
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    try:
        import numpy as np
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - depends on the host runtime
        print(f"TensorFlow import failed: {exc}", file=sys.stderr)
        return 2

    np.random.seed(1234)
    tf.random.set_seed(1234)
    try:
        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.config.threading.set_intra_op_parallelism_threads(1)
    except RuntimeError:
        # A caller may have initialized TensorFlow before this script. The
        # conversion remains safe; only the optional thread tuning is skipped.
        pass

    output_dir = args.output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = output_dir / "tiny_fixture.keras"
    tflite_path = output_dir / "tiny_fixture.tflite"

    model = tf.keras.Sequential(
        [
            tf.keras.Input(shape=(4,), name="features"),
            tf.keras.layers.Dense(
                3,
                activation="relu",
                kernel_initializer=tf.keras.initializers.Constant(0.125),
                bias_initializer=tf.keras.initializers.Constant(0.0),
            ),
            tf.keras.layers.Dense(
                2,
                activation="sigmoid",
                kernel_initializer=tf.keras.initializers.Constant(0.25),
                bias_initializer=tf.keras.initializers.Constant(0.0),
            ),
        ],
        name="tiny_post_training_fixture",
    )
    # Save and reload so the smoke covers the saved-Keras boundary as well.
    model.save(fixture_path)
    loaded = tf.keras.models.load_model(fixture_path)

    converter = tf.lite.TFLiteConverter.from_keras_model(loaded)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    try:
        converted = converter.convert()
    except Exception as exc:
        print(f"TFLite conversion failed: {exc}", file=sys.stderr)
        return 3

    if not converted:
        print("TFLite conversion returned empty bytes", file=sys.stderr)
        return 4
    tflite_path.write_bytes(converted)
    if not tflite_path.is_file() or tflite_path.stat().st_size == 0:
        print("TFLite artifact is missing or empty", file=sys.stderr)
        return 5

    try:
        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()
        inputs = interpreter.get_input_details()
        outputs = interpreter.get_output_details()
        if not inputs or not outputs:
            raise RuntimeError("interpreter exposed no input or output tensors")
        input_index = inputs[0]["index"]
        input_shape = tuple(int(value) for value in inputs[0]["shape"])
        sample = np.zeros(input_shape, dtype=inputs[0]["dtype"])
        interpreter.set_tensor(input_index, sample)
        interpreter.invoke()
        result = interpreter.get_tensor(outputs[0]["index"])
    except Exception as exc:
        print(f"TFLite interpreter validation failed: {exc}", file=sys.stderr)
        return 6

    print(f"Smoke OK: {tflite_path} ({tflite_path.stat().st_size} bytes)")
    print(f"Input shape/dtype: {input_shape}/{inputs[0]['dtype']}")
    print(f"Output shape: {tuple(int(v) for v in result.shape)}")
    if not args.keep_fixture:
        try:
            fixture_path.unlink()
        except FileNotFoundError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
