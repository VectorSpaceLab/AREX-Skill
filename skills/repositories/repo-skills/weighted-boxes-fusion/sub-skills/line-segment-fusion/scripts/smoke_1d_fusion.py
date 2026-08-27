#!/usr/bin/env python3
"""Deterministic smoke tests for weighted_boxes_fusion_1d.

This script exercises the normalized 1D span path, the NER-style
predictionstring round-trip, and the accepted confidence modes.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from typing import Any, Dict, List, Optional


def load_wbf_1d():
    try:
        from ensemble_boxes import weighted_boxes_fusion_1d
    except Exception as exc:  # pragma: no cover - import failure is surfaced to the caller
        raise SystemExit(f"Unable to import ensemble_boxes.weighted_boxes_fusion_1d: {exc}") from exc
    return weighted_boxes_fusion_1d


def assert_basic_modes() -> Dict[str, Any]:
    import numpy as np

    weighted_boxes_fusion_1d = load_wbf_1d()

    boxes_list = [
        [[0.10, 0.30]],
        [[0.20, 0.40]],
    ]
    scores_list = [[0.90], [0.60]]
    labels_list = [[0], [0]]
    weights = [2, 1]
    expected_box = np.array([[0.125, 0.325]], dtype=float)
    expected_scores = {
        "avg": 0.80,
        "box_and_model_avg": 0.80,
        "absent_model_aware_avg": 0.80,
        "max": 0.90,
    }

    results: Dict[str, Any] = {}
    for conf_type, expected_score in expected_scores.items():
        boxes, scores, labels = weighted_boxes_fusion_1d(
            deepcopy(boxes_list),
            deepcopy(scores_list),
            deepcopy(labels_list),
            weights=weights,
            iou_thr=0.25,
            skip_box_thr=0.0,
            conf_type=conf_type,
            allows_overflow=False,
        )
        boxes = np.asarray(boxes, dtype=float)
        scores = np.asarray(scores, dtype=float)
        labels = np.asarray(labels, dtype=int)

        np.testing.assert_allclose(boxes, expected_box, rtol=0.0, atol=1e-7)
        np.testing.assert_allclose(scores, np.array([expected_score], dtype=float), rtol=0.0, atol=1e-7)
        np.testing.assert_array_equal(labels, np.array([0], dtype=int))

        results[conf_type] = {
            "boxes": boxes.tolist(),
            "scores": scores.tolist(),
            "labels": labels.tolist(),
        }

    return results


def predictionstring_to_box(predictionstring: str, max_box_value: int) -> List[float]:
    tokens = [int(token) for token in predictionstring.split()]
    if not tokens:
        raise ValueError("predictionstring must not be empty")
    start = min(tokens)
    end = max(tokens)
    return [start / max_box_value, end / max_box_value]


def assert_ner_round_trip() -> Dict[str, Any]:
    import numpy as np

    weighted_boxes_fusion_1d = load_wbf_1d()

    class_to_label = {"Claim": 0, "Evidence": 1}
    label_to_class = {v: k for k, v in class_to_label.items()}
    max_box_value = 10

    raw_predictions = [
        [
            ("Claim", 0.91, "2 3 4"),
            ("Evidence", 0.74, "6 7 8"),
            ("Claim", 0.01, "0"),
        ],
        [
            ("Claim", 0.83, "2 3 4"),
            ("Evidence", 0.72, "6 7 8"),
        ],
    ]

    boxes_list = []
    scores_list = []
    labels_list = []
    for model_predictions in raw_predictions:
        model_boxes = []
        model_scores = []
        model_labels = []
        for label_name, score, predictionstring in model_predictions:
            model_boxes.append(predictionstring_to_box(predictionstring, max_box_value))
            model_scores.append(score)
            model_labels.append(class_to_label[label_name])
        boxes_list.append(model_boxes)
        scores_list.append(model_scores)
        labels_list.append(model_labels)

    boxes, scores, labels = weighted_boxes_fusion_1d(
        deepcopy(boxes_list),
        deepcopy(scores_list),
        deepcopy(labels_list),
        weights=[1, 1],
        iou_thr=0.50,
        skip_box_thr=0.05,
        conf_type="avg",
        allows_overflow=False,
    )
    boxes = np.asarray(boxes, dtype=float)
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=int)

    assert len(boxes) == 2, f"expected 2 fused spans, got {len(boxes)}"

    fused = []
    for box, score, label in zip(boxes, scores, labels):
        start = math.ceil(float(box[0]) * max_box_value)
        end = int(float(box[1]) * max_box_value)
        predictionstring = " ".join(str(token) for token in range(start, end + 1))
        fused.append((label_to_class[int(label)], round(float(score), 2), predictionstring))

    fused.sort()
    expected = [
        ("Claim", 0.87, "2 3"),
        ("Evidence", 0.73, "6 7 8"),
    ]
    assert fused == expected, f"unexpected fused rows: {fused!r}"

    return {
        "rows": fused,
        "count": len(fused),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test weighted_boxes_fusion_1d with deterministic span and NER round-trip cases.",
    )
    parser.add_argument(
        "--case",
        choices=("all", "basic", "ner"),
        default="all",
        help="Which deterministic smoke case to run.",
    )
    args = parser.parse_args(argv)

    summary: Dict[str, Any] = {}
    if args.case in ("all", "basic"):
        summary["basic"] = assert_basic_modes()
    if args.case in ("all", "ner"):
        summary["ner"] = assert_ner_round_trip()

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
