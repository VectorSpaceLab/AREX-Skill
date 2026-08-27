#!/usr/bin/env python3
"""Tiny categorical-distance demo for imbalanced-learn."""

from __future__ import annotations

import numpy as np
from sklearn.preprocessing import OrdinalEncoder

from imblearn.metrics.pairwise import ValueDifferenceMetric


def main() -> int:
    X = np.array(["green"] * 10 + ["red"] * 10 + ["blue"] * 10).reshape(-1, 1)
    y = np.array(["apple"] * 8 + ["not apple"] * 5 + ["apple"] * 7 + ["not apple"] * 9 + ["apple"])
    encoder = OrdinalEncoder(dtype=np.int32)
    X_encoded = encoder.fit_transform(X)
    vdm = ValueDifferenceMetric().fit(X_encoded, y)
    X_test = np.array(["green", "red", "blue"]).reshape(-1, 1)
    print(vdm.pairwise(encoder.transform(X_test)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
