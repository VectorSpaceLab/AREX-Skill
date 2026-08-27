#!/usr/bin/env python
"""Check a TFLearn runtime without relying on a source checkout.

The check imports TensorFlow compat.v1 and tflearn, prints public versions and
key signatures, optionally probes GPU visibility, and can build a tiny graph.
It performs no downloads and does not train a model.
"""
from __future__ import absolute_import, division, print_function

import argparse
import inspect
import sys


def dist_version(package_name):
    try:
        try:
            from importlib.metadata import version
        except Exception:
            from importlib_metadata import version
        return version(package_name)
    except Exception:
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except Exception:
            return "unknown"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Import and inspect a TFLearn/TensorFlow-v1-style runtime."
    )
    parser.add_argument(
        "--skip-graph",
        action="store_true",
        help="Only import and inspect signatures; do not build the tiny graph.",
    )
    parser.add_argument(
        "--probe-gpu",
        action="store_true",
        help="Also call the TensorFlow 1.x GPU visibility probe.",
    )
    return parser.parse_args(argv)


def import_runtime():
    try:
        import tensorflow.compat.v1 as tf
        try:
            tf.disable_v2_behavior()
        except Exception:
            pass
    except Exception as exc:
        print("ERROR importing tensorflow.compat.v1: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        print("Install a TensorFlow 1.x-compatible runtime before using TFLearn.", file=sys.stderr)
        return None, None

    try:
        import tflearn
    except Exception as exc:
        print("ERROR importing tflearn: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        print(
            "TFLearn 0.5.0 is legacy TensorFlow-v1-style code. A verified baseline "
            "is TensorFlow 1.15.x, NumPy 1.18.x, and protobuf 3.20.x. Modern "
            "TensorFlow 2.x may lack private symbols used by TFLearn.",
            file=sys.stderr,
        )
        return tf, None
    return tf, tflearn


def print_signature(label, obj):
    try:
        sig = inspect.signature(obj)
    except Exception as exc:
        sig = "<signature unavailable: {}>".format(exc)
    print("{} {}".format(label, sig))


def build_tiny_graph(tf, tflearn):
    graph = tf.Graph()
    with graph.as_default():
        x = tflearn.input_data(shape=[None, 2], name="CheckInput")
        net = tflearn.fully_connected(x, 2, activation="softmax", name="CheckDense")
        net = tflearn.regression(net, optimizer="sgd", loss="categorical_crossentropy", name="CheckTarget")
        print("graph_input: {}".format(x.name))
        print("graph_output: {}".format(net.name))
        print("collection_INPUTS: {}".format(len(tf.get_collection(tf.GraphKeys.INPUTS))))
        print("collection_TARGETS: {}".format(len(tf.get_collection(tf.GraphKeys.TARGETS))))
        print("collection_TRAIN_OPS: {}".format(len(tf.get_collection(tf.GraphKeys.TRAIN_OPS))))


def main(argv=None):
    args = parse_args(argv)
    tf, tflearn = import_runtime()
    if tf is None or tflearn is None:
        return 2

    print("tflearn_distribution_version: {}".format(dist_version("tflearn")))
    print("tensorflow_distribution_version: {}".format(dist_version("tensorflow")))
    print("tensorflow_module_version: {}".format(getattr(tf, "__version__", "unknown")))
    print("numpy_distribution_version: {}".format(dist_version("numpy")))
    print("protobuf_distribution_version: {}".format(dist_version("protobuf")))

    print_signature("tflearn.init_graph", tflearn.init_graph)
    print_signature("tflearn.input_data", tflearn.input_data)
    print_signature("tflearn.fully_connected", tflearn.fully_connected)
    print_signature("tflearn.regression", tflearn.regression)
    print_signature("tflearn.DNN.fit", tflearn.DNN.fit)
    print_signature("tflearn.DNN.load", tflearn.DNN.load)

    if args.probe_gpu:
        try:
            print("tensorflow_gpu_available: {}".format(tf.test.is_gpu_available()))
        except Exception as exc:
            print("tensorflow_gpu_available: probe_failed: {}: {}".format(type(exc).__name__, exc))
    else:
        print("tensorflow_gpu_available: not probed (use --probe-gpu)")

    if args.skip_graph:
        print("tiny_graph: skipped")
    else:
        build_tiny_graph(tf, tflearn)
        print("tiny_graph: built")

    print("OK tflearn environment check completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
