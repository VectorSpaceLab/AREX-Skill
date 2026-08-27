#!/usr/bin/env python3
"""Tiny synthetic Segmentation Models training smoke.

This script intentionally uses no external dataset, no network access, and
`encoder_weights=None`. It checks that a small Unet can be constructed,
compiled, trained for a tiny synthetic batch, evaluated, and optionally used for
prediction under the selected Keras framework.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-network Segmentation Models smoke test with synthetic "
            "arrays and encoder_weights=None."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("binary", "multiclass", "non-rgb"),
        default="binary",
        help=(
            "binary: one foreground sigmoid channel; multiclass: two foreground "
            "classes plus background with softmax; non-rgb: four-channel input "
            "trained from scratch."
        ),
    )
    parser.add_argument(
        "--framework",
        choices=("tf.keras", "keras"),
        default="tf.keras",
        help="Segmentation Models framework to select before import.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
        help="Number of tiny epochs to run. Use 0 to skip fit and only compile/evaluate.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Synthetic batch size. Default keeps the smoke lightweight.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=32,
        help="Synthetic image height. Use a multiple of 32 for this Unet smoke.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=32,
        help="Synthetic image width. Use a multiple of 32 for this Unet smoke.",
    )
    parser.add_argument(
        "--run-predict",
        action="store_true",
        help="Also run model.predict on one synthetic sample and print the shape.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.epochs < 0:
        raise SystemExit("--epochs must be >= 0")
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be >= 1")
    if args.height < 32 or args.width < 32:
        raise SystemExit("--height and --width must be at least 32 for this smoke")
    if args.height % 32 != 0 or args.width % 32 != 0:
        raise SystemExit("--height and --width must be multiples of 32 for this Unet smoke")


def import_framework(framework: str):
    os.environ["SM_FRAMEWORK"] = framework

    # Keep TensorFlow output concise when tf.keras is selected.
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    import segmentation_models as sm  # pylint: disable=import-error,import-outside-toplevel

    if framework == "tf.keras":
        from tensorflow import keras  # pylint: disable=import-error,import-outside-toplevel
    else:
        import keras  # pylint: disable=import-error,import-outside-toplevel

    return sm, keras


def make_synthetic_data(
    mode: str,
    batch_size: int,
    height: int,
    width: int,
) -> Tuple["np.ndarray", "np.ndarray", int, int, str]:
    import numpy as np  # pylint: disable=import-outside-toplevel

    rng = np.random.default_rng(123)

    if mode == "non-rgb":
        channels = 4
        classes = 1
        activation = "sigmoid"
    elif mode == "multiclass":
        channels = 3
        classes = 3  # two foreground classes plus background
        activation = "softmax"
    else:
        channels = 3
        classes = 1
        activation = "sigmoid"

    x = rng.normal(size=(batch_size, height, width, channels)).astype("float32")

    if classes == 1:
        y = (rng.random(size=(batch_size, height, width, 1)) > 0.5).astype("float32")
    else:
        labels = rng.integers(0, classes, size=(batch_size, height, width))
        y = np.eye(classes, dtype="float32")[labels]

    return x, y, channels, classes, activation


def build_model(sm, input_shape, classes: int, activation: str):
    # Keep decoder filters intentionally tiny so the script remains a plumbing
    # smoke rather than a real training job.
    return sm.Unet(
        "resnet18",
        input_shape=input_shape,
        classes=classes,
        activation=activation,
        encoder_weights=None,
        decoder_filters=(8, 4, 2, 1, 1),
    )


def compile_model(sm, keras, model, classes: int) -> None:
    if classes == 1:
        loss = sm.losses.bce_jaccard_loss
        metrics = [sm.metrics.IOUScore(threshold=0.5)]
    else:
        loss = sm.losses.cce_jaccard_loss
        metrics = [sm.metrics.IOUScore(threshold=None)]

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss=loss,
        metrics=metrics,
    )


def main() -> int:
    args = parse_args()
    validate_args(args)

    sm, keras = import_framework(args.framework)
    x, y, channels, classes, activation = make_synthetic_data(
        args.mode,
        args.batch_size,
        args.height,
        args.width,
    )

    model = build_model(
        sm,
        input_shape=(args.height, args.width, channels),
        classes=classes,
        activation=activation,
    )
    compile_model(sm, keras, model, classes)

    if args.epochs:
        history = model.fit(
            x,
            y,
            epochs=args.epochs,
            batch_size=args.batch_size,
            verbose=0,
        )
        last_loss = float(history.history["loss"][-1])
    else:
        last_loss = float("nan")

    eval_values = model.evaluate(x, y, batch_size=args.batch_size, verbose=0)
    if not isinstance(eval_values, (list, tuple)):
        eval_values = [eval_values]

    print(f"framework={sm.framework()} mode={args.mode}")
    print(f"x_shape={tuple(x.shape)} y_shape={tuple(y.shape)} output_shape={model.output_shape}")
    if args.epochs:
        print(f"fit_loss={last_loss:.6f}")
    print("evaluate=" + ",".join(f"{float(v):.6f}" for v in eval_values))

    if args.run_predict:
        pred = model.predict(x[:1], verbose=0)
        print(f"predict_shape={tuple(pred.shape)}")

    keras.backend.clear_session()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
