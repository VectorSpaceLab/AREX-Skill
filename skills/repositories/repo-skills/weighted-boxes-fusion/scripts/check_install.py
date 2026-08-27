#!/usr/bin/env python3
"""Smoke-test the ensemble_boxes installation from any working directory.

This helper is GUI-free, network-free, and deterministic. It exercises tiny
2D, 1D, and 3D in-memory cases so future agents can confirm the package is
usable before opening the geometry-specific sub-skills.
"""

from __future__ import annotations

import argparse
import copy
import json
from typing import Any

import numpy as np


def assert_contract(boxes, scores, labels, expected_dim: int):
    boxes = np.asarray(boxes)
    scores = np.asarray(scores)
    labels = np.asarray(labels)
    assert boxes.ndim == 2 and boxes.shape[1] == expected_dim, boxes.shape
    assert scores.ndim == 1 and labels.ndim == 1, (scores.shape, labels.shape)
    assert len(boxes) == len(scores) == len(labels), (len(boxes), len(scores), len(labels))
    return boxes, scores, labels


def run_exports() -> dict[str, Any]:
    import ensemble_boxes

    exports = sorted(x for x in dir(ensemble_boxes) if not x.startswith("_"))
    return {"module": ensemble_boxes.__name__, "exports": exports}


def run_2d() -> dict[str, Any]:
    from ensemble_boxes import (
        nms,
        nms_method,
        non_maximum_weighted,
        soft_nms,
        weighted_boxes_fusion,
        weighted_boxes_fusion_experimental,
    )

    boxes_list = [
        [[0.10, 0.10, 0.50, 0.50], [0.60, 0.60, 0.80, 0.80]],
        [[0.11, 0.11, 0.51, 0.51], [0.62, 0.62, 0.82, 0.82]],
    ]
    scores_list = [[0.90, 0.70], [0.80, 0.60]]
    labels_list = [[1, 1], [1, 1]]
    weights = [2.0, 1.0]

    outputs = {}
    for name, fn, kwargs, expected_dim in [
        ("wbf", weighted_boxes_fusion, {"weights": weights, "iou_thr": 0.5, "skip_box_thr": 0.0, "conf_type": "avg"}, 4),
        ("wbf_exp", weighted_boxes_fusion_experimental, {"weights": weights, "iou_thr": 0.5, "skip_box_thr": 0.0, "conf_type": "avg", "skip_checks": False}, 4),
        ("nmw", non_maximum_weighted, {"weights": weights, "iou_thr": 0.5, "skip_box_thr": 0.0}, 4),
        ("nms", nms, {"weights": weights, "iou_thr": 0.5}, 4),
        ("soft_nms", soft_nms, {"weights": weights, "iou_thr": 0.5, "sigma": 0.5, "thresh": 0.001}, 4),
    ]:
        boxes, scores, labels = fn(copy.deepcopy(boxes_list), copy.deepcopy(scores_list), copy.deepcopy(labels_list), **kwargs)
        boxes, scores, labels = assert_contract(boxes, scores, labels, expected_dim)
        outputs[name] = {"boxes_shape": list(boxes.shape), "scores_shape": list(scores.shape), "labels": labels.astype(int).tolist()}
    return outputs


def run_1d() -> dict[str, Any]:
    from ensemble_boxes import weighted_boxes_fusion_1d

    boxes, scores, labels = weighted_boxes_fusion_1d(
        copy.deepcopy([[[0.10, 0.30]], [[0.20, 0.40]]]),
        copy.deepcopy([[0.90], [0.60]]),
        copy.deepcopy([[0], [0]]),
        weights=[2.0, 1.0],
        iou_thr=0.25,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=False,
    )
    boxes, scores, labels = assert_contract(boxes, scores, labels, 2)
    np.testing.assert_allclose(boxes, np.array([[0.125, 0.325]], dtype=float), atol=1e-7, rtol=0.0)
    np.testing.assert_allclose(scores, np.array([0.80], dtype=float), atol=1e-7, rtol=0.0)
    np.testing.assert_array_equal(labels, np.array([0], dtype=int))
    return {"boxes_shape": list(boxes.shape), "scores_shape": list(scores.shape), "labels": labels.astype(int).tolist()}


def run_3d() -> dict[str, Any]:
    from ensemble_boxes import weighted_boxes_fusion_3d

    boxes, scores, labels = weighted_boxes_fusion_3d(
        copy.deepcopy([
            [[0.10, 0.10, 0.10, 0.50, 0.50, 0.50]],
            [[0.11, 0.11, 0.11, 0.51, 0.51, 0.51]],
        ]),
        copy.deepcopy([[0.90], [0.80]]),
        copy.deepcopy([[7], [7]]),
        weights=[2.0, 1.0],
        iou_thr=0.5,
        skip_box_thr=0.0,
        conf_type="avg",
        allows_overflow=False,
    )
    boxes, scores, labels = assert_contract(boxes, scores, labels, 6)
    return {"boxes_shape": list(boxes.shape), "scores_shape": list(scores.shape), "labels": labels.astype(int).tolist()}


def run_all() -> dict[str, Any]:
    return {
        "exports": run_exports(),
        "2d": run_2d(),
        "1d": run_1d(),
        "3d": run_3d(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=("all", "exports", "2d", "1d", "3d"),
        default="all",
        help="Select which install smoke case to run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.case == "exports":
        summary = {"exports": run_exports()}
    elif args.case == "2d":
        summary = {"2d": run_2d()}
    elif args.case == "1d":
        summary = {"1d": run_1d()}
    elif args.case == "3d":
        summary = {"3d": run_3d()}
    else:
        summary = run_all()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
