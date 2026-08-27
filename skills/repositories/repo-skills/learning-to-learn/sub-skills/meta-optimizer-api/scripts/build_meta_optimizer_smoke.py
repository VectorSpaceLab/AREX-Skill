#!/usr/bin/env python3
"""Build a tiny MetaOptimizer graph and optionally run a CPU smoke step."""

from __future__ import absolute_import, division, print_function

import argparse
import os
import random
import sys
import tempfile


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny Learning to Learn MetaOptimizer graph from a source "
            "checkout and optionally run a single CPU smoke step."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to the learning-to-learn repository root.",
    )
    parser.add_argument(
        "--run-session",
        action="store_true",
        help=(
            "Initialize the graph, run one tiny CPU unroll step, and exercise "
            "a .l2l save/load roundtrip in a temporary directory."
        ),
    )
    return parser.parse_args(argv)


def add_repo_root(repo_root):
    repo_root = os.path.abspath(repo_root)
    if not os.path.isdir(repo_root):
        raise SystemExit("repo root does not exist: %s" % repo_root)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    return repo_root


def build_graph(tf, meta, problems):
    tf.set_random_seed(0)
    random.seed(0)

    problem = problems.simple()
    optimizer = meta.MetaOptimizer(
        net={
            "net": "CoordinateWiseDeepLSTM",
            "net_options": {"layers": (), "initializer": "zeros"},
        }
    )
    meta_step = optimizer.meta_minimize(problem, len_unroll=2, learning_rate=1e-2)

    reset_op = tf.group(*meta_step.reset, name="reset")
    update_op = tf.group(*meta_step.update, name="update")
    return optimizer, meta_step, reset_op, update_op


def run_smoke(tf, meta, problems, optimizer, meta_step, reset_op, update_op):
    summary = {}
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        sess.run(reset_op)

        before_fx, before_x = sess.run([meta_step.fx, meta_step.x])
        sess.run(update_op)
        sess.run(meta_step.step)
        after_fx, after_x = sess.run([meta_step.fx, meta_step.x])

        summary["before_fx"] = before_fx
        summary["after_fx"] = after_fx
        summary["before_x"] = before_x
        summary["after_x"] = after_x

        with tempfile.TemporaryDirectory(prefix="l2l-meta-smoke-") as tmpdir:
            saved = optimizer.save(sess, path=tmpdir)
            if not saved:
                raise RuntimeError("optimizer.save returned no .l2l files")
            saved_path = next(iter(sorted(saved)))
            if not os.path.exists(saved_path):
                raise RuntimeError("missing saved file: %s" % saved_path)

            summary["saved_path"] = saved_path

            with tf.Graph().as_default():
                tf.set_random_seed(0)
                reloaded_problem = problems.simple()
                reloaded_optimizer = meta.MetaOptimizer(
                    net={
                        "net": "CoordinateWiseDeepLSTM",
                        "net_options": {"layers": (), "initializer": "zeros"},
                        "net_path": saved_path,
                    }
                )
                reloaded_step = reloaded_optimizer.meta_minimize(
                    reloaded_problem,
                    len_unroll=2,
                    learning_rate=1e-2,
                )
                reloaded_reset = tf.group(*reloaded_step.reset, name="reset")
                with tf.Session() as reload_sess:
                    reload_sess.run(tf.global_variables_initializer())
                    reload_sess.run(reloaded_reset)
                    summary["reload_fx"] = reload_sess.run(reloaded_step.fx)

    return summary


def main(argv=None):
    args = parse_args(argv)
    repo_root = add_repo_root(args.repo_root)

    import numpy as np
    import tensorflow as tf

    import meta
    import problems

    np.random.seed(0)

    with tf.Graph().as_default():
        optimizer, meta_step, reset_op, update_op = build_graph(tf, meta, problems)
        print("built_meta_optimizer_smoke ok")
        print("repo_root=%s" % repo_root)
        print("loss_shape=%s" % (meta_step.fx.get_shape().as_list(),))
        print("x_count=%d" % len(meta_step.x))

        if args.run_session:
            summary = run_smoke(tf, meta, problems, optimizer, meta_step, reset_op, update_op)
            print("session_smoke ok")
            print("before_fx=%s" % summary["before_fx"])
            print("after_fx=%s" % summary["after_fx"])
            print("saved_path=%s" % summary["saved_path"])
            print("reload_fx=%s" % summary["reload_fx"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
