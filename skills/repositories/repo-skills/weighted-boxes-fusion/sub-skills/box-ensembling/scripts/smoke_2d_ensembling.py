#!/usr/bin/env python3
"""Deterministic smoke checks for 2D box ensembling helpers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from copy import deepcopy

import numpy as np


@dataclass(frozen=True)
class EnsembleCase:
    boxes_list: list
    scores_list: list
    labels_list: list
    weights: list


def load_api():
    """Import the package lazily so --help works without runtime deps."""
    try:
        from ensemble_boxes import (
            nms,
            nms_method,
            non_maximum_weighted,
            soft_nms,
            weighted_boxes_fusion,
            weighted_boxes_fusion_experimental,
        )
    except Exception as exc:  # pragma: no cover - import-time environment guard
        raise SystemExit(
            "Unable to import ensemble_boxes. Install the package and its runtime dependencies before running this smoke script."
        ) from exc
    return {
        "nms": nms,
        "nms_method": nms_method,
        "non_maximum_weighted": non_maximum_weighted,
        "soft_nms": soft_nms,
        "weighted_boxes_fusion": weighted_boxes_fusion,
        "weighted_boxes_fusion_experimental": weighted_boxes_fusion_experimental,
    }


def normalize_xyxy(boxes_px, width, height):
    boxes = np.asarray(boxes_px, dtype=np.float32).copy()
    boxes[:, [0, 2]] /= float(width)
    boxes[:, [1, 3]] /= float(height)
    boxes[:, [0, 2]] = np.sort(boxes[:, [0, 2]], axis=1)
    boxes[:, [1, 3]] = np.sort(boxes[:, [1, 3]], axis=1)
    np.clip(boxes, 0.0, 1.0, out=boxes)
    return boxes


def assert_contract(boxes, scores, labels):
    assert boxes.ndim == 2 and boxes.shape[1] == 4, boxes.shape
    assert scores.ndim == 1 and labels.ndim == 1, (scores.shape, labels.shape)
    assert len(boxes) == len(scores) == len(labels), (len(boxes), len(scores), len(labels))
    assert np.all(boxes >= -1e-8) and np.all(boxes <= 1 + 1e-8), boxes
    assert np.all(np.diff(scores) <= 1e-8), scores


def repeated_single_model_case():
    return EnsembleCase(
        boxes_list=[
            [
                [0.10, 0.10, 0.40, 0.40],
                [0.10, 0.10, 0.40, 0.40],
                [0.10, 0.10, 0.40, 0.40],
            ],
            [],
        ],
        scores_list=[
            [0.90, 0.80, 0.70],
            [],
        ],
        labels_list=[
            [1, 1, 1],
            [],
        ],
        weights=[1.0, 1.0],
    )


def mixed_normalized_case():
    return EnsembleCase(
        boxes_list=[
            [
                [0.00, 0.10, 1.00, 0.90],
            ],
            [
                [0.00, 0.10, 1.00, 0.90],
            ],
        ],
        scores_list=[
            [0.95],
            [0.75],
        ],
        labels_list=[
            [3],
            [3],
        ],
        weights=[2.0, 1.0],
    )


def suppression_case():
    return EnsembleCase(
        boxes_list=[
            [],
            [
                [0.10, 0.10, 0.20, 0.20],
                [0.70, 0.70, 0.80, 0.80],
            ],
        ],
        scores_list=[
            [],
            [0.90, 0.80],
        ],
        labels_list=[
            [],
            [4, 4],
        ],
        weights=[1.0, 1.0],
    )


def smoke_repeated_boxes_and_overflow(api):
    case = repeated_single_model_case()
    wbf = api["weighted_boxes_fusion"]
    boxes_avg, scores_avg, labels_avg = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.2,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=False,
    )
    boxes_over, scores_over, labels_over = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.2,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=True,
    )
    boxes_box_model, scores_box_model, labels_box_model = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.2,
        skip_box_thr=0.0,
        conf_type="box_and_model_avg",
        allows_overflow=False,
    )
    boxes_absent, scores_absent, labels_absent = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.2,
        skip_box_thr=0.0,
        conf_type="absent_model_aware_avg",
        allows_overflow=False,
    )
    boxes_max, scores_max, labels_max = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.2,
        skip_box_thr=0.0,
        conf_type="max",
        allows_overflow=False,
    )

    expected_box = np.array([[0.10, 0.10, 0.40, 0.40]], dtype=np.float32)
    np.testing.assert_allclose(boxes_avg, expected_box)
    np.testing.assert_allclose(boxes_over, expected_box)
    np.testing.assert_allclose(boxes_box_model, expected_box)
    np.testing.assert_allclose(boxes_absent, expected_box)
    np.testing.assert_allclose(boxes_max, expected_box)
    np.testing.assert_array_equal(labels_avg, [1])
    np.testing.assert_array_equal(labels_over, [1])
    np.testing.assert_array_equal(labels_box_model, [1])
    np.testing.assert_array_equal(labels_absent, [1])
    np.testing.assert_array_equal(labels_max, [1])
    np.testing.assert_allclose(scores_avg, [0.80])
    np.testing.assert_allclose(scores_over, [1.20])
    np.testing.assert_allclose(scores_box_model, [0.40])
    np.testing.assert_allclose(scores_absent, [0.60])
    np.testing.assert_allclose(scores_max, [0.90])


def smoke_normalization_and_weight_reset(api):
    case = mixed_normalized_case()
    wbf = api["weighted_boxes_fusion"]
    wbf_experimental = api["weighted_boxes_fusion_experimental"]
    boxes_unweighted, scores_unweighted, labels_unweighted = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=None,
        iou_thr=0.5,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=False,
    )
    boxes_weighted, scores_weighted, labels_weighted = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.5,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=False,
    )
    boxes_reset, scores_reset, labels_reset = wbf(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=[9.0],
        iou_thr=0.5,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=False,
    )
    boxes_experimental, scores_experimental, labels_experimental = wbf_experimental(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.5,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=False,
        skip_checks=False,
    )

    np.testing.assert_allclose(boxes_unweighted, boxes_reset)
    np.testing.assert_allclose(scores_unweighted, scores_reset)
    np.testing.assert_array_equal(labels_unweighted, labels_reset)
    np.testing.assert_allclose(boxes_weighted, boxes_experimental, atol=2e-3, rtol=1e-3)
    np.testing.assert_allclose(scores_weighted, scores_experimental, atol=2e-3, rtol=1e-3)
    np.testing.assert_array_equal(labels_weighted, labels_experimental)
    assert_contract(boxes_unweighted, scores_unweighted, labels_unweighted)
    assert_contract(boxes_weighted, scores_weighted, labels_weighted)

    raw_boxes = np.array(
        [
            [-10.0, 20.0, 210.0, 180.0],
            [150.0, 160.0, 120.0, 140.0],
        ],
        dtype=np.float32,
    )
    normalized = normalize_xyxy(raw_boxes, width=200, height=200)
    np.testing.assert_allclose(normalized[0], [0.0, 0.10, 1.0, 0.90])
    np.testing.assert_allclose(normalized[1], [0.60, 0.70, 0.75, 0.80])
    assert np.all(normalized >= 0.0) and np.all(normalized <= 1.0)


def smoke_suppression_paths(api):
    case = suppression_case()
    nms_method = api["nms_method"]
    nms = api["nms"]
    soft_nms = api["soft_nms"]
    non_maximum_weighted = api["non_maximum_weighted"]

    boxes_nms_method, scores_nms_method, labels_nms_method = nms_method(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        method=3,
        iou_thr=0.5,
        sigma=0.5,
        thresh=0.001,
        weights=case.weights,
    )
    boxes_nms, scores_nms, labels_nms = nms(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        iou_thr=0.5,
        weights=case.weights,
    )
    boxes_soft, scores_soft, labels_soft = soft_nms(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        method=2,
        iou_thr=0.5,
        sigma=0.5,
        thresh=0.001,
        weights=case.weights,
    )
    boxes_nmw, scores_nmw, labels_nmw = non_maximum_weighted(
        deepcopy(case.boxes_list),
        deepcopy(case.scores_list),
        deepcopy(case.labels_list),
        weights=case.weights,
        iou_thr=0.5,
        skip_box_thr=0.0,
    )

    np.testing.assert_allclose(boxes_nms_method, boxes_nms)
    np.testing.assert_allclose(scores_nms_method, scores_nms)
    np.testing.assert_array_equal(labels_nms_method, labels_nms)
    np.testing.assert_allclose(boxes_nmw, np.array(case.boxes_list[1], dtype=np.float32))
    np.testing.assert_array_equal(labels_nmw, np.array(case.labels_list[1], dtype=np.float32))
    assert boxes_soft.shape[1] == 4
    assert scores_soft.ndim == 1 and labels_soft.ndim == 1
    assert_contract(boxes_nms, scores_nms, labels_nms)
    assert_contract(boxes_soft, scores_soft, labels_soft)
    assert_contract(boxes_nmw, scores_nmw, labels_nmw)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=("all", "overflow", "normalize", "suppress"),
        default="all",
        help="Select which deterministic smoke case to run.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    api = load_api()
    if args.case in ("all", "overflow"):
        smoke_repeated_boxes_and_overflow(api)
    if args.case in ("all", "normalize"):
        smoke_normalization_and_weight_reset(api)
    if args.case in ("all", "suppress"):
        smoke_suppression_paths(api)
    print("smoke_2d_ensembling: all requested checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
