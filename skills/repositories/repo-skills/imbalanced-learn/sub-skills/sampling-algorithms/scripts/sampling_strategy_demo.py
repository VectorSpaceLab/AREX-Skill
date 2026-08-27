#!/usr/bin/env python3
"""Show dict and callable sampling strategies on a tiny dataset."""

from __future__ import annotations

from collections import Counter

from sklearn.datasets import load_iris

from imblearn.datasets import make_imbalance


def ratio_multiplier(y):
    multiplier = {0: 0.5, 1: 0.7, 2: 0.95}
    stats = Counter(y)
    for key, value in stats.items():
        stats[key] = int(value * multiplier[key])
    return stats


def main() -> int:
    iris = load_iris()
    X, y = iris.data, iris.target
    print("original", sorted(Counter(y).items()))

    X_dict, y_dict = make_imbalance(
        X, y, sampling_strategy={0: 10, 1: 20, 2: 30}, random_state=42
    )
    print("dict", sorted(Counter(y_dict).items()), X_dict.shape)

    X_call, y_call = make_imbalance(X, y, sampling_strategy=ratio_multiplier)
    print("callable", sorted(Counter(y_call).items()), X_call.shape)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
