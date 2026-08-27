#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np

from boxmot.trackers.bbox.bytetrack import ByteTrack
from boxmot.trackers.bbox.occluboost import OccluBoost


@dataclass(frozen=True, slots=True)
class SmokeCase:
    name: str
    shape: tuple[int, ...]
    supports_obb: bool
    rows: int
    columns: int


_DEF_IMG = np.zeros((64, 64, 3), dtype=np.uint8)
_AABB_DETS = np.array(
    [
        [10.0, 12.0, 28.0, 36.0, 0.95, 0.0],
        [34.0, 20.0, 52.0, 44.0, 0.90, 1.0],
    ],
    dtype=np.float32,
)
_OBB_DETS = np.array(
    [
        [20.0, 18.0, 16.0, 10.0, 0.15, 0.95, 0.0],
        [42.0, 38.0, 18.0, 12.0, -0.35, 0.90, 1.0],
    ],
    dtype=np.float32,
)


def _fresh_tracker(name: str):
    key = name.lower()
    if key == "bytetrack":
        return ByteTrack(track_thresh=0.1, min_conf=0.01, match_thresh=0.99, min_hits=1)
    if key == "occluboost":
        return OccluBoost(reid_model=None, with_reid=False, use_cmc=False, min_hits=1)
    raise ValueError(f"Unsupported smoke tracker: {name}")


def _run_case(name: str, dets: np.ndarray, tracker_name: str) -> SmokeCase:
    tracker = _fresh_tracker(tracker_name)
    tracker.update(dets, _DEF_IMG)
    output = tracker.update(dets, _DEF_IMG)
    return SmokeCase(
        name=f"{tracker_name}:{name}",
        shape=tuple(int(dim) for dim in output.shape),
        supports_obb=bool(getattr(tracker, "supports_obb", False)),
        rows=int(output.shape[0]),
        columns=int(output.shape[1]) if output.ndim == 2 else 0,
    )


def _cases_for_mode(mode: str) -> Iterable[tuple[str, np.ndarray, str]]:
    if mode in {"aabb", "both"}:
        yield ("aabb", _AABB_DETS, "bytetrack")
        yield ("aabb", _AABB_DETS, "occluboost")
    if mode in {"obb", "both"}:
        yield ("obb", _OBB_DETS, "bytetrack")
        yield ("obb", _OBB_DETS, "occluboost")


def build_summary(mode: str) -> dict[str, object]:
    cases = [asdict(_run_case(case_name, dets, tracker_name)) for case_name, dets, tracker_name in _cases_for_mode(mode)]
    return {
        "mode": mode,
        "cases": cases,
        "expected_schemas": {
            "aabb": ["x1", "y1", "x2", "y2", "id", "conf", "cls", "det_ind"],
            "obb": ["cx", "cy", "w", "h", "angle", "id", "conf", "cls", "det_ind"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run tiny BoxMOT tracker contract smoke checks.")
    parser.add_argument("--mode", choices=("aabb", "obb", "both"), default="both")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of text.")
    args = parser.parse_args()

    summary = build_summary(args.mode)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"mode: {summary['mode']}")
        for case in summary["cases"]:
            print(f"- {case['name']}: shape={tuple(case['shape'])} supports_obb={case['supports_obb']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
