#!/usr/bin/env python3
"""Deterministic smoke checks for ActiveLearner workflows.

Covers pool-based querying, stream-based sampling, bootstrap/only_new/fit
history handling, return_metrics, and on_transformed query paths.
"""

from __future__ import annotations

import numpy as np
from sklearn.datasets import make_classification
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from modAL.batch import uncertainty_batch_sampling
from modAL.models import ActiveLearner
from modAL.uncertainty import classifier_uncertainty, uncertainty_sampling

SEED = 7


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def balanced_initial_indices(y: np.ndarray, per_class: int) -> np.ndarray:
    indices = [np.where(y == cls)[0][:per_class] for cls in np.unique(y)]
    return np.concatenate(indices)


def make_data() -> tuple[np.ndarray, np.ndarray]:
    return make_classification(
        n_samples=60,
        n_features=4,
        n_informative=3,
        n_redundant=0,
        n_clusters_per_class=1,
        class_sep=0.6,
        flip_y=0.05,
        random_state=SEED,
    )


def run_pool_workflow(X: np.ndarray, y: np.ndarray) -> None:
    init_idx = balanced_initial_indices(y, per_class=12)
    pool_idx = np.setdiff1d(np.arange(len(X)), init_idx)

    X_init, y_init = X[init_idx], y[init_idx]
    X_pool, y_pool = X[pool_idx], y[pool_idx]

    learner = ActiveLearner(
        estimator=RandomForestClassifier(
            n_estimators=25,
            max_depth=4,
            random_state=SEED,
        ),
        query_strategy=uncertainty_sampling,
        X_training=X_init,
        y_training=y_init,
        bootstrap_init=True,
    )

    preds = learner.predict(X_pool[:5])
    require(preds.shape == (5,), "predict should return one label per row")
    require(0.0 <= learner.score(X_pool[:10], y_pool[:10]) <= 1.0, "score should be bounded")

    query_idx, query_rows, metrics = learner.query(X_pool, return_metrics=True)
    require(metrics is not None, "return_metrics should produce uncertainty values")
    require(np.asarray(query_rows).ndim >= 1, "query should return the selected rows")

    selected = int(np.atleast_1d(query_idx)[0])
    learner.teach(
        X_pool[selected].reshape(1, -1),
        np.array([y_pool[selected]]),
    )
    rows_after_default_teach = learner.X_training.shape[0]

    learner.teach(
        X_pool[(selected + 1) % len(X_pool)].reshape(1, -1),
        np.array([y_pool[(selected + 1) % len(X_pool)]]),
        bootstrap=True,
    )
    require(
        learner.X_training.shape[0] == rows_after_default_teach + 1,
        "bootstrap teach should append the new labeled row",
    )

    rows_before_only_new = learner.X_training.shape[0]
    learner.teach(
        X_pool[(selected + 2) % len(X_pool)].reshape(1, -1),
        np.array([y_pool[(selected + 2) % len(X_pool)]]),
        only_new=True,
    )
    require(
        learner.X_training.shape[0] == rows_before_only_new,
        "only_new should not append to the stored training history",
    )

    X_reset = np.vstack([X_init[:3], X_init[12:15]])
    y_reset = np.hstack([y_init[:3], y_init[12:15]])
    learner.fit(X_reset, y_reset)
    require(learner.X_training.shape[0] == len(X_reset), "fit should reset the stored training history")

    print("PASS active-learning pool")


def run_stream_workflow(X: np.ndarray, y: np.ndarray) -> None:
    init_idx = balanced_initial_indices(y, per_class=10)
    pool_idx = np.setdiff1d(np.arange(len(X)), init_idx)

    learner = ActiveLearner(
        estimator=RandomForestClassifier(
            n_estimators=25,
            max_depth=4,
            random_state=SEED + 1,
        ),
        query_strategy=uncertainty_sampling,
        X_training=X[init_idx],
        y_training=y[init_idx],
    )

    stream_X = X[pool_idx[:12]]
    stream_y = y[pool_idx[:12]]
    uncertainties = classifier_uncertainty(learner, stream_X)
    threshold = float(np.median(uncertainties))

    queried = 0
    for row, label, uncertainty in zip(stream_X, stream_y, uncertainties):
        if uncertainty >= threshold:
            learner.teach(row.reshape(1, -1), np.array([label]))
            queried += 1

    require(queried > 0, "the stream loop should query at least one uncertain row")
    require(0.0 <= learner.score(X[pool_idx[12:20]], y[pool_idx[12:20]]) <= 1.0, "stream learner should remain usable")

    print("PASS active-learning stream")


def run_transformed_workflow(X: np.ndarray, y: np.ndarray) -> None:
    init_idx = balanced_initial_indices(y, per_class=10)
    pool_idx = np.setdiff1d(np.arange(len(X)), init_idx)

    learner = ActiveLearner(
        estimator=make_pipeline(
            StandardScaler(),
            PCA(n_components=2),
            LogisticRegression(max_iter=500, solver="liblinear", random_state=SEED),
        ),
        query_strategy=uncertainty_batch_sampling,
        X_training=X[init_idx],
        y_training=y[init_idx],
        on_transformed=True,
    )

    transformed = learner.transform_without_estimating(X[pool_idx[:3]])
    require(transformed.shape == (3, 2), "transform_without_estimating should expose the reduced feature space")

    query_idx, query_rows, metrics = learner.query(X[pool_idx], n_instances=1, return_metrics=True)
    require(metrics is not None, "on_transformed batch query should report metrics")
    require(np.asarray(query_rows).ndim >= 1, "query should return the selected rows")

    selected = int(np.atleast_1d(query_idx)[0])
    learner.teach(
        X[pool_idx[selected]].reshape(1, -1),
        np.array([y[pool_idx[selected]]]),
    )
    require(0.0 <= learner.score(X[pool_idx[3:12]], y[pool_idx[3:12]]) <= 1.0, "pipeline learner should remain usable")

    print("PASS active-learning transformed")


def main() -> None:
    np.random.seed(SEED)
    X, y = make_data()
    run_pool_workflow(X, y)
    run_stream_workflow(X, y)
    run_transformed_workflow(X, y)


if __name__ == "__main__":
    main()
