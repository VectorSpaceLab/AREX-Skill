#!/usr/bin/env python3
"""Tiny smoke check for scikitplot.estimators."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
import scikitplot as skplt
from sklearn.datasets import load_breast_cancer, load_iris
from sklearn.ensemble import RandomForestClassifier


def smoke_feature_importances() -> None:
    iris = load_iris()
    clf = RandomForestClassifier(n_estimators=16, random_state=0, n_jobs=1)
    clf.fit(iris.data, iris.target)

    fig, ax = plt.subplots(figsize=(6, 4))
    out_ax = skplt.estimators.plot_feature_importances(
        clf,
        feature_names=iris.feature_names,
        max_num_features=4,
        order="descending",
        ax=ax,
    )
    assert out_ax is ax
    assert len(out_ax.patches) > 0
    plt.close(fig)


def smoke_learning_curve() -> None:
    X, y = load_breast_cancer(return_X_y=True)

    fig, ax = plt.subplots(figsize=(6, 4))
    out_ax = skplt.estimators.plot_learning_curve(
        RandomForestClassifier(n_estimators=16, random_state=0, n_jobs=1),
        X,
        y,
        cv=3,
        shuffle=True,
        random_state=0,
        train_sizes=np.linspace(0.3, 1.0, 3),
        scoring="accuracy",
        ax=ax,
    )
    assert out_ax is ax
    assert len(out_ax.lines) >= 2
    plt.close(fig)


def main() -> int:
    smoke_feature_importances()
    smoke_learning_curve()
    plt.close("all")
    print("estimators smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
