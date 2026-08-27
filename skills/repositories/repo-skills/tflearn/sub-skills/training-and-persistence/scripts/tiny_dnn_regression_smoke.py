#!/usr/bin/env python
"""Tiny no-network TFLearn DNN regression smoke.

Builds a one-input linear regression model on built-in arrays, trains for a
small number of epochs, predicts, and optionally saves/restores a checkpoint in
a temp or user-provided directory. This script intentionally avoids writing to
the current repository by default.
"""
from __future__ import absolute_import, division, print_function

import argparse
import os
import shutil
import sys
import tempfile


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Train a tiny built-in TFLearn DNN regression model, run predict, "
            "and optionally save/load a TensorFlow checkpoint stem."
        )
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs for the tiny regression smoke (default: 5).",
    )
    parser.add_argument(
        "--model-dir",
        default=None,
        help=(
            "Directory for checkpoint files. Defaults to a temporary directory "
            "outside the current repository; user-provided directories are kept."
        ),
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Train and predict only; skip save/load checkpoint verification.",
    )
    args = parser.parse_args(argv)
    if args.epochs < 1:
        parser.error("--epochs must be >= 1")
    return args


def import_runtime():
    try:
        import numpy as np
        import tensorflow.compat.v1 as tf

        # Safe in TensorFlow 1.x and useful if the environment exposes compat.v1
        # from a TensorFlow 2.x install. TFLearn itself still requires TF1-era
        # internals, so this does not make modern TF2 runtimes supported.
        try:
            tf.disable_v2_behavior()
        except Exception:
            pass

        import tflearn
    except Exception as exc:  # pragma: no cover - environment diagnostic path.
        print("ERROR: failed to import the TFLearn/TensorFlow runtime: %s" % exc,
              file=sys.stderr)
        print("Use a TensorFlow 1.15.x-compatible environment with TFLearn 0.5.0.",
              file=sys.stderr)
        return None
    return np, tf, tflearn


def build_model(tf, tflearn):
    input_ = tflearn.input_data(shape=[None], name="input")
    linear = tflearn.single_unit(input_)
    regression = tflearn.regression(
        linear,
        optimizer="sgd",
        loss="mean_square",
        metric="R2",
        learning_rate=0.01,
        name="target",
    )
    return tflearn.DNN(regression, tensorboard_verbose=0)


def main(argv=None):
    args = parse_args(argv)
    runtime = import_runtime()
    if runtime is None:
        return 2
    np, tf, tflearn = runtime

    temp_dir = None
    if args.model_dir:
        model_dir = os.path.abspath(args.model_dir)
        os.makedirs(model_dir, exist_ok=True)
        keep_dir = True
    else:
        temp_dir = tempfile.mkdtemp(prefix="tflearn-tiny-dnn-")
        model_dir = temp_dir
        keep_dir = False

    checkpoint_stem = os.path.join(model_dir, "tiny_dnn_regression.tflearn")

    X = np.asarray(
        [3.3, 4.4, 5.5, 6.71, 6.93, 4.168, 9.779, 6.182,
         7.59, 2.167, 7.042, 10.791, 5.313, 7.997, 5.654,
         9.27, 3.1],
        dtype=np.float32,
    )
    Y = np.asarray(
        [1.7, 2.76, 2.09, 3.19, 1.694, 1.573, 3.366, 2.596,
         2.53, 1.221, 2.827, 3.465, 1.65, 2.904, 2.42, 2.94,
         1.3],
        dtype=np.float32,
    )

    try:
        with tf.Graph().as_default():
            np.random.seed(7)
            tf.set_random_seed(7)
            model = build_model(tf, tflearn)
            model.fit(
                {"input": X},
                {"target": Y},
                n_epoch=args.epochs,
                show_metric=False,
                snapshot_epoch=False,
                run_id="tiny_dnn_regression_smoke",
            )
            prediction = model.predict([3.2, 3.3, 3.4])
            print("prediction shape: %s" % (tuple(prediction.shape),))
            print("prediction sample: %s" % prediction.tolist())

            if not args.no_save:
                model.save(checkpoint_stem)
                print("checkpoint stem: %s" % checkpoint_stem)
                print("checkpoint index exists: %s" % os.path.exists(checkpoint_stem + ".index"))
            else:
                print("checkpoint stem: <not saved>")

        if not args.no_save:
            with tf.Graph().as_default():
                restored = build_model(tf, tflearn)
                restored.load(checkpoint_stem)
                restored_prediction = restored.predict([3.2, 3.3])
                print("restored prediction shape: %s" % (tuple(restored_prediction.shape),))
                print("restored prediction sample: %s" % restored_prediction.tolist())

        if temp_dir and not keep_dir:
            print("temporary model dir: %s" % temp_dir)
            print("temporary model dir cleanup: yes")
    finally:
        if temp_dir and not keep_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
