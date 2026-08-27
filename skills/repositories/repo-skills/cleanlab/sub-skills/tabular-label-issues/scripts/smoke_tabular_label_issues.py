#!/usr/bin/env python3
"""Deterministic smoke checks for tabular label-issue workflows."""

from __future__ import annotations

import argparse
import json

import numpy as np
from sklearn.linear_model import LinearRegression

from cleanlab.multilabel_classification import (
    get_label_quality_scores as get_multilabel_label_quality_scores,
)
from cleanlab.multilabel_classification import dataset as ml_dataset
from cleanlab.multilabel_classification import filter as ml_filter
from cleanlab.multilabel_classification import rank as ml_rank
from cleanlab.regression.learn import CleanLearning
from cleanlab.regression.rank import get_label_quality_scores as get_regression_label_quality_scores


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_multilabel_fixture() -> tuple[list[list[int]], np.ndarray]:
    multi_hot = np.array(
        [
            [1, 0, 0],
            [0, 1, 0],
            [1, 1, 0],
            [0, 0, 1],
            [0, 0, 0],
        ],
        dtype=int,
    )
    labels = [np.flatnonzero(row).tolist() for row in multi_hot]
    pred_probs = np.array(
        [
            [0.98, 0.01, 0.01],
            [0.02, 0.96, 0.02],
            [0.94, 0.93, 0.03],
            [0.01, 0.02, 0.97],
            [0.95, 0.94, 0.92],
        ],
        dtype=float,
    )
    return labels, pred_probs


def run_multilabel() -> dict[str, object]:
    labels, pred_probs = make_multilabel_fixture()
    class_names = ["alpha", "beta", "gamma"]

    # Use the direct multilabel filter that most clearly surfaces the missing-label example.
    issues_mask = ml_filter.find_label_issues(
        labels=labels,
        pred_probs=pred_probs,
        filter_by="predicted_neq_given",
    )
    ranked_issues = ml_filter.find_label_issues(
        labels=labels,
        pred_probs=pred_probs,
        return_indices_ranked_by="self_confidence",
        filter_by="predicted_neq_given",
    )
    per_class_mask = ml_filter.find_multilabel_issues_per_class(
        labels=labels,
        pred_probs=pred_probs,
        filter_by="predicted_neq_given",
    )
    scores = get_multilabel_label_quality_scores(labels, pred_probs)
    per_class_scores = ml_rank.get_label_quality_scores_per_class(labels, pred_probs)
    class_table = ml_dataset.rank_classes_by_multilabel_quality(
        labels=labels,
        pred_probs=pred_probs,
        class_names=class_names,
    )
    issue_table = ml_dataset.common_multilabel_issues(
        labels=labels,
        pred_probs=pred_probs,
        class_names=class_names,
    )
    health = ml_dataset.overall_multilabel_health_score(labels=labels, pred_probs=pred_probs)
    summary = ml_dataset.multilabel_health_summary(
        labels=labels,
        pred_probs=pred_probs,
        class_names=class_names,
        verbose=False,
    )

    expect(len(labels) == 5, "multilabel fixture should contain 5 examples")
    expect(labels[-1] == [], "last multilabel example should demonstrate an empty label list")
    expect(issues_mask.shape == (len(labels),), "multilabel issue mask should be 1D")
    expect(per_class_mask.shape == pred_probs.shape, "per-class multilabel mask should match pred_probs shape")
    expect(bool(per_class_mask[-1].all()), "missing-label multilabel example should be flagged for every class")
    expect(per_class_scores.shape == pred_probs.shape, "per-class scores should match pred_probs shape")
    expect(np.all(np.isfinite(scores)), "multilabel scores should be finite")
    expect(np.all((scores >= 0) & (scores <= 1)), "multilabel scores should lie in [0, 1]")
    expect(int(np.argmin(scores)) == len(labels) - 1, "missing-label multilabel example should have the lowest score")
    expect(ranked_issues[0] == len(labels) - 1, "missing-label multilabel example should rank first")
    expect(bool(issues_mask[-1]), "missing-label multilabel example should be flagged")
    expect(class_table.shape[0] == 3, "class ranking table should have one row per class")
    expect("Label Quality Score" in class_table.columns, "class ranking table should expose label quality scores")
    expect("Issue Probability" in issue_table.columns, "common issue table should expose issue probabilities")
    expect(np.isclose(summary["overall_multilabel_health_score"], health), "summary should reuse overall health score")
    expect(sorted(summary.keys()) == ["classes_by_multilabel_quality", "common_multilabel_issues", "overall_multilabel_health_score"], "summary should expose the expected keys")

    return {
        "flagged_indices": [int(i) for i in np.flatnonzero(issues_mask)],
        "ranked_issue_indices": [int(i) for i in ranked_issues],
        "lowest_quality_index": int(np.argmin(scores)),
        "overall_health_score": float(health),
        "class_table_rows": int(class_table.shape[0]),
    }


def make_regression_fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X = np.arange(12, dtype=float).reshape(-1, 1)
    clean_targets = 0.5 * X[:, 0] + 1.0
    noisy_targets = clean_targets.copy()
    noisy_targets[8] += 5.0
    return X, noisy_targets, clean_targets


def run_regression() -> dict[str, object]:
    X, y, clean_targets = make_regression_fixture()
    predictions = clean_targets.copy()
    weights = np.linspace(1.0, 2.0, len(y))

    residual_scores = get_regression_label_quality_scores(y, predictions, method="residual")
    outre_scores = get_regression_label_quality_scores(y, predictions, method="outre")
    expect(np.argmin(residual_scores) == 8, "corrupted regression target should have the lowest residual score")
    expect(np.argmin(outre_scores) == 8, "corrupted regression target should have the lowest OUTRE score")
    expect(np.all((residual_scores >= 0) & (residual_scores <= 1)), "residual scores should lie in [0, 1]")
    expect(np.all((outre_scores >= 0) & (outre_scores <= 1)), "OUTRE scores should lie in [0, 1]")

    cl = CleanLearning(
        model=LinearRegression(),
        cv_n_folds=3,
        n_boot=0,
        include_aleatoric_uncertainty=False,
        seed=0,
    )
    issues = cl.find_label_issues(X, y)
    expect({"is_label_issue", "label_quality", "given_label", "predicted_label"}.issubset(issues.columns), "CleanLearning issue table should expose the expected columns")
    expect(len(issues) == len(y), "CleanLearning issue table should have one row per example")
    expect(issues["label_quality"].between(0, 1).all(), "CleanLearning label_quality should lie in [0, 1]")
    expect(int(issues["label_quality"].idxmin()) == 8, "corrupted regression target should have the lowest label_quality")
    expect(bool(issues.loc[8, "is_label_issue"]), "corrupted regression target should be flagged")

    cl.fit(X, y, label_issues=issues, sample_weight=weights)
    preds = cl.predict(X)
    score = cl.score(X, y, sample_weight=weights)
    cached_issues = cl.get_label_issues()

    expect(preds.shape == y.shape, "CleanLearning predictions should match the target shape")
    expect(isinstance(score, float), "CleanLearning score should be a float")
    expect(cached_issues is not None, "CleanLearning should cache the label issues DataFrame after fit")

    cl.save_space()
    expect(cl.get_label_issues() is None, "save_space should clear cached label issues")

    return {
        "flagged_indices": [int(i) for i in issues.index[issues["is_label_issue"]]],
        "lowest_quality_index": int(np.argmin(outre_scores)),
        "fit_score": float(score),
        "predictions_head": [float(x) for x in preds[:3]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("all", "multilabel", "regression"),
        default="all",
        help="Which smoke checks to run.",
    )
    args = parser.parse_args()

    result: dict[str, object] = {}
    if args.mode in {"all", "multilabel"}:
        result["multilabel"] = run_multilabel()
    if args.mode in {"all", "regression"}:
        result["regression"] = run_regression()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
