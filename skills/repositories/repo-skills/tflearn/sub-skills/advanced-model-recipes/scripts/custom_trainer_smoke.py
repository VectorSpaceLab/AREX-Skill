#!/usr/bin/env python
"""Safe no-network TFLearn custom TensorFlow graph + Trainer smoke.

This script is adapted from the TFLearn custom TensorFlow Trainer pattern, but
uses tiny synthetic arrays instead of downloading MNIST. It validates that a
pure TensorFlow graph can be trained through tflearn.TrainOp and
 tflearn.Trainer.
"""
from __future__ import print_function

import argparse
import os
import sys
import tempfile


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny no-network custom TensorFlow graph through "
            "tflearn.TrainOp and tflearn.Trainer."
        )
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=2,
        help="Number of tiny training epochs to run (default: 2).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size for the 8-sample synthetic fixture (default: 4).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for NumPy and TensorFlow (default: 7).",
    )
    parser.add_argument(
        "--tensorboard-dir",
        default=None,
        help=(
            "Optional TensorBoard log directory. Defaults to a temporary "
            "directory so the smoke does not pollute the working tree."
        ),
    )
    return parser.parse_args(argv)


def import_runtime():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "ImportError: custom_trainer_smoke.py requires NumPy. "
            "Install a TFLearn-compatible runtime before running the smoke. "
            "Original import error: %s" % exc
        )

    try:
        import tensorflow.compat.v1 as tf
        tf.disable_v2_behavior()
    except Exception as exc:
        raise RuntimeError(
            "ImportError: custom_trainer_smoke.py requires TensorFlow with "
            "the compat.v1 graph/session API. The verified stack used "
            "TensorFlow 1.15.x. Original import error: %s" % exc
        )

    try:
        import tflearn
    except Exception as exc:
        raise RuntimeError(
            "ImportError: custom_trainer_smoke.py requires tflearn in a "
            "TensorFlow 1.x-compatible environment. Verified versions were "
            "tflearn 0.5.0, TensorFlow 1.15.x, NumPy 1.18.x, and protobuf "
            "3.20.x. If using modern TensorFlow, TFLearn may fail because "
            "TensorFlow 1.x internals are removed. Original import error: %s" % exc
        )

    return np, tf, tflearn


def make_fixture(np):
    # Linearly separable two-class toy data with duplicated points to exercise
    # batching without relying on downloads or external files.
    train_x = np.asarray(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.1, 0.0],
            [0.0, 0.9],
            [0.9, 0.1],
            [1.0, 0.8],
        ],
        dtype=np.float32,
    )
    # Class 1 when x0 + x1 >= 1, else class 0.
    cls = (train_x.sum(axis=1) >= 1.0).astype("int32")
    train_y = np.zeros((train_x.shape[0], 2), dtype=np.float32)
    train_y[np.arange(train_x.shape[0]), cls] = 1.0
    return train_x, train_y


def run_smoke(args):
    if args.epochs < 1:
        raise ValueError("--epochs must be >= 1")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")

    np, tf, tflearn = import_runtime()
    np.random.seed(args.seed)

    logdir = args.tensorboard_dir
    if logdir is None:
        logdir = tempfile.mkdtemp(prefix="tflearn_custom_trainer_smoke_")
    else:
        if not os.path.isdir(logdir):
            os.makedirs(logdir)

    train_x, train_y = make_fixture(np)
    batch_size = min(args.batch_size, len(train_x))

    graph = tf.Graph()
    with graph.as_default():
        tf.set_random_seed(args.seed)

        x_ph = tf.placeholder(tf.float32, [None, 2], name="X")
        y_ph = tf.placeholder(tf.float32, [None, 2], name="Y")

        w1 = tf.Variable(tf.random_normal([2, 4], stddev=0.1), name="W1")
        b1 = tf.Variable(tf.zeros([4]), name="b1")
        w2 = tf.Variable(tf.random_normal([4, 2], stddev=0.1), name="W2")
        b2 = tf.Variable(tf.zeros([2]), name="b2")

        hidden = tf.nn.tanh(tf.matmul(x_ph, w1) + b1, name="hidden")
        logits = tf.add(tf.matmul(hidden, w2), b2, name="logits")
        loss = tf.reduce_mean(
            tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=y_ph),
            name="loss",
        )
        accuracy = tf.reduce_mean(
            tf.cast(tf.equal(tf.argmax(logits, 1), tf.argmax(y_ph, 1)), tf.float32),
            name="acc",
        )
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.2)

        trainop = tflearn.TrainOp(
            loss=loss,
            optimizer=optimizer,
            metric=accuracy,
            batch_size=batch_size,
        )
        trainer = tflearn.Trainer(
            train_ops=trainop,
            tensorboard_verbose=0,
            tensorboard_dir=logdir,
        )
        trainer.fit(
            {x_ph: train_x, y_ph: train_y},
            val_feed_dicts={x_ph: train_x, y_ph: train_y},
            n_epoch=args.epochs,
            show_metric=True,
            snapshot_epoch=False,
            run_id="custom_trainer_smoke",
        )
        pred, loss_value, acc_value = trainer.session.run(
            [tf.nn.softmax(logits), loss, accuracy],
            feed_dict={x_ph: train_x, y_ph: train_y},
        )

    if not np.isfinite(loss_value):
        raise RuntimeError("Smoke failed: final loss is not finite: %r" % loss_value)
    if pred.shape != (len(train_x), 2):
        raise RuntimeError("Smoke failed: unexpected prediction shape %r" % (pred.shape,))

    print(
        "OK custom_trainer_smoke epochs=%d batch_size=%d loss=%.6f acc=%.3f pred_shape=%s logdir=%s"
        % (args.epochs, batch_size, float(loss_value), float(acc_value), tuple(pred.shape), logdir)
    )


def main(argv=None):
    args = parse_args(argv)
    try:
        run_smoke(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print("custom_trainer_smoke.py failed: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
