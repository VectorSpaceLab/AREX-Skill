#!/usr/bin/env python3
"""Tiny synthetic ReID smoke test for Norfair tracking core.

The script stays self-contained: it uses NumPy only, does not touch the original
source demo tree, and does not write videos.
"""
from __future__ import annotations

import argparse
import json
from typing import Optional, Sequence, Tuple

import numpy as np


def load_api():
    try:
        from norfair.tracker import Detection, Tracker
        from norfair.filter import OptimizedKalmanFilterFactory
        from norfair.utils import get_cutout
    except Exception as exc:  # pragma: no cover - smoke helper
        raise SystemExit(
            "Norfair core imports failed. Install the tracking dependencies and retry."
        ) from exc

    return Detection, Tracker, OptimizedKalmanFilterFactory, get_cutout


def make_box(
    Detection,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    color,
    label: str = "box",
):
    return Detection(
        points=np.array(
            [
                [xmin, ymin],
                [xmax, ymin],
                [xmin, ymax],
                [xmax, ymax],
            ],
            dtype=float,
        ),
        scores=np.ones(4, dtype=float),
        label=label,
        data={"color": np.asarray(color, dtype=float)},
    )


def latest_embedding(obj) -> Optional[np.ndarray]:
    candidates = [obj.last_detection, *reversed(obj.past_detections)]
    for det in candidates:
        if det is not None and getattr(det, "embedding", None) is not None:
            return np.asarray(det.embedding, dtype=float)
    return None


def render_frame(shape: Tuple[int, int, int], detections: Sequence[object]) -> np.ndarray:
    frame = np.zeros(shape, dtype=float)
    for det in detections:
        xmin = int(np.min(det.points[:, 0]))
        xmax = int(np.max(det.points[:, 0]))
        ymin = int(np.min(det.points[:, 1]))
        ymax = int(np.max(det.points[:, 1]))
        frame[ymin:ymax, xmin:xmax] = det.data["color"]
    return frame


def attach_embedding(get_cutout, frame: np.ndarray, detection: object) -> None:
    cutout = get_cutout(detection.points, frame)
    if cutout.size == 0:
        detection.embedding = None
    else:
        detection.embedding = cutout.reshape(-1, cutout.shape[-1]).mean(axis=0)


def id_by_color(objects: Sequence[object], target_color: np.ndarray) -> Optional[int]:
    for obj in objects:
        emb = latest_embedding(obj)
        if emb is None:
            continue
        if np.linalg.norm(emb - target_color) < 0.15:
            return obj.id
    return None


def run_tracker(Detection, Tracker, OptimizedKalmanFilterFactory, get_cutout, enable_reid: bool = True) -> dict:
    red = np.array([0.9, 0.1, 0.1], dtype=float)
    canvas_shape = (96, 128, 3)
    box_h = 14
    box_w = 12

    def reid_distance(new_obj, old_obj):
        new_emb = latest_embedding(new_obj)
        old_emb = latest_embedding(old_obj)
        if new_emb is None or old_emb is None:
            return 1.0
        return float(np.linalg.norm(new_emb - old_emb))

    tracker = Tracker(
        distance_function="euclidean",
        distance_threshold=20,
        hit_counter_max=2,
        initialization_delay=1,
        filter_factory=OptimizedKalmanFilterFactory(),
        past_detections_length=4,
        reid_distance_function=reid_distance if enable_reid else None,
        reid_distance_threshold=0.15 if enable_reid else 0,
        reid_hit_counter_max=8 if enable_reid else None,
    )

    # The object disappears long enough to become stale, then reappears far away.
    sequence = [12, 16, 20, None, None, 60, 64]
    red_id_history = []

    for xmin in sequence:
        if xmin is None:
            tracked = tracker.update()
        else:
            detection = make_box(
                Detection,
                xmin=xmin,
                ymin=36,
                xmax=xmin + box_w,
                ymax=36 + box_h,
                color=red,
            )
            frame = render_frame(canvas_shape, [detection])
            attach_embedding(get_cutout, frame, detection)
            tracked = tracker.update([detection])
        red_id_history.append(id_by_color(tracked, red))

    return {
        "enable_reid": enable_reid,
        "red_id_history": red_id_history,
        "final_red_id": red_id_history[-1],
        "first_red_id": next(item for item in red_id_history if item is not None),
        "active_count": tracker.current_object_count,
        "total_count": tracker.total_object_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the final smoke summary as JSON only.",
    )
    args = parser.parse_args()

    Detection, Tracker, OptimizedKalmanFilterFactory, get_cutout = load_api()
    with_reid = run_tracker(
        Detection, Tracker, OptimizedKalmanFilterFactory, get_cutout, enable_reid=True
    )
    without_reid = run_tracker(
        Detection, Tracker, OptimizedKalmanFilterFactory, get_cutout, enable_reid=False
    )

    assert with_reid["first_red_id"] == with_reid["final_red_id"]
    assert without_reid["first_red_id"] != without_reid["final_red_id"]

    summary = {
        "with_reid": with_reid,
        "without_reid": without_reid,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
