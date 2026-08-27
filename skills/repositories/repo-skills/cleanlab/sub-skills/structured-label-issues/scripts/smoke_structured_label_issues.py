#!/usr/bin/env python3
"""Deterministic smoke checks for cleanlab structured-label-issue APIs.

This script uses tiny in-memory fixtures for token classification, object
detection, and semantic segmentation. It does not download data or read the
source repository.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import warnings
from typing import Any, Dict, List, Tuple

import numpy as np


# Compatibility for cleanlab versions that still call np.in1d internally while
# running against NumPy builds where that alias is unavailable. This only affects
# this smoke process and is safe to remove once the installed cleanlab/numpy pair
# no longer needs it.
if not hasattr(np, "in1d"):
    np.in1d = np.isin  # type: ignore[attr-defined]


def _prepare_matplotlib(enable: bool, require: bool) -> bool:
    """Configure a safe non-interactive backend for visualization helpers."""
    if not enable:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        plt.show = lambda *args, **kwargs: None  # type: ignore[assignment]
        return True
    except Exception as exc:  # pragma: no cover - depends on optional dependency
        if require:
            raise RuntimeError("matplotlib display checks were required but unavailable") from exc
        print(f"[structured-label-issues] skipping display checks: {exc}")
        return False


def _run_token_classification(display: bool) -> Dict[str, Any]:
    from cleanlab.token_classification.filter import find_label_issues
    from cleanlab.token_classification.rank import get_label_quality_scores, issues_from_scores
    from cleanlab.token_classification.summary import common_label_issues, display_issues

    tokens = [["Hello", "World"], ["#I", "love", "Cleanlab"], ["A"]]
    labels = [[0, 0], [1, 1, 1], [2]]
    pred_probs = [
        np.array([[0.9, 0.1, 0.0], [0.6, 0.2, 0.2]]),
        np.array([[0.1, 0.0, 0.9], [0.1, 0.8, 0.1], [0.1, 0.8, 0.1]]),
        np.array([[0.1, 0.1, 0.8]]),
    ]

    issues = find_label_issues(labels, pred_probs)
    assert issues == [(1, 0)], f"unexpected token issues: {issues}"

    sentence_scores, token_scores = get_label_quality_scores(labels, pred_probs, tokens=tokens)
    assert sentence_scores.shape == (3,)
    assert int(np.argmin(sentence_scores)) == 1

    threshold_issues = issues_from_scores(sentence_scores, token_scores=token_scores)
    assert threshold_issues == issues

    with contextlib.redirect_stdout(io.StringIO()):
        common_df = common_label_issues(
            issues,
            tokens,
            labels=labels,
            pred_probs=pred_probs,
            class_names=["A", "B", "C"],
            verbose=False,
        )
    assert not common_df.empty
    assert "#I" in common_df["token"].tolist()

    if display:
        display_issues(
            issues,
            tokens,
            labels=labels,
            pred_probs=pred_probs,
            class_names=["A", "B", "C"],
            top=1,
        )

    return {
        "issues": issues,
        "sentence_scores": sentence_scores.round(6).tolist(),
        "common_rows": int(len(common_df)),
    }


def _generate_detection_labels(num_classes: int, num_boxes: int) -> np.ndarray:
    return np.random.choice(num_classes, num_boxes)


def _generate_detection_bbox(image_size: int) -> List[int]:
    x2 = int(np.random.randint(low=2, high=image_size - 1))
    y2 = int(np.random.randint(low=2, high=image_size - 1))
    x1 = x2 - int(np.random.randint(low=1, high=x2))
    y1 = y2 - int(np.random.randint(low=1, high=y2))
    return [x1, y1, x2, y2]


def _generate_detection_annotation(
    *, num_classes: int, max_boxes: int, image_size: int
) -> Dict[str, np.ndarray]:
    num_boxes = int(np.random.randint(low=1, high=max_boxes))
    bboxes = np.array([_generate_detection_bbox(image_size) for _ in range(num_boxes)], dtype=float)
    labels = _generate_detection_labels(num_classes, num_boxes).astype(int)
    return {"bboxes": bboxes, "labels": labels}


def _generate_detection_prediction(
    annotation: Dict[str, np.ndarray],
    *,
    num_classes: int,
    max_boxes: int,
    image_size: int,
    is_issue: bool,
) -> np.ndarray:
    per_class: List[List[List[float]]] = [[] for _ in range(num_classes)]
    if not is_issue:
        for label, bbox in zip(annotation["labels"], annotation["bboxes"]):
            prob = float(np.random.randint(low=96, high=100) / 100)
            per_class[int(label)].append([float(x) for x in bbox] + [prob])
    else:
        num_predictions = int(np.random.randint(low=1, high=max_boxes + 1))
        for label in _generate_detection_labels(num_classes, num_predictions):
            bbox = _generate_detection_bbox(image_size)
            prob = float(np.random.randint(low=96, high=100) / 100)
            per_class[int(label)].append([float(x) for x in bbox] + [prob])

    return np.array(
        [
            np.array(boxes, dtype=float) if boxes else np.empty((0, 5), dtype=float)
            for boxes in per_class
        ],
        dtype=object,
    )


def _make_object_detection_fixture() -> Tuple[List[Dict[str, np.ndarray]], List[np.ndarray]]:
    np.random.seed(0)
    num_classes = 10
    num_good = 5
    num_bad = 5
    good_labels = [
        _generate_detection_annotation(num_classes=num_classes, max_boxes=10, image_size=300)
        for _ in range(num_good)
    ]
    good_predictions = [
        _generate_detection_prediction(
            annotation,
            num_classes=num_classes,
            max_boxes=12,
            image_size=300,
            is_issue=False,
        )
        for annotation in good_labels
    ]

    bad_labels = [
        _generate_detection_annotation(num_classes=num_classes, max_boxes=10, image_size=300)
        for _ in range(num_bad)
    ]
    bad_predictions = [
        _generate_detection_prediction(
            annotation,
            num_classes=num_classes,
            max_boxes=12,
            image_size=300,
            is_issue=True,
        )
        for annotation in bad_labels
    ]

    return good_labels + bad_labels, good_predictions + bad_predictions


def _run_object_detection(display: bool) -> Dict[str, Any]:
    from cleanlab.object_detection.filter import find_label_issues
    from cleanlab.object_detection.rank import get_label_quality_scores, issues_from_scores
    from cleanlab.object_detection.summary import object_counts_per_image, visualize

    labels, predictions = _make_object_detection_fixture()
    scores = get_label_quality_scores(labels, predictions, verbose=False)
    assert scores.shape == (10,)
    assert bool(np.all(scores[:5] > 0.9)), scores.tolist()
    assert bool(np.all(scores[5:] < 0.7)), scores.tolist()

    # find_label_issues prints a pruning message through its internal rank call;
    # capture it to keep smoke output machine-readable.
    with contextlib.redirect_stdout(io.StringIO()):
        issue_mask = find_label_issues(labels, predictions)
        ranked_issues = find_label_issues(labels, predictions, return_indices_ranked_by_score=True)
    assert issue_mask.tolist() == [False, False, False, False, False, True, True, True, True, True]
    assert set(ranked_issues.tolist()) == set(range(5, 10))

    score_issues = issues_from_scores(scores, threshold=1.0)
    assert int(score_issues[0]) in range(5, 10)

    label_counts, prediction_counts = object_counts_per_image(labels, predictions)
    assert len(label_counts) == len(prediction_counts) == 10

    if display:
        image = np.zeros((300, 300, 3), dtype=np.uint8)
        visualize(
            image,
            label=labels[int(ranked_issues[0])],
            prediction=predictions[int(ranked_issues[0])],
            class_names={str(i): f"class_{i}" for i in range(10)},
            overlay=False,
        )

    return {
        "ranked_issues": ranked_issues.astype(int).tolist(),
        "score_min_index": int(np.argmin(scores)),
        "label_counts_first_three": [int(x) for x in label_counts[:3]],
    }


def _make_segmentation_fixture() -> Tuple[np.ndarray, np.ndarray, List[int]]:
    np.random.seed(0)
    good_gt = np.zeros((10, 10), dtype=float)
    good_gt[:5, :] = 1.0
    bad_gt = np.ones((10, 10), dtype=float)
    bad_gt[:5, :] = 0.0

    good_pr = np.random.random((2, 10, 10))
    good_pr[0, :5, :] = good_pr[0, :5, :] / 10
    good_pr[1, 5:, :] = good_pr[1, 5:, :] / 10

    pattern = "010"
    labels = []
    pred_probs = []
    error = []
    for case in pattern:
        labels.append(good_gt if case == "0" else bad_gt)
        pred_probs.append(good_pr)
        error.append(int(case))

    return np.array(labels).astype(int), np.array(pred_probs).astype(float), error


def _run_segmentation(display: bool) -> Dict[str, Any]:
    from cleanlab.segmentation.filter import find_label_issues
    from cleanlab.segmentation.rank import get_label_quality_scores, issues_from_scores
    from cleanlab.segmentation.summary import display_issues, filter_by_class

    labels, pred_probs, error = _make_segmentation_fixture()
    issues = find_label_issues(
        labels,
        pred_probs,
        downsample=1,
        batch_size=1000,
        n_jobs=1,
        verbose=False,
    )
    issue_counts = issues.sum(axis=(1, 2))
    assert int(np.argmax(issue_counts)) == int(np.argmax(error)) == 1

    image_scores, pixel_scores = get_label_quality_scores(labels, pred_probs, verbose=False)
    assert image_scores.shape == (3,)
    assert pixel_scores.shape == labels.shape
    assert int(np.argmin(image_scores)) == 1

    threshold_mask = issues_from_scores(image_scores, pixel_scores, threshold=0.5)
    assert threshold_mask.shape == labels.shape
    class_issues = filter_by_class(0, issues, labels, pred_probs)
    assert class_issues.shape == labels.shape

    if display:
        display_issues(
            issues,
            labels=labels,
            pred_probs=pred_probs,
            class_names=["class_0", "class_1"],
            top=1,
        )

    return {
        "issue_counts": [int(x) for x in issue_counts.tolist()],
        "lowest_image_score_index": int(np.argmin(image_scores)),
        "threshold_issue_counts": [int(x) for x in threshold_mask.sum(axis=(1, 2)).tolist()],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-display",
        action="store_true",
        help="Skip matplotlib-backed display/visualization helper checks.",
    )
    parser.add_argument(
        "--require-display",
        action="store_true",
        help="Fail if matplotlib-backed display checks cannot run.",
    )
    args = parser.parse_args()

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    display = _prepare_matplotlib(enable=not args.skip_display, require=args.require_display)

    result = {
        "display_checks": bool(display),
        "token_classification": _run_token_classification(display),
        "object_detection": _run_object_detection(display),
        "segmentation": _run_segmentation(display),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
