#!/usr/bin/env python3
"""Quick Norfair environment checker for this generated repo skill.

Run this helper from any working directory to confirm the active Python can
import the relevant Norfair surfaces. It performs only tiny, deterministic
checks and never downloads models or opens a GUI window.
"""
from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict

import numpy as np


def safe_version(dist_name: str) -> str | None:
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return None


def check_core() -> Dict[str, Any]:
    from norfair import Detection, Tracker

    tracker = Tracker("euclidean", distance_threshold=5, initialization_delay=0)
    tracked_objects = tracker.update([Detection(np.array([[1.0, 1.0]], dtype=float))])
    return {
        "distribution": "norfair",
        "version": safe_version("norfair"),
        "tracked_objects": len(tracked_objects),
        "current_object_count": tracker.current_object_count,
        "total_object_count": tracker.total_object_count,
    }


def check_video() -> Dict[str, Any]:
    from norfair import Video
    from norfair.camera_motion import MotionEstimator, TranslationTransformationGetter
    from norfair.drawing import Paths, draw_boxes, draw_points

    return {
        "distribution": "opencv-backed video",
        "version": safe_version("opencv-python"),
        "symbols": [
            Video.__name__,
            draw_points.__name__,
            draw_boxes.__name__,
            Paths.__name__,
            MotionEstimator.__name__,
            TranslationTransformationGetter.__name__,
        ],
    }


def check_metrics() -> Dict[str, Any]:
    from norfair import metrics

    matrix = np.array([[1, 1, 1, 2, 3, 4, 0.9, 1, 1, 0]], dtype=float)
    df = metrics.load_motchallenge(matrix)
    return {
        "distribution": "motmetrics",
        "norfair_version": safe_version("norfair"),
        "motmetrics_version": safe_version("motmetrics"),
        "pandas_version": safe_version("pandas"),
        "rows": int(len(df)),
        "columns": list(df.columns),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny Norfair environment checks for the generated repo skill."
    )
    parser.add_argument("--core", action="store_true", help="Check the core tracking import and a tiny tracker update.")
    parser.add_argument("--video", action="store_true", help="Check the OpenCV-backed video and drawing imports.")
    parser.add_argument("--metrics", action="store_true", help="Check the MOTChallenge metrics imports and parser.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    return parser


def run_step(name: str, checker, recovery: str) -> Dict[str, Any]:
    try:
        return checker()
    except Exception as exc:  # pragma: no cover - helper error path
        raise RuntimeError(f"{name} check failed: {exc}. {recovery}") from exc


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    requested = [flag for flag in ("core", "video", "metrics") if getattr(args, flag)]
    if not requested:
        requested = ["core", "video", "metrics"]

    results: Dict[str, Any] = {}
    try:
        if "core" in requested:
            results["core"] = run_step(
                "core",
                check_core,
                "Install Norfair itself and retry, for example `pip install norfair`.",
            )
        if "video" in requested:
            results["video"] = run_step(
                "video",
                check_video,
                "Install OpenCV-backed video support, for example `pip install norfair[video]`.",
            )
        if "metrics" in requested:
            results["metrics"] = run_step(
                "metrics",
                check_metrics,
                "Install MOTChallenge metrics support, for example `pip install norfair[metrics]`.",
            )
    except Exception as exc:
        print(f"Norfair environment check failed: {exc}")
        return 1

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for name, payload in results.items():
            print(f"[{name}] {json.dumps(payload, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
