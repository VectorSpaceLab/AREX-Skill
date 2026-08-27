#!/usr/bin/env python3
"""Smoke checks for weighted_boxes_fusion_3d.

The script is GUI-free, network-free, and deterministic.
It assumes the boxes you feed into WBF are already normalized to [0, 1].
If you start from metric LiDAR, MRI, CT, or other volumetric coordinates,
normalize each axis to a shared scene range first and keep x/y/z ordering
unchanged.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import warnings
from copy import deepcopy
from typing import Iterable, Sequence

import numpy as np
from ensemble_boxes import weighted_boxes_fusion_3d


def _normalize_box(box: Sequence[float], axis_min: Sequence[float], axis_max: Sequence[float]) -> np.ndarray:
    """Apply a simple per-axis affine normalization to a 3D cuboid."""

    box_arr = np.asarray(box, dtype=np.float32)
    mins = np.asarray(axis_min, dtype=np.float32)
    maxs = np.asarray(axis_max, dtype=np.float32)
    spans = maxs - mins

    if box_arr.shape != (6,):
        raise ValueError(f"expected a 6-value box, got shape {box_arr.shape}")
    if mins.shape != (3,) or maxs.shape != (3,):
        raise ValueError("axis_min and axis_max must each have three values")
    if np.any(spans <= 0):
        raise ValueError("each axis_max value must be greater than axis_min")

    normalized = box_arr.copy()
    normalized[:3] = (box_arr[:3] - mins) / spans
    normalized[3:] = (box_arr[3:] - mins) / spans
    return normalized


def _fuse_safely(
    boxes_list: list[list[list[float]]],
    scores_list: list[list[float]],
    labels_list: list[list[int]],
    *,
    conf_type: str,
    weights: Sequence[float] = (1.0, 1.0),
    iou_thr: float = 0.5,
    skip_box_thr: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run WBF while suppressing expected warnings from the smoke cases."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return weighted_boxes_fusion_3d(
            boxes_list,
            scores_list,
            labels_list,
            weights=list(weights),
            iou_thr=iou_thr,
            skip_box_thr=skip_box_thr,
            conf_type=conf_type,
            allows_overflow=False,
        )


def _assert_basic_contract(boxes: np.ndarray, scores: np.ndarray, labels: np.ndarray) -> None:
    assert boxes.ndim == 2 and boxes.shape[1] == 6, boxes.shape
    assert scores.ndim == 1, scores.shape
    assert labels.ndim == 1, labels.shape
    assert len(boxes) == len(scores) == len(labels)


def check_avg_and_max_modes(atol: float) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Exercise normalization, reversed axes, and avg/max confidence modes."""

    axis_min = (0.0, 0.0, 0.0)
    axis_max = (10.0, 10.0, 10.0)

    metric_box = [2.0, 4.0, 6.0, 5.0, 8.0, 9.0]
    reversed_metric_box = [5.0, 8.0, 9.0, 2.0, 4.0, 6.0]
    ordered = _normalize_box(metric_box, axis_min, axis_max)
    reversed_box = _normalize_box(reversed_metric_box, axis_min, axis_max)

    np.testing.assert_allclose(
        ordered,
        np.array([0.2, 0.4, 0.6, 0.5, 0.8, 0.9], dtype=np.float32),
        atol=atol,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        reversed_box,
        np.array([0.5, 0.8, 0.9, 0.2, 0.4, 0.6], dtype=np.float32),
        atol=atol,
        rtol=0.0,
    )

    boxes_list = [[ordered.tolist()], [reversed_box.tolist()]]
    scores_list = [[0.9], [0.8]]
    labels_list = [[7], [7]]

    avg_boxes, avg_scores, avg_labels = _fuse_safely(
        deepcopy(boxes_list),
        deepcopy(scores_list),
        deepcopy(labels_list),
        conf_type="avg",
    )
    max_boxes, max_scores, max_labels = _fuse_safely(
        deepcopy(boxes_list),
        deepcopy(scores_list),
        deepcopy(labels_list),
        conf_type="max",
    )

    _assert_basic_contract(avg_boxes, avg_scores, avg_labels)
    _assert_basic_contract(max_boxes, max_scores, max_labels)

    assert int(avg_labels[0]) == 7
    assert int(max_labels[0]) == 7
    np.testing.assert_allclose(avg_boxes[0], ordered, atol=atol, rtol=0.0)
    np.testing.assert_allclose(max_boxes[0], ordered, atol=atol, rtol=0.0)
    np.testing.assert_allclose(avg_scores[0], 0.85, atol=atol, rtol=0.0)
    np.testing.assert_allclose(max_scores[0], 0.9, atol=atol, rtol=0.0)

    return (avg_boxes, avg_scores, avg_labels), (max_boxes, max_scores, max_labels)


def check_invalid_conf_type_falls_back_to_avg(
    reference_avg: tuple[np.ndarray, np.ndarray, np.ndarray],
    atol: float,
) -> None:
    """Capture the printed fallback message and compare with avg outputs."""

    axis_min = (0.0, 0.0, 0.0)
    axis_max = (10.0, 10.0, 10.0)
    metric_box = [2.0, 4.0, 6.0, 5.0, 8.0, 9.0]
    reversed_metric_box = [5.0, 8.0, 9.0, 2.0, 4.0, 6.0]
    ordered = _normalize_box(metric_box, axis_min, axis_max)
    reversed_box = _normalize_box(reversed_metric_box, axis_min, axis_max)

    np.testing.assert_allclose(
        ordered,
        np.array([0.2, 0.4, 0.6, 0.5, 0.8, 0.9], dtype=np.float32),
        atol=atol,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        reversed_box,
        np.array([0.5, 0.8, 0.9, 0.2, 0.4, 0.6], dtype=np.float32),
        atol=atol,
        rtol=0.0,
    )

    boxes_list = [[ordered.tolist()], [reversed_box.tolist()]]
    scores_list = [[0.9], [0.8]]
    labels_list = [[7], [7]]

    stdout = io.StringIO()
    with warnings.catch_warnings(), contextlib.redirect_stdout(stdout):
        warnings.simplefilter("ignore")
        fallback_boxes, fallback_scores, fallback_labels = weighted_boxes_fusion_3d(
            deepcopy(boxes_list),
            deepcopy(scores_list),
            deepcopy(labels_list),
            weights=[1.0, 1.0],
            iou_thr=0.5,
            skip_box_thr=0.0,
            conf_type="absent_model_aware_avg",
            allows_overflow=False,
        )

    message = stdout.getvalue()
    assert "Unknown conf_type" in message
    assert "Use \"avg\"" in message

    avg_boxes, avg_scores, avg_labels = reference_avg
    np.testing.assert_allclose(fallback_boxes, avg_boxes, atol=atol, rtol=0.0)
    np.testing.assert_allclose(fallback_scores, avg_scores, atol=atol, rtol=0.0)
    np.testing.assert_allclose(fallback_labels, avg_labels, atol=atol, rtol=0.0)


def check_zero_volume_skip() -> None:
    """Confirm that degenerate cuboids are skipped."""

    zero_volume_box = [0.25, 0.35, 0.45, 0.25, 0.55, 0.65]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        boxes, scores, labels = weighted_boxes_fusion_3d(
            deepcopy([[zero_volume_box]]),
            deepcopy([[0.9]]),
            deepcopy([[7]]),
            weights=[1.0],
            iou_thr=0.5,
            skip_box_thr=0.0,
            conf_type="avg",
            allows_overflow=False,
        )

    assert boxes.shape == (0, 6)
    assert scores.shape == (0,)
    assert labels.shape == (0,)


def run_scenario(scenario: str, atol: float) -> None:
    if scenario == "fusion":
        check_avg_and_max_modes(atol)
        print("[ok] avg/max 3D fusion smoke passed")
        return

    if scenario == "fallback":
        reference_avg, _ = check_avg_and_max_modes(atol)
        check_invalid_conf_type_falls_back_to_avg(reference_avg, atol)
        print("[ok] invalid conf_type fallback smoke passed")
        return

    if scenario == "zero-volume":
        check_zero_volume_skip()
        print("[ok] zero-volume skip smoke passed")
        return

    if scenario == "all":
        reference_avg, _ = check_avg_and_max_modes(atol)
        check_invalid_conf_type_falls_back_to_avg(reference_avg, atol)
        check_zero_volume_skip()
        print("[ok] avg/max 3D fusion smoke passed")
        print("[ok] invalid conf_type fallback smoke passed")
        print("[ok] zero-volume skip smoke passed")
        return

    raise ValueError(f"unsupported scenario: {scenario}")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test weighted_boxes_fusion_3d on normalized 3D cuboids.",
    )
    parser.add_argument(
        "--scenario",
        choices=("all", "fusion", "fallback", "zero-volume"),
        default="all",
        help="Select which deterministic smoke scenario to run.",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-6,
        help="Absolute tolerance for floating-point assertions.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    run_scenario(args.scenario, args.atol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
