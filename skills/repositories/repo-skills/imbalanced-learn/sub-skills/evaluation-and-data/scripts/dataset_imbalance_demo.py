#!/usr/bin/env python3
"""Tiny dataset-shaping demo for imbalanced-learn."""

from __future__ import annotations

from collections import Counter

from sklearn.datasets import load_iris

from imblearn.datasets import fetch_datasets, make_imbalance


def main() -> int:
    iris = load_iris()
    X_imb, y_imb = make_imbalance(
        iris.data, iris.target, sampling_strategy={0: 10, 1: 20, 2: 30}, random_state=42
    )
    print("make_imbalance", sorted(Counter(y_imb).items()), X_imb.shape)

    try:
        cached = fetch_datasets(filter_data=("ecoli",), download_if_missing=False)
        print("fetch_datasets", list(cached))
    except Exception as exc:  # pragma: no cover - optional cached-data path
        print("fetch_datasets_skipped", type(exc).__name__)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
