#!/usr/bin/env python3
"""Deterministic smoke checks for cleanlab.multiannotator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cleanlab.multiannotator import (
    convert_long_to_wide_dataset,
    get_active_learning_scores,
    get_active_learning_scores_ensemble,
    get_label_quality_multiannotator,
    get_label_quality_multiannotator_ensemble,
    get_majority_vote_label,
)


def make_toy_inputs() -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create a tiny deterministic multiannotator example."""

    wide = pd.DataFrame(
        [
            [0, 0, np.nan],
            [0, 1, np.nan],
            [1, 1, 2],
            [2, np.nan, 2],
        ],
        index=["task_0", "task_1", "task_2", "task_3"],
        columns=["ann_a", "ann_b", "ann_c"],
    )

    long = pd.DataFrame(
        [
            {"task": "task_0", "annotator": "ann_a", "label": 0},
            {"task": "task_0", "annotator": "ann_b", "label": 0},
            {"task": "task_1", "annotator": "ann_a", "label": 0},
            {"task": "task_1", "annotator": "ann_b", "label": 1},
            {"task": "task_2", "annotator": "ann_a", "label": 1},
            {"task": "task_2", "annotator": "ann_b", "label": 1},
            {"task": "task_2", "annotator": "ann_c", "label": 2},
            {"task": "task_3", "annotator": "ann_a", "label": 2},
            {"task": "task_3", "annotator": "ann_c", "label": 2},
        ]
    )

    pred_probs = np.array(
        [
            [0.80, 0.10, 0.10],
            [0.20, 0.70, 0.10],
            [0.10, 0.75, 0.15],
            [0.10, 0.10, 0.80],
        ],
        dtype=float,
    )

    pred_probs_ensemble = np.stack(
        [
            pred_probs,
            np.array(
                [
                    [0.70, 0.20, 0.10],
                    [0.10, 0.80, 0.10],
                    [0.15, 0.75, 0.10],
                    [0.05, 0.10, 0.85],
                ],
                dtype=float,
            ),
        ],
        axis=0,
    )

    pred_probs_unlabeled = np.array(
        [
            [0.34, 0.33, 0.33],
            [0.90, 0.05, 0.05],
        ],
        dtype=float,
    )

    pred_probs_unlabeled_ensemble = np.stack(
        [
            pred_probs_unlabeled,
            np.array(
                [
                    [0.30, 0.35, 0.35],
                    [0.85, 0.10, 0.05],
                ],
                dtype=float,
            ),
        ],
        axis=0,
    )

    return long, wide, pred_probs, pred_probs_ensemble, pred_probs_unlabeled, pred_probs_unlabeled_ensemble


def main() -> int:
    long, wide, pred_probs, pred_probs_ensemble, pred_probs_unlabeled, pred_probs_unlabeled_ensemble = make_toy_inputs()

    converted = convert_long_to_wide_dataset(long)
    pd.testing.assert_frame_equal(converted, wide.astype(float), check_dtype=False)

    majority_vote_df = get_majority_vote_label(wide, pred_probs)
    majority_vote_array = get_majority_vote_label(wide.to_numpy(), pred_probs)
    np.testing.assert_array_equal(majority_vote_df, np.array([0, 1, 1, 2]))
    np.testing.assert_array_equal(majority_vote_df, majority_vote_array)

    results = get_label_quality_multiannotator(
        wide,
        pred_probs,
        consensus_method=["majority_vote", "best_quality"],
        return_weights=True,
        verbose=False,
    )
    assert set(results) == {
        "label_quality",
        "detailed_label_quality",
        "annotator_stats",
        "model_weight",
        "annotator_weight",
    }

    label_quality = results["label_quality"]
    assert list(label_quality.columns) == [
        "consensus_label",
        "consensus_quality_score",
        "annotator_agreement",
        "num_annotations",
        "consensus_label_best_quality",
        "consensus_quality_score_best_quality",
        "annotator_agreement_best_quality",
    ]
    np.testing.assert_array_equal(label_quality["consensus_label"].to_numpy(), majority_vote_df)
    assert label_quality["consensus_quality_score"].between(0, 1).all()
    assert label_quality["annotator_agreement"].between(0, 1).all()
    assert np.array_equal(label_quality["num_annotations"].to_numpy(), np.array([2, 2, 3, 2]))

    detailed = results["detailed_label_quality"]
    assert detailed.shape == wide.shape
    assert list(detailed.columns) == [
        "quality_annotator_ann_a",
        "quality_annotator_ann_b",
        "quality_annotator_ann_c",
    ]
    assert detailed.isna().sum().sum() == 3

    annotator_stats = results["annotator_stats"]
    assert set(annotator_stats.index) == set(wide.columns)
    assert list(annotator_stats.columns) == [
        "annotator_quality",
        "agreement_with_consensus",
        "worst_class",
        "num_examples_labeled",
    ]
    assert np.isscalar(results["model_weight"])
    assert np.asarray(results["annotator_weight"]).shape == (3,)

    agreement_only = get_label_quality_multiannotator(
        wide.to_numpy(),
        pred_probs,
        consensus_method="majority_vote",
        quality_method="agreement",
        return_detailed_quality=False,
        return_annotator_stats=False,
        verbose=False,
    )
    assert set(agreement_only) == {"label_quality"}
    np.testing.assert_array_equal(
        agreement_only["label_quality"]["consensus_label"].to_numpy(), majority_vote_df
    )

    labeled_scores, unlabeled_scores = get_active_learning_scores(
        labels_multiannotator=wide,
        pred_probs=pred_probs,
        pred_probs_unlabeled=pred_probs_unlabeled,
    )
    assert labeled_scores.shape == (4,)
    assert unlabeled_scores.shape == (2,)
    assert np.all((0 <= labeled_scores) & (labeled_scores <= 1))
    assert np.all((0 <= unlabeled_scores) & (unlabeled_scores <= 1))
    assert unlabeled_scores[0] < unlabeled_scores[1]

    ensemble_results = get_label_quality_multiannotator_ensemble(
        wide,
        pred_probs_ensemble.copy(),
        return_weights=True,
        verbose=False,
    )
    assert set(ensemble_results) == {
        "label_quality",
        "detailed_label_quality",
        "annotator_stats",
        "model_weight",
        "annotator_weight",
    }
    assert ensemble_results["model_weight"].shape == (2,)
    assert np.asarray(ensemble_results["annotator_weight"]).shape == (3,)
    assert ensemble_results["detailed_label_quality"].shape == wide.shape

    ensemble_labeled_scores, ensemble_unlabeled_scores = get_active_learning_scores_ensemble(
        labels_multiannotator=wide,
        pred_probs=pred_probs_ensemble.copy(),
        pred_probs_unlabeled=pred_probs_unlabeled_ensemble.copy(),
    )
    assert ensemble_labeled_scores.shape == (4,)
    assert ensemble_unlabeled_scores.shape == (2,)
    assert np.all((0 <= ensemble_labeled_scores) & (ensemble_labeled_scores <= 1))
    assert np.all((0 <= ensemble_unlabeled_scores) & (ensemble_unlabeled_scores <= 1))
    assert ensemble_unlabeled_scores[0] < ensemble_unlabeled_scores[1]

    print("multiannotator smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
