#!/usr/bin/env python3
"""Print a compact summary of a UniAD results pickle.

The summary is intentionally shallow: key names, container sizes, and tensor / 
array shapes only. It is meant for local trusted pickles that were produced by
UniAD evaluation or a compatible mmcv dump.
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Any, Iterable

# Avoid importing heavy ML modules unless pickle loading itself needs them.


FEATURE_GROUPS = {
    "tracking": ["boxes_3d", "scores_3d", "labels_3d"],
    "motion": ["traj", "traj_scores"],
    "map": ["pts_bbox", "pts_bbox.lane_score", "pts_bbox.score_list", "pts_bbox.lane"],
    "planning": ["planning_traj", "command"],
    "occ": ["occ", "occ.seg_gt", "occ.ins_seg_gt", "occ.seg_out", "occ.ins_seg_out"],
}


def load_pickle(path: Path) -> Any:
    with path.open("rb") as handle:
        return pickle.load(handle)


def short_list(items: Iterable[Any], max_items: int) -> str:
    seq = list(items)
    preview = ", ".join(str(item) for item in seq[:max_items])
    if len(seq) > max_items:
        preview += ", ..."
    return preview


def describe_value(value: Any, max_items: int = 6) -> str:
    module_name = type(value).__module__
    if module_name.startswith("torch") and hasattr(value, "shape"):
        return (
            f"Tensor(shape={tuple(value.shape)}, "
            f"dtype={getattr(value, 'dtype', '<unknown>')}, "
            f"device={getattr(value, 'device', '<unknown>')})"
        )
    if module_name.startswith("numpy") and hasattr(value, "shape"):
        return f"ndarray(shape={value.shape}, dtype={getattr(value, 'dtype', '<unknown>')})"
    if isinstance(value, dict):
        return f"dict(len={len(value)}, keys=[{short_list(value.keys(), max_items)}])"
    if isinstance(value, (list, tuple)):
        item_types = [type(item).__name__ for item in value[:max_items]]
        suffix = ", ..." if len(value) > max_items else ""
        return f"{type(value).__name__}(len={len(value)}, item_types={item_types}{suffix})"
    tensor = getattr(value, "tensor", None)
    if tensor is not None and hasattr(tensor, "shape"):
        return (
            f"{type(value).__name__}(tensor_shape={tuple(tensor.shape)}, "
            f"tensor_dtype={getattr(tensor, 'dtype', '<unknown>')}, "
            f"tensor_device={getattr(tensor, 'device', '<unknown>')})"
        )
    shape = getattr(value, "shape", None)
    if shape is not None:
        try:
            shape = tuple(shape)
        except Exception:
            shape = str(shape)
        return f"{type(value).__name__}(shape={shape})"
    return type(value).__name__


def has_path(obj: Any, path: str) -> bool:
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return False
            current = current[part]
        else:
            return False
    return True


def get_path(obj: Any, path: str) -> Any:
    current = obj
    for part in path.split("."):
        current = current[part]
    return current


def feature_state(sample: dict[str, Any], paths: list[str]) -> bool:
    return all(has_path(sample, path) for path in paths)


def summarize_sample(sample: dict[str, Any], index: int, max_keys: int, max_items: int) -> list[str]:
    lines: list[str] = []
    token = sample.get("token", "<missing>")
    keys = list(sample.keys())
    lines.append(f"[{index}] token={token}")
    lines.append(f"    keys=[{short_list(keys, max_keys)}]")

    for name, paths in FEATURE_GROUPS.items():
        lines.append(f"    {name}: {'yes' if feature_state(sample, paths) else 'no'}")

    for key in (
        "boxes_3d",
        "scores_3d",
        "labels_3d",
        "track_scores",
        "bbox_index",
        "track_ids",
        "traj",
        "traj_scores",
        "sdc_boxes_3d",
        "sdc_scores_3d",
        "sdc_track_scores",
        "track_bbox_results",
        "planning_traj",
        "planning_traj_gt",
        "command",
    ):
        if key in sample:
            lines.append(f"    {key}: {describe_value(sample[key], max_items=max_items)}")

    for nested in ("pts_bbox", "occ", "planning"):
        if nested in sample and isinstance(sample[nested], dict):
            nested_keys = list(sample[nested].keys())
            lines.append(f"    {nested}.keys=[{short_list(nested_keys, max_keys)}]")
            for nested_key in ("lane", "lane_score", "score_list", "drivable", "seg_out", "ins_seg_out"):
                path = f"{nested}.{nested_key}"
                if has_path(sample, path):
                    lines.append(f"    {path}: {describe_value(get_path(sample, path), max_items=max_items)}")

    return lines


def summarize_result(obj: Any, sample_limit: int, max_keys: int, max_items: int) -> str:
    lines: list[str] = []
    lines.append(f"Top-level type: {type(obj).__name__}")

    if isinstance(obj, dict):
        top_keys = list(obj.keys())
        lines.append(f"Top-level keys: [{short_list(top_keys, max_keys)}]")

        bbox_results = obj.get("bbox_results")
        if isinstance(bbox_results, list):
            lines.append(f"bbox_results: list(len={len(bbox_results)})")
            sample_count = min(sample_limit, len(bbox_results))
            if sample_count:
                lines.append(f"Sample summaries (first {sample_count}):")
                for i in range(sample_count):
                    sample = bbox_results[i]
                    if isinstance(sample, dict):
                        lines.extend(summarize_sample(sample, i, max_keys=max_keys, max_items=max_items))
                    else:
                        lines.append(f"[{i}] {describe_value(sample, max_items=max_items)}")

                lines.append("Feature presence across inspected samples:")
                for name, paths in FEATURE_GROUPS.items():
                    present = 0
                    for i in range(sample_count):
                        sample = bbox_results[i]
                        if isinstance(sample, dict) and feature_state(sample, paths):
                            present += 1
                    lines.append(f"  {name}: {present}/{sample_count}")
        elif bbox_results is not None:
            lines.append(f"bbox_results: {describe_value(bbox_results, max_items=max_items)}")
    else:
        lines.append(f"Preview: {describe_value(obj, max_items=max_items)}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize the key structure of a UniAD results pickle."
    )
    parser.add_argument("pickle_path", help="Path to the results pickle to inspect.")
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=3,
        help="Number of bbox_results entries to summarize.",
    )
    parser.add_argument(
        "--max-keys",
        type=int,
        default=8,
        help="Maximum number of keys to print from a dictionary.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=6,
        help="Maximum number of item types to show for sequences.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.pickle_path)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        obj = load_pickle(path)
    except Exception as exc:  # pragma: no cover - runtime dependent
        print(f"error: failed to load pickle: {exc}", file=sys.stderr)
        return 1

    print(summarize_result(obj, args.sample_limit, args.max_keys, args.max_items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
