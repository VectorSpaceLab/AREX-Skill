#!/usr/bin/env python3
"""No-download smoke check for ART TensorFlowV2Classifier and KerasClassifier."""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np


def run_smoke(skip_fit: bool = False, keras_only: bool = False, verbose: bool = False) -> None:
    # Keep backend logs quiet for a tiny smoke command; users can override externally.
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    import tensorflow as tf

    from art.estimators.classification import KerasClassifier, TensorFlowV2Classifier
    from art.utils import to_categorical

    tf.random.set_seed(23)
    np.random.seed(23)

    x = np.array(
        [
            [0.00, 0.10, 0.20, 0.30],
            [0.20, 0.30, 0.40, 0.50],
            [0.50, 0.40, 0.30, 0.20],
            [0.90, 0.80, 0.10, 0.00],
            [0.05, 0.25, 0.75, 0.95],
            [0.60, 0.10, 0.50, 0.40],
        ],
        dtype=np.float32,
    )
    y_index = np.array([0, 1, 2, 2, 1, 0], dtype=np.int64)
    y_one_hot = to_categorical(y_index, nb_classes=3).astype(np.float32)

    def make_model() -> tf.keras.Model:
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(4,)),
                tf.keras.layers.Dense(6, activation="relu"),
                tf.keras.layers.Dense(3),
            ]
        )
        # Force model variables to exist for all supported Keras variants.
        _ = model(x[:1], training=False)
        return model

    if not keras_only:
        tfv2_model = make_model()
        tfv2_classifier = TensorFlowV2Classifier(
            model=tfv2_model,
            nb_classes=3,
            input_shape=(4,),
            loss_object=tf.keras.losses.CategoricalCrossentropy(from_logits=True),
            optimizer=tf.keras.optimizers.SGD(learning_rate=0.05),
            clip_values=(0.0, 1.0),
        )
        if not skip_fit:
            tfv2_classifier.fit(x, y_one_hot, batch_size=3, nb_epochs=1, verbose=False)
        tfv2_pred = tfv2_classifier.predict(x[:2])
        assert tfv2_pred.shape == (2, 3), tfv2_pred.shape
        assert np.isfinite(tfv2_pred).all()
        tfv2_grad = tfv2_classifier.loss_gradient(x[:2], y_one_hot[:2])
        assert tfv2_grad.shape == x[:2].shape, tfv2_grad.shape
        assert np.isfinite(tfv2_grad).all()
        if verbose:
            print("TensorFlowV2 prediction shape:", tfv2_pred.shape)
            print("TensorFlowV2 loss_gradient shape:", tfv2_grad.shape)

    keras_model = make_model()
    keras_model.compile(
        optimizer=tf.keras.optimizers.SGD(learning_rate=0.05),
        loss=tf.keras.losses.CategoricalCrossentropy(from_logits=True),
    )
    keras_classifier = KerasClassifier(
        model=keras_model,
        use_logits=True,
        clip_values=(0.0, 1.0),
    )
    keras_pred = keras_classifier.predict(x[:2])
    assert keras_pred.shape == (2, 3), keras_pred.shape
    assert np.isfinite(keras_pred).all()
    if verbose:
        print("Keras prediction shape:", keras_pred.shape)

    print("OK: TensorFlowV2/Keras classifier wrappers produced finite tiny-batch outputs")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fit", action="store_true", help="Skip the one-epoch TensorFlowV2 tiny fit.")
    parser.add_argument("--keras-only", action="store_true", help="Only run the KerasClassifier half of the smoke.")
    parser.add_argument("--verbose", action="store_true", help="Print prediction and gradient shapes in addition to the OK line.")
    args = parser.parse_args(argv)
    run_smoke(skip_fit=args.skip_fit, keras_only=args.keras_only, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - command-line diagnostics
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
