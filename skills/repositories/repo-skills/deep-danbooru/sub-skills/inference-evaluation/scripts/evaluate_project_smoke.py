#!/usr/bin/env python3
"""Check project-backed folder evaluation through the supported evaluate API."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import tempfile
from pathlib import Path

# Keep the generated check on the required, verified CPU backend.
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
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer="sgd", loss="binary_crossentropy")
    return model


def write_png(tf, np, path: Path, value: int) -> None:
    pixels = np.full((8, 8, 3), value, dtype=np.uint8)
    tf.io.write_file(str(path), tf.io.encode_png(pixels))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    import numpy as np
    import tensorflow as tf

    from deepdanbooru.commands.evaluate import evaluate

    # The native evaluate-project command in the covered 1.0.0 package calls
    # the missing dd.data.load_tags_from_project symbol. Exercise the documented
    # evaluate --project-path --allow-folder fallback instead; this smoke must
    # not claim that the defective native command ran successfully.

    with tempfile.TemporaryDirectory(prefix="deepdanbooru-project-") as temp_dir:
        root = Path(temp_dir)
        project_path = root / "project"
        target_path = root / "targets" / "nested"
        project_path.mkdir()
        target_path.mkdir(parents=True)

        (project_path / "project.json").write_text(
            json.dumps({"model": "smoke", "image_width": 8, "image_height": 8}),
            encoding="utf-8",
        )
        (project_path / "tags.txt").write_text(
            "selected_tag\nrejected_tag\n", encoding="utf-8"
        )
        build_model(tf).save(project_path / "model-smoke.keras")

        image10 = target_path / "image10.png"
        image2 = target_path / "image2.png"
        write_png(tf, np, image10, 64)
        write_png(tf, np, image2, 192)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            evaluate(
                (str(root / "targets"),),
                str(project_path),
                None,
                None,
                0.5,
                False,
                False,
                True,
                False,
                "*.[Pp][Nn][Gg],*.[Jj][Pp][Gg],*.[Jj][Pp][Ee][Gg],*.[Gg][Ii][Ff]",
                False,
            )
        output = stdout.getvalue()

        heading2 = f"Tags of {image2}:"
        heading10 = f"Tags of {image10}:"
        assert heading2 in output and heading10 in output, output
        assert output.index(heading2) < output.index(heading10), output
        assert output.count("selected_tag") == 2, output
        assert "rejected_tag" not in output, output

    print(
        "project evaluation smoke passed through the supported evaluate "
        "project-path/folder fallback; native evaluate-project remains "
        "unverified because of the 1.0.0 tag-loader defect"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
