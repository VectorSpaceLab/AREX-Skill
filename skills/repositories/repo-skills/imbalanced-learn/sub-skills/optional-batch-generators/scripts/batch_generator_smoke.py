#!/usr/bin/env python3
"""Tiny optional-backend smoke for imbalanced-learn batch generators."""

from __future__ import annotations

from collections import Counter

from sklearn.datasets import make_classification

from imblearn.under_sampling import RandomUnderSampler


def main() -> int:
    X, y = make_classification(
        n_samples=120,
        n_features=4,
        n_informative=2,
        weights=[0.2, 0.8],
        random_state=0,
    )

    try:
        from imblearn.tensorflow import balanced_batch_generator
    except Exception as exc:  # pragma: no cover - optional backend path
        print("tensorflow_generator_skipped", type(exc).__name__)
    else:
        tf_gen, steps = balanced_batch_generator(
            X,
            y,
            sampler=RandomUnderSampler(random_state=0),
            batch_size=16,
            random_state=0,
        )
        xb, yb = next(tf_gen)
        print("tensorflow", steps, xb.shape, yb.shape, sorted(Counter(yb).items()))

    try:
        from imblearn.keras import BalancedBatchGenerator
    except Exception as exc:  # pragma: no cover - optional backend path
        print("keras_generator_skipped", type(exc).__name__)
    else:
        gen = BalancedBatchGenerator(
            X,
            y,
            sampler=RandomUnderSampler(random_state=0),
            batch_size=16,
            random_state=0,
        )
        xb, yb = gen[0]
        print("keras", len(gen), xb.shape, yb.shape, sorted(Counter(yb).items()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
