#!/usr/bin/env python3
"""Run a tiny keras-vis optimization smoke test.

The script builds a minimal Keras model, defines a custom Loss subclass,
runs `Optimizer.minimize()` for a few iterations, and prints the optimized
input plus gradient / target tensor shapes.

It is designed to fail loudly on import/backend problems while remaining safe
and best-effort deterministic by default. Exact repeatability still depends on
the active legacy backend and its execution environment.
"""

from __future__ import print_function

import argparse
import random
import sys


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny keras-vis optimization smoke test.",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=3,
        help="Number of optimization iterations to run. Default: %(default)s",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1337,
        help="Random seed for numpy and backend RNGs when supported. Default: %(default)s",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)

    try:
        import numpy as np
        import keras.backend as K
        from keras.layers import Dense
        from keras.models import Sequential

        from vis.losses import Loss
        from vis.optimizer import Optimizer
    except Exception as exc:  # pragma: no cover - environment guard
        print(f"import/backend error: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    random.seed(args.seed)
    np.random.seed(args.seed)
    keras_seed_set = False
    try:
        if hasattr(K, "set_random_seed"):
            K.set_random_seed(args.seed)
            keras_seed_set = True
    except Exception:
        pass
    if not keras_seed_set:
        try:
            import tensorflow as tf

            if hasattr(tf, "set_random_seed"):
                tf.set_random_seed(args.seed)
            elif hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
                tf.compat.v1.set_random_seed(args.seed)
        except Exception:
            # Legacy backends differ in seed APIs; NumPy/Python seeding remains applied.
            pass

    class _TinyLoss(Loss):
        def __init__(self, tensor):
            super().__init__()
            self.name = "tiny-smoke-loss"
            self._tensor = tensor

        def build_loss(self):
            return K.sum(self._tensor * self._tensor)

    model = Sequential([
        Dense(4, activation="linear", input_shape=(2,)),
    ])
    loss = _TinyLoss(model.output)
    optimizer = Optimizer(model.input, [(loss, 1.0)], wrt_tensor=None, norm_grads=True)

    seed_input = np.array([[0.25, -0.75]], dtype=K.floatx())
    try:
        optimized_input, grads, wrt_value = optimizer.minimize(
            seed_input=seed_input,
            max_iter=args.max_iter,
            verbose=False,
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        print(f"optimization error: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 3

    print(f"optimized_input_shape={optimized_input.shape}")
    print(f"grads_shape={getattr(grads, 'shape', None)}")
    print(f"wrt_value_shape={getattr(wrt_value, 'shape', None)}")
    print(f"optimized_input={np.asarray(optimized_input).tolist()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
