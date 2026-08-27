#!/usr/bin/env python
"""Bounded TensorFlow 1.x Reader -> Estimator -> export smoke test.

This helper intentionally does not import application readers or download
medical data.  It creates a deterministic in-memory feature/label generator,
trains at most a few steps, evaluates, resumes from the same model directory,
and checks a SavedModel export.  The default directory is a private temporary
folder; --model-dir is opt-in and is never deleted by this script.
"""
from __future__ import print_function

import argparse
import os
import tempfile

import numpy as np


_FEATURE_SHAPE = [2, 4, 4, 1]
_LABEL_SHAPE = [1]


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run a bounded synthetic DLTK TensorFlow 1.x Estimator smoke test.")
    parser.add_argument(
        "--steps", type=int, default=1, choices=(1, 2, 3),
        help="steps in the first train call (default: 1)")
    parser.add_argument(
        "--resume-steps", type=int, default=1, choices=(1, 2, 3),
        help="additional steps in the resume call (default: 1)")
    parser.add_argument(
        "--eval-steps", type=int, default=1, choices=(1, 2),
        help="bounded evaluation steps (default: 1)")
    parser.add_argument(
        "--seed", type=int, default=17,
        help="NumPy and TensorFlow seed for the synthetic fixture")
    parser.add_argument(
        "--model-dir", default=None,
        help="optional caller-owned model directory; it is never deleted")
    parser.add_argument(
        "--restart", action="store_true",
        help="rejected intentionally; use a new model directory instead")
    return parser


def synthetic_read_fn(file_references, mode, params=None):
    """Yield fixed-shape examples matching Reader's nested contract."""
    del mode
    params = params or {}
    count = int(params.get("count", 4))
    base = np.linspace(-1.0, 1.0, num=32, dtype=np.float32).reshape(
        _FEATURE_SHAPE)
    # file_references is deliberately accepted like a real DLTK reader.  The
    # fixture does not interpret paths or touch the filesystem.
    references = file_references or [None]
    for ref_index, unused_reference in enumerate(references):
        del unused_reference
        for index in range(count):
            offset = np.float32((ref_index + index) * 0.01)
            feature = (base + offset).astype(np.float32)
            target = np.asarray([np.mean(feature)], dtype=np.float32)
            yield {
                "features": {"x": feature},
                "labels": {"y": target},
            }


def make_model_fn(tf):
    """Return a small model_fn that exercises batch-norm update dependencies."""
    def model_fn(features, labels, mode, params):
        flat = tf.layers.flatten(features["x"])
        hidden = tf.layers.dense(flat, units=4, activation=tf.nn.relu)
        hidden = tf.layers.batch_normalization(
            hidden, training=(mode == tf.estimator.ModeKeys.TRAIN),
            name="fixture_batch_norm")
        logits = tf.layers.dense(hidden, units=1, name="fixture_logits")
        predictions = {"logits": logits, "y_": logits}

        if mode == tf.estimator.ModeKeys.PREDICT:
            return tf.estimator.EstimatorSpec(
                mode=mode,
                predictions=predictions,
                export_outputs={
                    "out": tf.estimator.export.PredictOutput(predictions)})

        if labels is None or "y" not in labels:
            raise ValueError("TRAIN/EVAL requires labels['y']")
        loss = tf.losses.mean_squared_error(
            labels=labels["y"], predictions=logits)
        optimizer = tf.train.AdamOptimizer(
            learning_rate=params["learning_rate"], epsilon=1e-5)
        global_step = tf.train.get_global_step()
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        # This dependency is the important legacy batch-normalization gate.
        with tf.control_dependencies(update_ops):
            train_op = optimizer.minimize(loss, global_step=global_step)
        eval_metric_ops = {
            "mse": tf.metrics.mean_squared_error(labels["y"], logits)}
        return tf.estimator.EstimatorSpec(
            mode=mode,
            predictions=predictions,
            loss=loss,
            train_op=train_op,
            eval_metric_ops=eval_metric_ops)

    return model_fn


def run_smoke(args):
    if args.restart:
        raise ValueError(
            "Refusing --restart: this smoke preserves model directories; "
            "choose a new --model-dir instead.")

    # Import the legacy stack after --help can be handled without it.  The
    # fixture is deliberately CPU-only so a caller's CUDA visibility or a
    # shared GPU cannot turn this tiny check into a device allocation test.
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    import tensorflow as tf
    if not tf.__version__.startswith("1."):
        raise RuntimeError(
            "This smoke requires TensorFlow 1.x; found %s" % tf.__version__)
    missing = [name for name in ("Session", "layers", "contrib", "estimator")
               if not hasattr(tf, name)]
    if missing:
        raise RuntimeError(
            "TensorFlow 1.x APIs are missing: %s" % ", ".join(missing))
    from dltk.io.abstract_reader import Reader

    tf.reset_default_graph()
    np.random.seed(args.seed)
    tf.set_random_seed(args.seed)

    example_shapes = {
        "features": {"x": list(_FEATURE_SHAPE)},
        "labels": {"y": list(_LABEL_SHAPE)},
    }
    dtypes = {
        "features": {"x": tf.float32},
        "labels": {"y": tf.float32},
    }
    reader_params = {"count": 4}
    reader = Reader(synthetic_read_fn, dtypes)
    references = [["synthetic", 0]]
    train_input_fn, train_hook = reader.get_inputs(
        file_references=references,
        mode=tf.estimator.ModeKeys.TRAIN,
        example_shapes=example_shapes,
        shuffle_cache_size=1,
        batch_size=2,
        params=reader_params)
    eval_input_fn, eval_hook = reader.get_inputs(
        file_references=references,
        mode=tf.estimator.ModeKeys.EVAL,
        example_shapes=example_shapes,
        shuffle_cache_size=1,
        batch_size=2,
        params=reader_params)

    def receiver_fn():
        # The feature receiver intentionally has no label placeholder.
        x = tf.placeholder(
            dtype=tf.float32,
            shape=[None] + list(_FEATURE_SHAPE),
            name="x")
        return tf.estimator.export.ServingInputReceiver({"x": x}, {"x": x})

    model_fn = make_model_fn(tf)

    if args.model_dir is None:
        directory_context = tempfile.TemporaryDirectory(
            prefix="dltk-estimator-smoke-")
        model_dir = directory_context.name
    else:
        directory_context = None
        model_dir = os.path.abspath(os.path.expanduser(args.model_dir))
        if os.path.abspath(os.getcwd()) == model_dir:
            raise ValueError(
                "Refusing to use the current working directory as --model-dir")
        if os.path.exists(model_dir) and not os.path.isdir(model_dir):
            raise ValueError("--model-dir is not a directory: %s" % model_dir)
        if not os.path.isdir(model_dir):
            os.makedirs(model_dir)

    try:
        estimator = tf.estimator.Estimator(
            model_fn=model_fn,
            model_dir=model_dir,
            params={"learning_rate": 0.01},
            config=tf.estimator.RunConfig(save_summary_steps=1))
        estimator.train(
            input_fn=train_input_fn,
            hooks=[train_hook],
            steps=args.steps)
        first_step = int(estimator.get_variable_value("global_step"))

        # Reusing the same Estimator and model_dir exercises checkpoint resume.
        estimator.train(
            input_fn=train_input_fn,
            hooks=[train_hook],
            steps=args.resume_steps)
        resumed_step = int(estimator.get_variable_value("global_step"))
        expected_step = first_step + args.resume_steps
        if resumed_step != expected_step:
            raise AssertionError(
                "resume global_step=%d, expected %d" %
                (resumed_step, expected_step))

        result = estimator.evaluate(
            input_fn=eval_input_fn,
            hooks=[eval_hook],
            steps=args.eval_steps)
        if "loss" not in result or not np.isfinite(result["loss"]):
            raise AssertionError("evaluation did not return a finite loss")

        export_dir = estimator.export_savedmodel(
            export_dir_base=model_dir,
            serving_input_receiver_fn=receiver_fn)
        if isinstance(export_dir, bytes):
            export_dir = export_dir.decode("utf-8")
        if not os.path.isdir(export_dir):
            raise AssertionError("export directory was not created")
        saved_model = os.path.join(export_dir, "saved_model.pb")
        if not os.path.isfile(saved_model):
            raise AssertionError("export is missing saved_model.pb")

        print("PASS synthetic Reader -> Estimator train/eval/resume/export")
        print("global_step=%d eval_loss=%.6g" %
              (resumed_step, float(result["loss"])))
        print("exported_saved_model=%s" % saved_model)
    finally:
        # TemporaryDirectory removes only the directory created by this run.
        # Caller-owned --model-dir is intentionally left untouched.
        if directory_context is not None:
            directory_context.cleanup()


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        run_smoke(args)
    except (ImportError, RuntimeError, ValueError, AssertionError) as exc:
        raise SystemExit("tiny_estimator_smoke: %s" % exc)


if __name__ == "__main__":
    main()
