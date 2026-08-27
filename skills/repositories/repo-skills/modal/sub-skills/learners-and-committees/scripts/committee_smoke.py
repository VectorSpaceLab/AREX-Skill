#!/usr/bin/env python3
"""Deterministic smoke checks for Committee and CommitteeRegressor workflows."""

from __future__ import annotations

import numpy as np
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from modAL.disagreement import max_std_sampling, vote_entropy_sampling
from modAL.models import ActiveLearner, Committee, CommitteeRegressor

SEED = 11


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def class_indices(y: np.ndarray, *class_counts: tuple[int, int]) -> np.ndarray:
    parts = [np.where(y == cls)[0][:count] for cls, count in class_counts]
    return np.concatenate(parts)


def run_committee_classification() -> None:
    iris = load_iris()
    X, y = iris.data, iris.target

    idx_a = class_indices(y, (0, 10), (1, 10))
    idx_b = class_indices(y, (1, 10), (2, 10))
    pool_idx = np.setdiff1d(np.arange(len(X)), np.union1d(idx_a, idx_b))

    learner_a = ActiveLearner(
        estimator=DecisionTreeClassifier(max_depth=4, random_state=SEED),
        X_training=X[idx_a],
        y_training=y[idx_a],
        bootstrap_init=True,
    )
    learner_b = ActiveLearner(
        estimator=DecisionTreeClassifier(max_depth=4, random_state=SEED + 1),
        X_training=X[idx_b],
        y_training=y[idx_b],
        bootstrap_init=True,
    )

    committee = Committee(
        learner_list=[learner_a, learner_b],
        query_strategy=vote_entropy_sampling,
    )

    require(committee.n_classes_ == 3, "committee should union the class labels")
    require(tuple(committee.classes_.tolist()) == (0, 1, 2), "committee.classes_ should be sorted and complete")

    votes = committee.vote(X[:8])
    require(votes.shape == (8, 2), "vote should return one column per learner")

    vote_proba = committee.vote_proba(X[:8])
    require(vote_proba.shape == (8, 2, 3), "vote_proba should expose all committee classes")
    require(np.allclose(vote_proba.sum(axis=2), 1.0), "each learner probability row should sum to 1")

    consensus = committee.predict_proba(X[:8])
    require(consensus.shape == (8, 3), "predict_proba should average across learners")

    preds = committee.predict(X[:8])
    require(preds.shape == (8,), "predict should return one class per row")
    require(set(np.unique(preds)).issubset({0, 1, 2}), "predictions should use the committee class space")

    score = committee.score(X, y)
    require(0.0 <= score <= 1.0, "committee.score should be an accuracy value")

    query_idx, query_rows, metrics = committee.query(X[pool_idx], return_metrics=True)
    require(metrics is not None, "committee query should report metrics when available")
    require(np.asarray(query_rows).ndim >= 1, "committee query should return selected rows")

    selected = int(np.atleast_1d(query_idx)[0])
    rows_before_teach = committee.learner_list[0].X_training.shape[0]
    committee.teach(
        X[pool_idx[selected]].reshape(1, -1),
        np.array([y[pool_idx[selected]]]),
        bootstrap=True,
    )
    require(
        committee.learner_list[0].X_training.shape[0] == rows_before_teach + 1,
        "committee teach should append the new row to each learner history",
    )

    committee.rebag()
    require(committee.predict(X[:8]).shape == (8,), "committee should remain usable after rebag")

    print("PASS committee classification")


def run_committee_regression() -> None:
    X = np.linspace(-1.0, 1.0, 30).reshape(-1, 1)
    y = np.sin(3.0 * X).ravel()

    idx_1 = np.arange(0, 6)
    idx_2 = np.arange(6, 12)
    idx_3 = np.arange(12, 18)
    pool_idx = np.arange(18, len(X))

    learners = [
        ActiveLearner(
            estimator=DecisionTreeRegressor(max_depth=4, random_state=SEED + offset),
            X_training=X[idx],
            y_training=y[idx],
        )
        for offset, idx in enumerate([idx_1, idx_2, idx_3])
    ]

    committee = CommitteeRegressor(
        learner_list=learners,
        query_strategy=max_std_sampling,
    )

    mean, std = committee.predict(X[:5], return_std=True)
    require(mean.shape == (5,), "CommitteeRegressor.predict(return_std=True) should return a mean vector")
    require(std.shape == (5,), "CommitteeRegressor.predict(return_std=True) should return a std vector")

    votes = committee.vote(X[:5])
    require(votes.shape == (5, 3), "vote should return one column per regressor")

    query_idx, query_rows, metrics = committee.query(X[pool_idx], return_metrics=True)
    require(metrics is not None, "CommitteeRegressor query should report std metrics")
    require(np.asarray(query_rows).ndim >= 1, "CommitteeRegressor query should return selected rows")

    selected = int(np.atleast_1d(query_idx)[0])
    committee.teach(
        X[pool_idx[selected]].reshape(1, -1),
        np.array([y[pool_idx[selected]]]),
        bootstrap=True,
    )

    committee.rebag()
    mean_after, std_after = committee.predict(X[:5], return_std=True)
    require(mean_after.shape == (5,), "CommitteeRegressor should stay usable after rebag")
    require(std_after.shape == (5,), "CommitteeRegressor std output should stay usable after rebag")

    print("PASS committee regression")


def main() -> None:
    np.random.seed(SEED)
    run_committee_classification()
    run_committee_regression()


if __name__ == "__main__":
    main()
