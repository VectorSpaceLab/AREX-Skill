#!/usr/bin/env python3
"""Deterministic smoke for modAL query-strategy helpers."""

from __future__ import annotations

import warnings

import numpy as np
from scipy.spatial.distance import euclidean
from sklearn.exceptions import ConvergenceWarning
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC

from modAL.batch import uncertainty_batch_sampling
from modAL.density import information_density, similarize_distance
from modAL.models import ActiveLearner
from modAL.multilabel import (
    SVM_binary_minimum,
    avg_confidence,
    avg_score,
    max_loss,
    max_score,
    mean_max_loss,
    min_confidence,
)
from modAL.uncertainty import classifier_margin, classifier_uncertainty
from modAL.utils.combination import make_linear_combination, make_product, make_query_strategy
from modAL.utils.selection import multi_argmax

warnings.filterwarnings("ignore", category=ConvergenceWarning)
np.random.seed(7)


def _shape(value):
    return np.asarray(value).shape


def _expect_shape(label, value, expected):
    actual = _shape(value)
    if actual != expected:
        raise AssertionError(f"{label}: expected shape {expected}, got {actual}")


def _build_binary_dataset():
    x = np.array(
        [
            [0.0, 0.1],
            [0.2, 0.8],
            [0.8, 0.2],
            [1.0, 0.9],
            [0.1, 0.3],
            [0.9, 0.7],
        ],
        dtype=float,
    )
    y = np.array([0, 0, 1, 1, 0, 1], dtype=int)
    return x[:4], y[:4], x[4:], y[4:]


def _build_multilabel_dataset():
    x = np.array(
        [
            [0.0, 0.0],
            [0.1, 0.9],
            [0.9, 0.1],
            [1.0, 1.0],
            [0.2, 0.7],
            [0.8, 0.3],
            [0.3, 0.2],
            [0.7, 0.8],
        ],
        dtype=float,
    )
    y = np.array(
        [
            [0, 0],
            [0, 1],
            [1, 0],
            [1, 1],
            [0, 1],
            [1, 0],
            [0, 0],
            [1, 1],
        ],
        dtype=int,
    )
    return x[:6], y[:6], x[6:], y[6:]


def smoke_custom_strategy():
    x_train, y_train, x_pool, _ = _build_binary_dataset()

    combined = make_linear_combination(
        classifier_uncertainty,
        lambda learner, x: 1.0 - classifier_margin(learner, x),
        weights=[0.7, 0.3],
    )
    product = make_product(classifier_uncertainty, classifier_margin, exponents=[1.0, 1.0])

    def top2_selector(values):
        return multi_argmax(values, n_instances=2)

    learner = ActiveLearner(
        estimator=GaussianNB(),
        query_strategy=make_query_strategy(combined, top2_selector),
        X_training=x_train,
        y_training=y_train,
    )

    query_idx, query_rows, query_metrics = learner.query(x_pool, return_metrics=True)
    _expect_shape("custom query indices", query_idx, (2,))
    _expect_shape("custom query rows", query_rows, (2, 2))
    _expect_shape("custom query metrics", query_metrics, (2,))
    _expect_shape("product utility", product(learner, x_pool), (len(x_pool),))


def smoke_ranked_batch():
    x_train, y_train, x_pool, _ = _build_binary_dataset()
    learner = ActiveLearner(
        estimator=GaussianNB(),
        query_strategy=uncertainty_batch_sampling,
        X_training=x_train,
        y_training=y_train,
    )

    query_idx, query_rows, query_metrics = learner.query(
        x_pool,
        return_metrics=True,
        n_instances=2,
        metric="euclidean",
        n_jobs=1,
    )
    _expect_shape("ranked batch indices", query_idx, (2,))
    _expect_shape("ranked batch rows", query_rows, (2, 2))
    _expect_shape("ranked batch metrics", query_metrics, (2,))


def smoke_information_density():
    x = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
        ],
        dtype=float,
    )
    density = information_density(x)
    euclidean_density = information_density(x, similarize_distance(euclidean))
    _expect_shape("density", density, (4,))
    _expect_shape("euclidean density", euclidean_density, (4,))


def smoke_multilabel():
    x_train, y_train, x_pool, _ = _build_multilabel_dataset()

    binary_learner = ActiveLearner(
        estimator=OneVsRestClassifier(LinearSVC(dual=False, max_iter=5000, random_state=0)),
        query_strategy=SVM_binary_minimum,
        X_training=x_train,
        y_training=y_train,
    )
    binary_idx, binary_row = binary_learner.query(x_pool)
    _expect_shape("SVM binary minimum index", binary_idx, ())
    _expect_shape("SVM binary minimum row", binary_row, (2,))

    prob_model = OneVsRestClassifier(GaussianNB())
    prob_model.fit(x_train, y_train)

    for fn in [max_loss, mean_max_loss, min_confidence, avg_confidence, max_score, avg_score]:
        query_idx, query_metrics = fn(prob_model, x_pool, n_instances=2, random_tie_break=False)
        _expect_shape(f"{fn.__name__} indices", query_idx, (2,))
        _expect_shape(f"{fn.__name__} metrics", query_metrics, (2,))


def main():
    smoke_custom_strategy()
    smoke_ranked_batch()
    smoke_information_density()
    smoke_multilabel()
    print("PASS")


if __name__ == "__main__":
    main()
