#!/usr/bin/env python3
"""Run evaluate_image with a tiny deterministic Keras model and PNG fixture."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

# The repository's required verified backend is CPU.
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


def build_model(tf):
    inputs = tf.keras.Input(shape=(8, 8, 3), name="image")
    flattened = tf.keras.layers.Flatten()(inputs)
    outputs = tf.keras.layers.Dense(
        2,
        activation="sigmoid",
        kernel_initializer="zeros",
        bias_initializer=tf.keras.initializers.Constant([2.0, -2.0]),
        name="tags",
    )(flattened)
    return tf.keras.Model(inputs=inputs, outputs=outputs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    import numpy as np
    import tensorflow as tf

    from deepdanbooru.commands.evaluate import evaluate_image

    model = build_model(tf)
    tags = ["selected_tag", "rejected_tag"]
    fixture = np.full((8, 8, 3), 127, dtype=np.uint8)

    with tempfile.TemporaryDirectory(prefix="deepdanbooru-evaluate-") as temp_dir:
        image_path = Path(temp_dir) / "fixture.png"
        tf.io.write_file(str(image_path), tf.io.encode_png(fixture))
        result = list(evaluate_image(str(image_path), model, tags, threshold=0.5))

    assert [tag for tag, _ in result] == ["selected_tag"], result
    expected = 1.0 / (1.0 + np.exp(-2.0))
    assert np.isclose(float(result[0][1]), expected, atol=1e-6), result
    print(
        "evaluate_image smoke passed: "
        f"selected_tag={float(result[0][1]):.3f}, rejected_tag below 0.5"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
