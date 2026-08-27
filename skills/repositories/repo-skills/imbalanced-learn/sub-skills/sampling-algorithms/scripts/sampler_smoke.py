#!/usr/bin/env python3
"""Tiny representative smoke for imbalanced-learn samplers."""

from __future__ import annotations

from collections import Counter

import numpy as np
from sklearn.datasets import make_classification

from imblearn import FunctionSampler
from imblearn.combine import SMOTEENN, SMOTETomek
from imblearn.over_sampling import RandomOverSampler, SMOTE, SMOTENC, SMOTEN
from imblearn.under_sampling import RandomUnderSampler, TomekLinks


def main() -> int:
    X, y = make_classification(
        n_samples=100,
        n_features=5,
        n_informative=3,
        weights=[0.15, 0.85],
        random_state=0,
    )

    for name, sampler in [
        ("ros", RandomOverSampler(random_state=0)),
        ("smote", SMOTE(random_state=0)),
        ("rus", RandomUnderSampler(random_state=0)),
        ("tomek", TomekLinks()),
        ("smoteenn", SMOTEENN(random_state=0)),
        ("smotetomek", SMOTETomek(random_state=0)),
    ]:
        Xr, yr = sampler.fit_resample(X, y)
        print(name, Xr.shape, sorted(Counter(yr).items()))

    X_fun, y_fun = FunctionSampler(func=lambda X, y: (X[:8], y[:8])).fit_resample(X, y)
    print("function", X_fun.shape, len(y_fun))

    X_mixed = np.array(
        [
            [0.1, "red"],
            [0.2, "blue"],
            [0.3, "red"],
            [0.4, "blue"],
            [0.5, "green"],
            [0.6, "green"],
        ],
        dtype=object,
    )
    y_mixed = np.array([0, 0, 0, 0, 1, 1])
    X_nc, y_nc = SMOTENC(categorical_features=[1], random_state=0, k_neighbors=1).fit_resample(X_mixed, y_mixed)
    print("smotenc", X_nc.shape, sorted(Counter(y_nc).items()))

    X_cat = np.array([["a"], ["a"], ["b"], ["b"], ["c"], ["c"]], dtype=object)
    y_cat = np.array([0, 0, 0, 0, 1, 1])
    X_sn, y_sn = SMOTEN(random_state=0, k_neighbors=1).fit_resample(X_cat, y_cat)
    print("smoten", X_sn.shape, sorted(Counter(y_sn).items()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
