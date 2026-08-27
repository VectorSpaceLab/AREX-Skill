#!/usr/bin/env python3
"""Deterministic smoke checks for cleanlab standard classification APIs.

This helper uses only tiny in-memory fixtures. It verifies core noisy-label,
dataset-health, noise-generation, and data-valuation paths without downloads or
access to checkout source files.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

from cleanlab.benchmarking.noise_generation import (
    generate_noise_matrix_from_trace,
    generate_noisy_labels,
    noise_matrix_is_valid,
)
from cleanlab.classification import CleanLearning
from cleanlab.count import estimate_py_noise_matrices_and_cv_pred_proba, num_label_issues
from cleanlab.data_valuation import data_shapley_knn
from cleanlab.dataset import (
    find_overlapping_classes,
    health_summary,
    overall_label_health_score,
    rank_classes_by_label_quality,
)
from cleanlab.filter import find_label_issues
from cleanlab.rank import get_label_quality_scores

warnings.filterwarnings(
    "ignore",
    message="When X and pred_probs are both provided, the former may be ignored.",
)


def make_classifier() -> LogisticRegression:
    return LogisticRegression(solver="liblinear", max_iter=200, random_state=0)


def make_binary_fixture():
    x = np.array(
        [
            [0.00, 0.00],
            [0.10, 0.05],
            [-0.05, 0.10],
            [0.15, -0.10],
            [0.05, 0.15],
            [0.12, 0.08],
            [0.95, 1.00],
            [1.05, 0.90],
            [0.90, 1.10],
            [1.10, 1.05],
            [1.15, 1.10],
            [0.85, 0.95],
        ],
        dtype=float,
    )
    true_labels = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], dtype=int)
    noisy_labels = true_labels.copy()
    noisy_labels[10] = 0
    return x, true_labels, noisy_labels


def smoke_cleanlearning_and_label_issues() -> np.ndarray:
    x, true_labels, noisy_labels = make_binary_fixture()

    py, noise_matrix, inverse_noise_matrix, confident_joint, pred_probs = (
        estimate_py_noise_matrices_and_cv_pred_proba(
            x,
            noisy_labels,
            clf=make_classifier(),
            cv_n_folds=5,
            seed=0,
        )
    )

    assert pred_probs.shape == (len(noisy_labels), 2)
    assert np.allclose(pred_probs.sum(axis=1), 1.0, atol=1e-6)
    assert py.shape == (2,)
    assert noise_matrix.shape == (2, 2)
    assert inverse_noise_matrix.shape == (2, 2)
    assert confident_joint.shape == (2, 2)
    assert np.allclose(noise_matrix.sum(axis=0), 1.0, atol=1e-6)
    assert np.allclose(inverse_noise_matrix.sum(axis=0), 1.0, atol=1e-6)

    issue_mask = find_label_issues(
        noisy_labels,
        pred_probs,
        filter_by="confident_learning",
        min_examples_per_class=1,
        n_jobs=1,
    )
    issue_indices = find_label_issues(
        noisy_labels,
        pred_probs,
        filter_by="confident_learning",
        min_examples_per_class=1,
        n_jobs=1,
        return_indices_ranked_by="self_confidence",
    )
    issue_count = num_label_issues(noisy_labels, pred_probs)
    assert issue_mask.dtype == bool
    assert issue_mask.shape == noisy_labels.shape
    assert issue_indices.ndim == 1
    assert issue_mask.sum() == issue_count == len(issue_indices)

    quality_scores = get_label_quality_scores(noisy_labels, pred_probs)
    assert quality_scores.shape == noisy_labels.shape
    assert np.all((quality_scores >= 0.0) & (quality_scores <= 1.0))

    cl_cv = CleanLearning(
        clf=make_classifier(),
        seed=0,
        cv_n_folds=5,
        find_label_issues_kwargs={"min_examples_per_class": 1, "n_jobs": 1},
    )
    cl_cv.fit(x, noisy_labels)
    label_issues_cv = cl_cv.get_label_issues()
    assert isinstance(label_issues_cv, pd.DataFrame)
    assert len(label_issues_cv) == len(noisy_labels)
    assert {"is_label_issue", "label_quality", "given_label", "predicted_label"} <= set(
        label_issues_cv.columns
    )
    assert "sample_weight" in label_issues_cv.columns
    assert label_issues_cv["label_quality"].between(0.0, 1.0).all()
    assert label_issues_cv["sample_weight"].ge(0.0).all()
    assert len(cl_cv.predict(x)) == len(noisy_labels)
    assert cl_cv.predict_proba(x).shape == (len(noisy_labels), 2)
    assert 0.0 <= cl_cv.score(x, true_labels) <= 1.0

    cl_probs = CleanLearning(
        clf=make_classifier(),
        seed=0,
        find_label_issues_kwargs={"min_examples_per_class": 1, "n_jobs": 1},
    )
    cl_probs.fit(x, noisy_labels, pred_probs=pred_probs)
    label_issues_probs = cl_probs.get_label_issues()
    assert isinstance(label_issues_probs, pd.DataFrame)
    assert len(label_issues_probs) == len(noisy_labels)
    assert "sample_weight" in label_issues_probs.columns
    assert cl_probs.predict(x).shape == noisy_labels.shape
    assert cl_probs.predict_proba(x).shape == (len(noisy_labels), 2)

    return pred_probs


def smoke_dataset_health() -> None:
    labels = np.array([0, 0, 1, 1, 2, 2], dtype=int)
    pred_probs = np.array(
        [
            [0.45, 0.50, 0.05],
            [0.60, 0.35, 0.05],
            [0.40, 0.55, 0.05],
            [0.30, 0.60, 0.10],
            [0.10, 0.25, 0.65],
            [0.15, 0.35, 0.50],
        ],
        dtype=float,
    )
    class_names = ["zero", "one", "two"]

    summary = health_summary(labels=labels, pred_probs=pred_probs, class_names=class_names, verbose=False)
    score = overall_label_health_score(labels=labels, pred_probs=pred_probs, verbose=False)
    overlap = find_overlapping_classes(labels=labels, pred_probs=pred_probs, class_names=class_names)
    ranked = rank_classes_by_label_quality(labels=labels, pred_probs=pred_probs, class_names=class_names)

    assert set(summary) == {
        "overall_label_health_score",
        "joint",
        "classes_by_label_quality",
        "overlapping_classes",
    }
    assert isinstance(summary["classes_by_label_quality"], pd.DataFrame)
    assert isinstance(summary["overlapping_classes"], pd.DataFrame)
    assert summary["joint"].shape == (3, 3)
    assert len(ranked) == 3
    assert len(overlap) > 0
    assert 0.0 <= score <= 1.0
    assert abs(summary["overall_label_health_score"] - score) < 1e-12


def smoke_noise_generation() -> None:
    py = np.array([0.3, 0.4, 0.3], dtype=float)
    true_labels = np.array([0, 0, 1, 1, 2, 2], dtype=int)
    noise_matrix = generate_noise_matrix_from_trace(
        K=3,
        trace=2.2,
        py=py,
        valid_noise_matrix=True,
        seed=0,
    )
    assert noise_matrix is not None
    assert noise_matrix.shape == (3, 3)
    assert noise_matrix_is_valid(noise_matrix, py)

    noisy_labels = generate_noisy_labels(true_labels, noise_matrix)
    assert noisy_labels.shape == true_labels.shape
    assert set(np.unique(noisy_labels)).issubset({0, 1, 2})


def smoke_data_valuation() -> None:
    features = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.2, 0.2],
        ],
        dtype=float,
    )
    labels = np.array([0, 1, 0, 1, 0], dtype=int)
    knn_graph = NearestNeighbors(n_neighbors=3).fit(features).kneighbors_graph(mode="distance")

    scores_from_features = data_shapley_knn(labels=labels, features=features, k=3)
    scores_from_graph = data_shapley_knn(labels=labels, knn_graph=knn_graph, k=3)

    assert scores_from_features.shape == (5,)
    assert scores_from_graph.shape == (5,)
    assert np.all((scores_from_features >= 0.0) & (scores_from_features <= 1.0))
    assert np.all((scores_from_graph >= 0.0) & (scores_from_graph <= 1.0))
    assert np.isfinite(scores_from_features).all()
    assert np.isfinite(scores_from_graph).all()


def main() -> None:
    smoke_cleanlearning_and_label_issues()
    smoke_dataset_health()
    smoke_noise_generation()
    smoke_data_valuation()
    print("classification smoke: ok")


if __name__ == "__main__":
    main()
