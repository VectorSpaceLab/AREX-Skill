#!/usr/bin/env python
"""Smoke-test keras-vis activation maximization on a tiny local model.

The script is best-effort deterministic and safe by default:
- no model downloads;
- no dataset reads;
- no source-checkout imports are added to sys.path;
- small image shape and a tiny max_iter default.

It is intended as an environment probe for the generated keras-vis skill.
"""
from __future__ import print_function

import argparse
import os
import random
import sys
import traceback
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run a tiny keras-vis visualize_activation smoke test."
    )
    parser.add_argument(
        "--target",
        choices=("dense", "regression", "conv"),
        default="dense",
        help="Layer type to target: dense class output, regression output, or conv filter.",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=3,
        help="Maximum optimizer iterations. Keep small for smoke tests.",
    )
    parser.add_argument(
        "--filter-index",
        type=int,
        default=0,
        help="Class/unit/filter index to maximize in the selected target layer.",
    )
    parser.add_argument(
        "--decrease-regression",
        action="store_true",
        help="For --target regression, negate gradients to decrease the selected output.",
    )
    parser.add_argument(
        "--input-min",
        type=float,
        default=0.0,
        help="Minimum value for visualize_activation input_range.",
    )
    parser.add_argument(
        "--input-max",
        type=float,
        default=1.0,
        help="Maximum value for visualize_activation input_range.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="Random seed for NumPy and TensorFlow when available.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print keras-vis per-iteration loss values.",
    )
    return parser.parse_args(argv)


def import_runtime():
    """Import legacy runtime dependencies and return the imported objects."""
    import numpy as np
    import keras
    from keras import backend as K
    from keras.layers import Conv2D, Dense, Flatten
    from keras.models import Sequential
    from vis.visualization import visualize_activation
    from vis.utils import utils

    return np, keras, K, Conv2D, Dense, Flatten, Sequential, visualize_activation, utils


def print_import_advice(exc):
    print("IMPORT_ERROR: {}".format(exc), file=sys.stderr)
    print(
        "This smoke test expects keras-vis 0.5.0 with standalone Keras 2.2.x "
        "and a TensorFlow 1.x graph-mode backend. Install legacy dependencies "
        "before debugging activation-maximization model code; do not replace "
        "these imports with tensorflow.keras for this skill.",
        file=sys.stderr,
    )


def set_seeds(np, K, seed):
    """Apply available process and backend seeds without promising bitwise reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if K.backend() == "tensorflow":
        try:
            import tensorflow as tf

            keras_seed_set = False
            try:
                if hasattr(K, "set_random_seed"):
                    K.set_random_seed(seed)
                    keras_seed_set = True
            except Exception:
                pass
            if not keras_seed_set:
                if hasattr(tf, "set_random_seed"):
                    tf.set_random_seed(seed)
                elif hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
                    tf.compat.v1.set_random_seed(seed)
        except Exception:
            # Seeding is best-effort; failure should not hide activation errors.
            pass


def build_tiny_model(target, K, Conv2D, Dense, Flatten, Sequential):
    """Build a tiny untrained model with image input and named target layers."""
    model = Sequential(name="activation_smoke_model")
    model.add(
        Conv2D(
            2,
            (3, 3),
            activation="relu",
            input_shape=(8, 8, 1),
            name="conv_probe",
        )
    )
    model.add(Flatten(name="flatten_probe"))
    if target == "regression":
        model.add(Dense(1, activation="linear", name="regression_probe"))
        return model, "regression_probe"
    model.add(Dense(3, activation="linear", name="dense_probe"))
    if target == "conv":
        return model, "conv_probe"
    return model, "dense_probe"


def initialize_variables_if_needed(K):
    """Initialize TensorFlow graph variables for old standalone Keras backends."""
    if K.backend() != "tensorflow":
        return
    try:
        import tensorflow as tf

        initializer = getattr(tf, "global_variables_initializer", None)
        if initializer is None and hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
            initializer = tf.compat.v1.global_variables_initializer
        if initializer is not None and hasattr(K, "get_session"):
            K.get_session().run(initializer())
    except Exception:
        # Some Keras backends initialize lazily; let the actual smoke call decide.
        pass


def run(argv):
    args = parse_args(argv)
    if args.max_iter < 1:
        print("ERROR: --max-iter must be >= 1", file=sys.stderr)
        return 2
    if args.input_max <= args.input_min:
        print("ERROR: --input-max must be greater than --input-min", file=sys.stderr)
        return 2

    try:
        (
            np,
            keras,
            K,
            Conv2D,
            Dense,
            Flatten,
            Sequential,
            visualize_activation,
            utils,
        ) = import_runtime()
    except ImportError as exc:
        print_import_advice(exc)
        return 2

    old_format = K.image_data_format()
    try:
        set_seeds(np, K, args.seed)
        K.set_image_data_format("channels_last")
        model, layer_name = build_tiny_model(args.target, K, Conv2D, Dense, Flatten, Sequential)
        initialize_variables_if_needed(K)
        layer_idx = utils.find_layer_idx(model, layer_name)

        grad_modifier = None
        if args.target == "regression" and args.decrease_regression:
            grad_modifier = "negate"

        output = visualize_activation(
            model,
            layer_idx,
            filter_indices=args.filter_index,
            input_range=(args.input_min, args.input_max),
            max_iter=args.max_iter,
            verbose=args.verbose,
            grad_modifier=grad_modifier,
        )
        arr = np.asarray(output)

        print("status=ok")
        print("target={}".format(args.target))
        print("layer_name={}".format(layer_name))
        print("layer_idx={}".format(layer_idx))
        print("filter_index={}".format(args.filter_index))
        print("keras_version={}".format(getattr(keras, "__version__", "unknown")))
        print("backend={}".format(K.backend()))
        print("image_data_format={}".format(K.image_data_format()))
        print("output_shape={}".format(tuple(arr.shape)))
        print("output_dtype={}".format(arr.dtype))
        print("output_range=({:.6f}, {:.6f})".format(float(arr.min()), float(arr.max())))
        return 0
    except ImportError as exc:
        print_import_advice(exc)
        return 2
    except Exception as exc:
        print("SMOKE_FAILED: {}".format(exc), file=sys.stderr)
        traceback.print_exc()
        return 1
    finally:
        K.set_image_data_format(old_format)


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
