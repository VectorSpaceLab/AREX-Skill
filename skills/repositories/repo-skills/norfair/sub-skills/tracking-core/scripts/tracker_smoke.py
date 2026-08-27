#!/usr/bin/env python3
"""Tiny Norfair core tracking smoke test.

This script exercises the core tracker loop without drawing or video output.
It checks:
- point wrapping with validate_points
- label-aware tracking
- skipped frames with period handling
- object counters
- get_cutout
- the NaN guard on custom distances
"""
from __future__ import annotations

import argparse
import json
from typing import List

import numpy as np


def load_api():
    try:
        from norfair.tracker import Detection, Tracker
        from norfair.filter import NoFilterFactory, OptimizedKalmanFilterFactory
        from norfair.utils import get_cutout, print_objects_as_table, validate_points
    except Exception as exc:  # pragma: no cover - smoke helper
        raise SystemExit(
            "Norfair core imports failed. Install the tracking dependencies and retry."
        ) from exc

    return Detection, Tracker, NoFilterFactory, OptimizedKalmanFilterFactory, get_cutout, print_objects_as_table, validate_points


def make_detection(Detection, x: float, y: float, label: str) -> object:
    return Detection(
        points=np.array([x, y], dtype=float),
        scores=np.array([1.0], dtype=float),
        label=label,
    )


def snapshot(objects: List[object]) -> list[dict]:
    rows = []
    for obj in objects:
        rows.append(
            {
                "label": obj.label,
                "id": obj.id,
                "age": obj.age,
                "hit_counter": obj.hit_counter,
                "last_distance": None if obj.last_distance is None else round(float(obj.last_distance), 4),
            }
        )
    return rows


def run_smoke(filter_kind: str = "optimized") -> dict:
    Detection, Tracker, NoFilterFactory, OptimizedKalmanFilterFactory, get_cutout, print_objects_as_table, validate_points = load_api()

    filter_factory = (
        NoFilterFactory() if filter_kind == "no-filter" else OptimizedKalmanFilterFactory()
    )

    tracker = Tracker(
        distance_function="euclidean",
        distance_threshold=20,
        hit_counter_max=5,
        initialization_delay=0,
        pointwise_hit_counter_max=2,
        filter_factory=filter_factory,
        past_detections_length=2,
    )

    # Frame 0: birth.
    tracked = tracker.update(
        [
            make_detection(Detection, 20, 20, "target"),
            make_detection(Detection, 80, 20, "other"),
        ]
    )
    assert len(tracked) == 2
    target_id = next(obj.id for obj in tracked if obj.label == "target")
    other_id = next(obj.id for obj in tracked if obj.label == "other")

    # Frame 1: confirmation and stable IDs.
    tracked = tracker.update(
        [
            make_detection(Detection, 21, 20, "target"),
            make_detection(Detection, 81, 20, "other"),
        ]
    )
    assert len(tracked) == 2
    assert next(obj.id for obj in tracked if obj.label == "target") == target_id
    assert next(obj.id for obj in tracked if obj.label == "other") == other_id

    # Print a table only after last_distance has been populated.
    print_objects_as_table(tracked)

    # Skip two frames, then update with period=3 to simulate detector skipping.
    tracker.update()
    tracker.update()
    tracked = tracker.update(
        [
            make_detection(Detection, 24, 20, "target"),
            make_detection(Detection, 84, 20, "other"),
        ],
        period=3,
    )
    assert len(tracked) == 2
    assert next(obj.id for obj in tracked if obj.label == "target") == target_id
    assert next(obj.id for obj in tracked if obj.label == "other") == other_id

    # Smoke-check point wrapping and image cutouts.
    wrapped = validate_points(np.array([9.0, 8.0], dtype=float))
    assert wrapped.shape == (1, 2)

    image = np.arange(40 * 60 * 3, dtype=np.uint8).reshape(40, 60, 3)
    cutout = get_cutout(np.array([[4.0, 5.0], [9.0, 12.0]], dtype=float), image)
    assert cutout.shape[:2] == (7, 5)

    # NaN guard: the tracker should fail fast.
    def nan_distance(detection, tracked_object):
        if detection.data and detection.data.get("nan"):
            return np.nan
        return float(np.linalg.norm(detection.points - tracked_object.estimate))

    nan_tracker = Tracker(
        distance_function=nan_distance,
        distance_threshold=5,
        hit_counter_max=2,
        initialization_delay=0,
        filter_factory=filter_factory,
    )
    nan_tracker.update(
        [Detection(points=np.array([0.0, 0.0]), scores=np.array([1.0]), label="nan")]
    )
    try:
        nan_tracker.update(
            [
                Detection(
                    points=np.array([1.0, 0.0]),
                    scores=np.array([1.0]),
                    label="nan",
                    data={"nan": True},
                )
            ]
        )
    except ValueError as exc:
        assert "nan values" in str(exc).lower()
    else:  # pragma: no cover - smoke helper
        raise AssertionError("Expected tracker NaN guard to raise ValueError")

    return {
        "filter_kind": filter_kind,
        "target_id": target_id,
        "other_id": other_id,
        "current_object_count": tracker.current_object_count,
        "total_object_count": tracker.total_object_count,
        "snapshot": snapshot(tracked),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filter",
        choices=("optimized", "no-filter"),
        default="optimized",
        help="Choose the tracker filter factory to smoke-test.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the final smoke summary as JSON only.",
    )
    args = parser.parse_args()

    summary = run_smoke(args.filter)
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
