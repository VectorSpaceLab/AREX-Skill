#!/usr/bin/env python3
"""Tiny smoke checks for tslearn supervised-model workflows.

Modes map to the supervised example families:
- neighbors: nearest-neighbor search/classification/regression plus a tiny sklearn pipeline search
- svm: GAK SVC/SVR on variable-length data
- early: non-myopic early classification on equal-length data
- shapelets: Keras-backend-safe LearningShapelets fit/transform/predict
- all: run all modes and a tiny equal-length TimeSeriesMLP check
"""

from __future__ import annotations

import argparse
import os
from typing import Callable

import numpy as np

from tslearn.utils import to_time_series_dataset


def variable_length_dataset():
    X = to_time_series_dataset([
        [1, 2, 3, 4],
        [1, 2, 3],
        [1, 2, 3, 4, 5],
        [9, 8, 7, 6, 5, 2],
        [8, 7, 6, 5, 3],
        [9, 8, 7, 6],
    ])
    y_cls = np.array([0, 0, 0, 1, 1, 1])
    y_reg = np.array([0.1, 0.2, 0.3, 1.1, 1.2, 1.3])
    return X, y_cls, y_reg


def equal_length_dataset():
    X = to_time_series_dataset([
        [1, 2, 3, 4, 5, 6],
        [1, 2, 3, 4, 5, 5],
        [1, 2, 3, 3, 2, 1],
        [1, 2, 4, 3, 2, 1],
        [3, 2, 1, 1, 2, 3],
        [3, 2, 1, 2, 2, 3],
    ])
    y_cls = np.array([0, 0, 1, 1, 0, 0])
    y_reg = np.array([0.0, 0.1, 1.0, 1.1, 0.2, 0.3])
    return X, y_cls, y_reg


def run_neighbors() -> None:
    from sklearn.model_selection import GridSearchCV, StratifiedKFold
    from sklearn.pipeline import Pipeline
    from tslearn.neighbors import (
        KNeighborsTimeSeries,
        KNeighborsTimeSeriesClassifier,
        KNeighborsTimeSeriesRegressor,
    )
    from tslearn.preprocessing import TimeSeriesScalerMinMax

    X, y_cls, y_reg = variable_length_dataset()

    search = KNeighborsTimeSeries(n_neighbors=2, metric="dtw").fit(X)
    dists, indices = search.kneighbors(X[:2])
    assert dists.shape == indices.shape == (2, 2)

    clf = KNeighborsTimeSeriesClassifier(n_neighbors=1, metric="dtw").fit(X, y_cls)
    assert clf.predict(X).shape == y_cls.shape

    reg = KNeighborsTimeSeriesRegressor(n_neighbors=1, metric="dtw").fit(X, y_reg)
    assert reg.predict(X).shape == y_reg.shape

    pipe = Pipeline([
        ("scale", TimeSeriesScalerMinMax()),
        ("knn", KNeighborsTimeSeriesClassifier(metric="dtw")),
    ])
    grid = GridSearchCV(
        pipe,
        {"knn__n_neighbors": [1, 2], "knn__weights": ["uniform"]},
        cv=StratifiedKFold(n_splits=2, shuffle=True, random_state=0),
    )
    grid.fit(X, y_cls)
    assert grid.predict(X).shape == y_cls.shape
    print("neighbors: ok")


def run_svm() -> None:
    from tslearn.svm import TimeSeriesSVC, TimeSeriesSVR

    X, y_cls, y_reg = variable_length_dataset()

    svc = TimeSeriesSVC(kernel="gak", gamma=1.0, random_state=0).fit(X, y_cls)
    assert svc.predict(X).shape == y_cls.shape

    svr = TimeSeriesSVR(kernel="gak", gamma=1.0).fit(X, y_reg)
    assert svr.predict(X).shape == y_reg.shape
    print("svm: ok")


def run_early() -> None:
    from tslearn.early_classification import NonMyopicEarlyClassifier
    from tslearn.neighbors import KNeighborsTimeSeriesClassifier

    X, y_cls, _ = equal_length_dataset()
    early = NonMyopicEarlyClassifier(
        n_clusters=2,
        base_classifier=KNeighborsTimeSeriesClassifier(n_neighbors=1, metric="euclidean"),
        min_t=2,
        lamb=10.0,
        cost_time_parameter=0.1,
        random_state=0,
    )
    early.fit(X, y_cls)
    preds, times = early.predict_class_and_earliness(X)
    assert preds.shape == times.shape == y_cls.shape
    partial_preds, delays = early.early_predict(X[:, :3])
    assert partial_preds.shape == delays.shape == y_cls.shape
    print("early: ok")


def run_shapelets() -> None:
    # Must happen before importing keras or tslearn.shapelets.
    os.environ.setdefault("KERAS_BACKEND", "torch")
    try:
        from tslearn.shapelets import LearningShapelets
    except ImportError as exc:
        raise SystemExit(
            "shapelets need Keras 3 plus a backend such as torch; "
            "set KERAS_BACKEND before importing keras or tslearn.shapelets"
        ) from exc

    X = to_time_series_dataset([[1, 2, 3, 4, 5], [3, 2, 1]])
    y = np.array([0, 1])
    model = LearningShapelets(
        n_shapelets_per_size={3: 1},
        max_iter=1,
        verbose=0,
        random_state=0,
        scale=True,
    )
    model.fit(X, y)
    assert model.predict(X).shape == y.shape
    assert model.transform(X).shape[0] == X.shape[0]
    assert model.locate(X).shape[0] == X.shape[0]
    print("shapelets: ok")


def run_mlp() -> None:
    from tslearn.neural_network import TimeSeriesMLPClassifier, TimeSeriesMLPRegressor

    X, y_cls, y_reg = equal_length_dataset()
    clf = TimeSeriesMLPClassifier(hidden_layer_sizes=(4,), max_iter=2, random_state=0)
    clf.fit(X, y_cls)
    assert clf.predict(X).shape == y_cls.shape

    reg = TimeSeriesMLPRegressor(hidden_layer_sizes=(4,), max_iter=2, random_state=0)
    reg.fit(X, y_reg)
    assert reg.predict(X).shape == y_reg.shape
    print("mlp: ok")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["neighbors", "svm", "early", "shapelets", "all"],
        default="all",
        help="Which smoke workflow to run.",
    )
    args = parser.parse_args()

    modes: dict[str, Callable[[], None]] = {
        "neighbors": run_neighbors,
        "svm": run_svm,
        "early": run_early,
        "shapelets": run_shapelets,
    }

    if args.mode == "all":
        for name in ["neighbors", "svm", "early", "shapelets"]:
            modes[name]()
        run_mlp()
    else:
        modes[args.mode]()


if __name__ == "__main__":
    main()
