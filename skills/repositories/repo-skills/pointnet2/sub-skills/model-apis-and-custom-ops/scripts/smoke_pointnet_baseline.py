#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the CPU-safe PointNet baseline graph from models/pointnet_cls_basic.py.

This smoke intentionally avoids PointNet++ custom ops. It proves TensorFlow 1.x
and tf_util.py are usable enough for the baseline model API.

Compatible with Python 2.7 and Python 3.x so it can run inside legacy TF1
inspection environments.
"""
from __future__ import print_function

import argparse
import json
import os
import sys
import traceback

try:
    import __builtin__ as builtins  # Python 2
except ImportError:  # pragma: no cover - Python 3
    import builtins


def _parents(path):
    path = os.path.abspath(path)
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent


def find_repo_root(explicit):
    if explicit:
        root = os.path.abspath(os.path.expanduser(explicit))
        if not os.path.exists(root):
            raise SystemExit("repo root does not exist: %s" % root)
        return root
    starts = [os.getcwd(), os.path.abspath(__file__)]
    for start in starts:
        for candidate in _parents(start):
            if os.path.isfile(os.path.join(candidate, "models", "pointnet_cls_basic.py")) and os.path.isfile(
                os.path.join(candidate, "utils", "tf_util.py")
            ):
                return candidate
    raise SystemExit("could not infer repo root; pass --repo-root /path/to/pointnet2")


def fail(message, detail=None, as_json=False):
    payload = {"ok": False, "message": message}
    if detail:
        payload.update(detail)
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("ERROR: %s" % message, file=sys.stderr)
        if detail:
            for key in sorted(detail.keys()):
                print("  %s: %s" % (key, detail[key]), file=sys.stderr)
    return 1


def import_tensorflow():
    try:
        import tensorflow as tf
    except BaseException as exc:
        raise RuntimeError("TensorFlow import failed: %s: %s" % (type(exc).__name__, exc))
    if hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
        try:
            tf.compat.v1.disable_eager_execution()
        except Exception:
            pass
    if not hasattr(tf, "contrib"):
        raise RuntimeError(
            "TensorFlow imported but tf.contrib is missing. The source tf_util.py uses "
            "tf.contrib.layers.xavier_initializer and batch_norm; use TensorFlow 1.x "
            "rather than a TF2-only environment."
        )
    required = ["Graph", "Session", "variable_scope", "get_variable", "placeholder"]
    missing = [name for name in required if not hasattr(tf, name)]
    if missing:
        raise RuntimeError("TensorFlow lacks TF1 graph symbols required by source code: " + ", ".join(missing))
    return tf


def run_smoke(repo_root, batch_size, num_point, run_session):
    if not hasattr(builtins, "xrange"):
        setattr(builtins, "xrange", range)

    tf = import_tensorflow()

    models_dir = os.path.join(repo_root, "models")
    utils_dir = os.path.join(repo_root, "utils")
    for path in [models_dir, utils_dir]:
        if path not in sys.path:
            sys.path.insert(0, path)

    try:
        import pointnet_cls_basic
    except BaseException as exc:
        raise RuntimeError("import pointnet_cls_basic failed: %s: %s" % (type(exc).__name__, exc))

    with tf.Graph().as_default():
        with tf.device("/cpu:0"):
            inputs = tf.zeros((batch_size, num_point, 3), dtype=tf.float32)
            logits, end_points = pointnet_cls_basic.get_model(inputs, tf.constant(False))
            static_shape = logits.get_shape().as_list()
            if static_shape != [batch_size, 40]:
                raise RuntimeError("unexpected logits static shape %s; expected [%s, 40]" % (static_shape, batch_size))
            labels = tf.zeros((batch_size,), dtype=tf.int32)
            loss = pointnet_cls_basic.get_loss(logits, labels, end_points)

        result = {
            "ok": True,
            "repo_root": repo_root,
            "tensorflow_version": getattr(tf, "__version__", "unknown"),
            "batch_size": batch_size,
            "num_point": num_point,
            "logits_static_shape": static_shape,
            "loss_tensor_shape": loss.get_shape().as_list(),
            "ran_session": False,
        }
        if run_session:
            with tf.Session() as sess:
                sess.run(tf.global_variables_initializer())
                logits_value, loss_value = sess.run([logits, loss])
            result.update(
                {
                    "ran_session": True,
                    "logits_runtime_shape": list(logits_value.shape),
                    "loss_value": float(loss_value),
                }
            )
        return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Path to the pointnet2 checkout. If omitted, search upward.")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size for the graph smoke.")
    parser.add_argument("--num-point", type=int, default=16, help="Number of XYZ points for the graph smoke.")
    parser.add_argument("--run-session", action="store_true", help="Also initialize variables and run one CPU session step.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.batch_size <= 0 or args.num_point <= 0:
        return fail("--batch-size and --num-point must be positive", as_json=args.json)
    repo_root = find_repo_root(args.repo_root)
    try:
        result = run_smoke(repo_root, args.batch_size, args.num_point, args.run_session)
    except BaseException as exc:
        return fail(
            str(exc),
            {"traceback_tail": traceback.format_exc(limit=4).splitlines()[-8:]},
            as_json=args.json,
        )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("PointNet baseline graph smoke: OK")
        print("  repo_root: %s" % result["repo_root"])
        print("  tensorflow_version: %s" % result["tensorflow_version"])
        print("  logits_static_shape: %s" % result["logits_static_shape"])
        if result["ran_session"]:
            print("  logits_runtime_shape: %s" % result["logits_runtime_shape"])
            print("  loss_value: %s" % result["loss_value"])
        print("  custom_ops_required: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
