#!/usr/bin/env python
"""Build a tiny TFLearn layer graph and print collection checks.

This script is intentionally safe: no network, no dataset download, no training,
and no dependency on a source checkout. It imports the installed ``tflearn``
package, builds a small TensorFlow-v1-style graph, and optionally runs one
prediction tensor through a session.
"""

from __future__ import absolute_import, division, print_function

import argparse
import sys


def _version(package_name):
    """Return an installed distribution version without printing install paths."""
    try:
        try:
            from importlib.metadata import version  # Python >= 3.8
        except Exception:  # pragma: no cover - Python 3.7 fallback
            from importlib_metadata import version
        return version(package_name)
    except Exception:
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except Exception:
            return "unknown"


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test TFLearn layer/operation graph construction without "
            "training or downloading data."
        )
    )
    parser.add_argument(
        "--skip-session-run",
        action="store_true",
        help="Only build the graph and print collections; do not open a TensorFlow session.",
    )
    parser.add_argument(
        "--features",
        type=int,
        default=4,
        help="Number of input features for the synthetic input placeholder (default: 4).",
    )
    parser.add_argument(
        "--hidden-units",
        type=int,
        default=3,
        help="Hidden units per branch before merge (default: 3).",
    )
    parser.add_argument(
        "--classes",
        type=int,
        default=2,
        help="Number of output classes for the classification head (default: 2).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="TensorFlow graph seed for deterministic graph initialization (default: 7).",
    )
    return parser.parse_args(argv)


def import_runtime():
    try:
        import tensorflow.compat.v1 as tf
        tf.disable_v2_behavior()
    except Exception as exc:
        print("ERROR importing tensorflow.compat.v1: %s" % exc, file=sys.stderr)
        return None, None

    try:
        import tflearn
    except Exception as exc:
        print("ERROR importing tflearn: %s" % exc, file=sys.stderr)
        print(
            "Hint: this package is TensorFlow-v1-style. A verified baseline is "
            "TensorFlow 1.15.x with protobuf 3.20.x; modern TensorFlow 2.x "
            "builds may lack private TF1 symbols used by TFLearn.",
            file=sys.stderr,
        )
        return tf, None

    return tf, tflearn


def collection_names(tf, key):
    names = []
    for item in tf.get_collection(key):
        name = getattr(item, "name", None)
        if name is None and hasattr(item, "__class__"):
            name = item.__class__.__name__
        names.append(str(name))
    return names


def build_graph(tf, tflearn, args):
    graph = tf.Graph()
    with graph.as_default():
        tf.set_random_seed(args.seed)
        tflearn.init_graph(seed=args.seed, soft_placement=True)

        x = tflearn.input_data(shape=[None, args.features], name="SmokeInput")
        left = tflearn.fully_connected(
            x,
            args.hidden_units,
            activation="relu",
            name="left_dense",
        )
        right = tflearn.fully_connected(
            x,
            args.hidden_units,
            activation="tanh",
            name="right_dense",
        )
        merged = tflearn.merge([left, right], mode="concat", axis=1, name="branch_merge")
        dropped = tflearn.dropout(merged, keep_prob=0.9, name="smoke_dropout")
        logits = tflearn.fully_connected(
            dropped,
            args.classes,
            activation="linear",
            name="logits",
        )
        predictions = tflearn.activation(logits, activation="softmax", name="predictions")
        network = tflearn.regression(
            predictions,
            optimizer="sgd",
            learning_rate=0.01,
            loss="categorical_crossentropy",
            metric="accuracy",
            batch_size=2,
            name="SmokeTargets",
            op_name="smoke_sgd",
        )

        checks = {
            "input_tensor": x.name,
            "merged_tensor": merged.name,
            "prediction_tensor": network.name,
            "prediction_shape": network.get_shape().as_list(),
            "left_dense_vars": [v.name for v in tflearn.get_layer_variables_by_name("left_dense")],
            "logits_vars": [v.name for v in tflearn.get_layer_variables_by_name("logits")],
            "inputs": collection_names(tf, tf.GraphKeys.INPUTS),
            "targets": collection_names(tf, tf.GraphKeys.TARGETS),
            "train_ops": collection_names(tf, tf.GraphKeys.TRAIN_OPS),
            "activations_count": len(tf.get_collection(tf.GraphKeys.ACTIVATIONS)),
            "layer_tensor_merge": collection_names(tf, tf.GraphKeys.LAYER_TENSOR + "/branch_merge"),
            "regularization_losses_count": len(tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)),
        }
        init_op = tf.global_variables_initializer()
    return graph, x, network, init_op, checks


def print_checks(tf, checks):
    print("tflearn_version: %s" % _version("tflearn"))
    print("tensorflow_version: %s" % getattr(tf, "__version__", "unknown"))
    print("input_tensor: %s" % checks["input_tensor"])
    print("merged_tensor: %s" % checks["merged_tensor"])
    print("prediction_tensor: %s" % checks["prediction_tensor"])
    print("prediction_static_shape: %s" % checks["prediction_shape"])
    print("left_dense_vars: %s" % ", ".join(checks["left_dense_vars"]))
    print("logits_vars: %s" % ", ".join(checks["logits_vars"]))
    print("collection INPUTS: %d %s" % (len(checks["inputs"]), checks["inputs"]))
    print("collection TARGETS: %d %s" % (len(checks["targets"]), checks["targets"]))
    print("collection TRAIN_OPS: %d %s" % (len(checks["train_ops"]), checks["train_ops"]))
    print("collection ACTIVATIONS: %d" % checks["activations_count"])
    print("collection LAYER_TENSOR/branch_merge: %d %s" % (
        len(checks["layer_tensor_merge"]), checks["layer_tensor_merge"]
    ))
    print("collection REGULARIZATION_LOSSES: %d" % checks["regularization_losses_count"])


def run_session(tf, tflearn, graph, input_tensor, prediction_tensor, init_op, args):
    sample = [
        [0.0 for _ in range(args.features)],
        [1.0 for _ in range(args.features)],
    ]
    with graph.as_default():
        with tf.Session() as sess:
            sess.run(init_op)
            # Ensure dropout/batchnorm-style training mode is off for this prediction check.
            try:
                tflearn.is_training(False, session=sess)
            except Exception as exc:
                print("warning: could not set tflearn prediction mode: %s" % exc)
            pred = sess.run(prediction_tensor, feed_dict={input_tensor: sample})
    print("session_run: enabled")
    print("prediction_shape: %s" % (getattr(pred, "shape", None),))
    print("prediction_row_sums: %s" % [round(float(row.sum()), 6) for row in pred])


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.features < 1 or args.hidden_units < 1 or args.classes < 1:
        print("ERROR: --features, --hidden-units, and --classes must be positive integers.", file=sys.stderr)
        return 2

    tf, tflearn = import_runtime()
    if tf is None or tflearn is None:
        return 2

    graph, x, predictions, init_op, checks = build_graph(tf, tflearn, args)
    print_checks(tf, checks)

    if args.skip_session_run:
        print("session_run: skipped")
    else:
        run_session(tf, tflearn, graph, x, predictions, init_op, args)

    if len(checks["inputs"]) != 1 or len(checks["targets"]) != 1 or len(checks["train_ops"]) != 1:
        print("ERROR: expected exactly one input, target, and train op collection entry.", file=sys.stderr)
        return 1
    print("OK layer graph smoke completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
