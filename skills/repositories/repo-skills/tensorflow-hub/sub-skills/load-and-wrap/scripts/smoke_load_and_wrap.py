#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""No-download smoke test for TensorFlow Hub load/wrap workflows.

The script creates tiny local SavedModels in temporary directories and verifies
that the current Python environment can use:

- tensorflow_hub.resolve()
- tensorflow_hub.load()
- tensorflow_hub.KerasLayer()
- optionally tensorflow_hub.feature_column_v2.text_embedding_column_v2()

It never downloads remote handles and never reads the original source checkout.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from typing import Optional, Sequence


def _import_runtime():
    """Imports TensorFlow Hub runtime dependencies with clear diagnostics."""
    try:
        import tensorflow as tf  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise RuntimeError(
            "TensorFlow is required before tensorflow_hub can be imported. "
            "Install a TensorFlow package compatible with this Python."
        ) from exc

    try:
        import tensorflow_hub as hub  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise RuntimeError(
            "tensorflow_hub import failed. If TensorFlow uses Keras 3, ensure "
            "a matching tf_keras package is installed; if the error names "
            "pkg_resources, use a setuptools version that still provides it."
        ) from exc

    return tf, hub


def _assert_close(actual, expected, label: str) -> None:
    if len(actual) != len(expected):
        raise AssertionError(f"{label}: length mismatch {actual!r} != {expected!r}")
    for got, want in zip(actual, expected):
        if abs(float(got) - float(want)) > 1e-5:
            raise AssertionError(f"{label}: {actual!r} != {expected!r}")


def run_load_and_keras_smoke(quiet: bool = False) -> None:
    """Creates a tiny callable SavedModel and verifies Hub load/wrap APIs."""
    tf, hub = _import_runtime()

    class ToyModule(tf.Module):
        @tf.function(input_signature=[tf.TensorSpec(shape=[None], dtype=tf.float32)])
        def __call__(self, values):
            return values + 1.0

    export_dir = tempfile.mkdtemp(prefix="tfhub-load-smoke-")
    tf.saved_model.save(ToyModule(), export_dir)

    resolved = hub.resolve(export_dir)
    if resolved != export_dir:
        raise AssertionError(f"hub.resolve returned {resolved!r}, expected {export_dir!r}")

    values = tf.constant([1.0, 2.0], dtype=tf.float32)
    loaded = hub.load(export_dir)
    _assert_close(loaded(values).numpy().tolist(), [2.0, 3.0], "hub.load")

    layer = hub.KerasLayer(export_dir)
    _assert_close(layer(values).numpy().tolist(), [2.0, 3.0], "KerasLayer")

    if not quiet:
        print("load/wrap smoke: ok")
        print(f"resolved_local_path={resolved!r}")
        print("hub.load([1.0, 2.0]) -> [2.0, 3.0]")
        print("hub.KerasLayer([1.0, 2.0]) -> [2.0, 3.0]")


def _import_keras_for_feature_columns(tf):
    """Returns a Keras 2-compatible namespace for DenseFeatures."""
    try:
        import tf_keras as keras  # pylint: disable=import-outside-toplevel

        return keras
    except ImportError:
        keras = getattr(tf, "keras", None)
        if keras is None:
            raise RuntimeError("No Keras namespace is available for DenseFeatures.")
        return keras


def run_feature_column_smoke(quiet: bool = False) -> None:
    """Verifies the feature-column helper through its direct submodule path."""
    tf, _ = _import_runtime()
    try:
        import tensorflow_hub.feature_column_v2 as hub_feature_column_v2  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise RuntimeError(
            "Could not import tensorflow_hub.feature_column_v2. The feature "
            "column helper is not a top-level tensorflow_hub attribute; use "
            "the direct submodule import path."
        ) from exc

    keras = _import_keras_for_feature_columns(tf)
    if not hasattr(keras.layers, "DenseFeatures"):
        raise RuntimeError(
            "The selected Keras namespace does not expose DenseFeatures. In a "
            "Keras 3 environment, install and import matching tf_keras."
        )

    class TextLengthEmbedding(tf.Module):
        @tf.function(input_signature=[tf.TensorSpec(shape=[None], dtype=tf.string)])
        def __call__(self, text):
            lengths = tf.cast(tf.strings.length(text), tf.float32)
            return tf.expand_dims(lengths, -1)

    export_dir = tempfile.mkdtemp(prefix="tfhub-feature-column-smoke-")
    tf.saved_model.save(TextLengthEmbedding(), export_dir)

    column = hub_feature_column_v2.text_embedding_column_v2(
        "text", export_dir, trainable=False
    )
    dense_features = keras.layers.DenseFeatures([column])
    result = dense_features({"text": tf.constant(["hi", "hello"])}).numpy().tolist()
    if result != [[2.0], [5.0]]:
        raise AssertionError(f"feature-column smoke produced {result!r}")

    if not quiet:
        print("feature-column smoke: ok")
        print("text lengths ['hi', 'hello'] -> [[2.0], [5.0]]")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run no-download TensorFlow Hub load/KerasLayer smoke checks."
    )
    parser.add_argument(
        "--feature-column",
        action="store_true",
        help=(
            "Also verify tensorflow_hub.feature_column_v2.text_embedding_column_v2 "
            "with a tiny local SavedModel."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors; suppress success details.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    try:
        run_load_and_keras_smoke(quiet=args.quiet)
        if args.feature_column:
            run_feature_column_smoke(quiet=args.quiet)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
