#!/usr/bin/env python3
"""Safe, no-training checks for Diffusion Planner model-ready inputs.

This helper intentionally uses only the standard library and numpy. It never
imports diffusion_planner, initializes CUDA/DDP, downloads files, or writes
inputs/checkpoints. It validates normalization.json and a bounded sample of the
JSON/.npz data handoff.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - environment diagnostic
    print("ERROR: numpy is required for manifest checks: {}".format(exc), file=sys.stderr)
    raise SystemExit(2)


REQUIRED_KEYS = (
    "ego_current_state",
    "ego_agent_future",
    "neighbor_agents_past",
    "neighbor_agents_future",
    "lanes",
    "lanes_speed_limit",
    "lanes_has_speed_limit",
    "route_lanes",
    "route_lanes_speed_limit",
    "route_lanes_has_speed_limit",
    "static_objects",
)

NORMALIZATION_KEYS = (
    "ego",
    "neighbor",
    "ego_current_state",
    "neighbor_agents_past",
    "static_objects",
    "lanes",
    "lanes_speed_limit",
    "route_lanes",
    "route_lanes_speed_limit",
)

BOOLEAN_KEYS = {
    "lanes_has_speed_limit",
    "route_lanes_has_speed_limit",
}

NORMALIZATION_DIMS = {
    "ego": 4,
    "neighbor": 4,
    "ego_current_state": 10,
    "neighbor_agents_past": 11,
    "static_objects": 10,
    "lanes": 12,
    "lanes_speed_limit": 1,
    "route_lanes": 12,
    "route_lanes_speed_limit": 1,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Diffusion Planner normalization and model-ready .npz contracts without training."
    )
    parser.add_argument("--check-normalization", metavar="JSON", help="validate normalization.json")
    parser.add_argument("--check-manifest", metavar="DATA_DIR", help="validate .npz files under this directory")
    parser.add_argument("--data-list", metavar="JSON", help="JSON filename list used with --check-manifest")
    parser.add_argument("--limit", type=int, default=0, help="check at most N manifest entries (0 means all)")
    parser.add_argument("--predicted-neighbor-num", type=int, default=10)
    parser.add_argument("--future-len", type=int, default=80)
    parser.add_argument("--time-len", type=int, default=21)
    parser.add_argument("--agent-num", type=int, default=32)
    parser.add_argument("--agent-state-dim", type=int, default=11)
    parser.add_argument("--static-objects-num", type=int, default=5)
    parser.add_argument("--static-objects-state-dim", type=int, default=10)
    parser.add_argument("--lane-num", type=int, default=70)
    parser.add_argument("--lane-len", type=int, default=20)
    parser.add_argument("--lane-state-dim", type=int, default=12)
    parser.add_argument("--route-num", type=int, default=25)
    parser.add_argument("--route-len", type=int, default=20)
    parser.add_argument("--route-state-dim", type=int, default=12)
    parser.add_argument("--print-defaults", action="store_true", help="print the default tensor contract and exit")
    return parser


def _positive(name: str, value: int, errors: List[str]) -> None:
    if value <= 0:
        errors.append("{} must be positive, got {}".format(name, value))


def _shape_error(name: str, actual: Sequence[int], expected: Sequence[int], errors: List[str], prefix: str = "") -> None:
    actual_tuple = tuple(int(x) for x in actual)
    expected_tuple = tuple(int(x) for x in expected)
    if actual_tuple != expected_tuple:
        errors.append("{}{} shape {} != expected {}".format(prefix, name, actual_tuple, expected_tuple))


def _at_least_shape(name: str, actual: Sequence[int], expected: Sequence[int], errors: List[str], prefix: str = "") -> None:
    actual_tuple = tuple(int(x) for x in actual)
    expected_tuple = tuple(int(x) for x in expected)
    if len(actual_tuple) != len(expected_tuple) or any(a < e for a, e in zip(actual_tuple, expected_tuple)):
        errors.append("{}{} shape {} is smaller than required {}".format(prefix, name, actual_tuple, expected_tuple))


def _validate_normalization(path: str, predicted_neighbor_num: int) -> List[str]:
    errors: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        return ["normalization file {} could not be read: {}".format(path, exc)]

    if not isinstance(data, dict):
        return ["normalization file must contain a JSON object"]
    for key in NORMALIZATION_KEYS:
        if key not in data:
            errors.append("normalization missing key {!r}".format(key))
    for key, value in data.items():
        if not isinstance(value, dict) or "mean" not in value or "std" not in value:
            errors.append("normalization {!r} must contain mean and std arrays".format(key))
            continue
        mean, std = value["mean"], value["std"]
        if not isinstance(mean, list) or not isinstance(std, list) or len(mean) != len(std):
            errors.append("normalization {!r} mean/std lengths differ or are not arrays".format(key))
            continue
        if not mean:
            errors.append("normalization {!r} has empty statistics".format(key))
        expected_dim = NORMALIZATION_DIMS.get(key)
        if expected_dim is not None and len(mean) != expected_dim:
            errors.append(
                "normalization {!r} has {} channels; expected {}".format(
                    key, len(mean), expected_dim
                )
            )
        for i, item in enumerate(std):
            try:
                if not math.isfinite(float(item)) or float(item) <= 0:
                    errors.append("normalization {!r} std[{}] must be finite and > 0".format(key, i))
            except (TypeError, ValueError):
                errors.append("normalization {!r} std[{}] is not numeric".format(key, i))
    for key in ("ego", "neighbor"):
        if key in data and isinstance(data[key], dict) and len(data[key].get("mean", [])) != 4:
            errors.append("normalization {!r} must have four future-state channels".format(key))
    if predicted_neighbor_num <= 0:
        errors.append("predicted_neighbor_num must be positive")
    return errors


def _validate_array_finite(name: str, array, errors: List[str], prefix: str) -> None:
    if name in BOOLEAN_KEYS:
        if array.dtype != np.bool_:
            errors.append("{}{} must have boolean dtype, got {}".format(prefix, name, array.dtype))
        return
    if not np.issubdtype(array.dtype, np.number):
        errors.append("{}{} has non-numeric dtype {}".format(prefix, name, array.dtype))
        return
    if not np.isfinite(array).all():
        errors.append("{}{} contains NaN or infinite values".format(prefix, name))


def _validate_record(path: Path, args: argparse.Namespace) -> List[str]:
    errors: List[str] = []
    prefix = "{}: ".format(path)
    try:
        with np.load(str(path), allow_pickle=False) as record:
            present = set(record.files)
            for key in REQUIRED_KEYS:
                if key not in present:
                    errors.append("{}missing key {!r}".format(prefix, key))
            if errors:
                return errors
            arrays: Dict[str, object] = {key: record[key] for key in REQUIRED_KEYS}
    except Exception as exc:
        return ["{}could not load npz: {}".format(prefix, exc)]

    exact_shapes = {
        "ego_current_state": (10,),
        "ego_agent_future": (args.future_len, 3),
        "lanes": (args.lane_num, args.lane_len, args.lane_state_dim),
        "lanes_speed_limit": (args.lane_num, 1),
        "lanes_has_speed_limit": (args.lane_num, 1),
        "route_lanes": (args.route_num, args.route_len, args.route_state_dim),
        "route_lanes_speed_limit": (args.route_num, 1),
        "route_lanes_has_speed_limit": (args.route_num, 1),
        "static_objects": (args.static_objects_num, args.static_objects_state_dim),
    }
    for key, expected in exact_shapes.items():
        _shape_error(key, arrays[key].shape, expected, errors, prefix)

    past_shape = tuple(int(x) for x in arrays["neighbor_agents_past"].shape)
    if (
        len(past_shape) != 3
        or past_shape[0] < args.agent_num
        or past_shape[1:] != (args.time_len, args.agent_state_dim)
    ):
        errors.append(
            "{}neighbor_agents_past shape {} must be (at least {}, {}, {})".format(
                prefix, past_shape, args.agent_num, args.time_len, args.agent_state_dim
            )
        )

    future_shape = tuple(int(x) for x in arrays["neighbor_agents_future"].shape)
    if (
        len(future_shape) != 3
        or future_shape[0] < args.predicted_neighbor_num
        or future_shape[1:] != (args.future_len, 3)
    ):
        errors.append(
            "{}neighbor_agents_future shape {} must be (at least {}, {}, 3)".format(
                prefix, future_shape, args.predicted_neighbor_num, args.future_len
            )
        )
    for key, array in arrays.items():
        _validate_array_finite(key, array, errors, prefix)
    return errors


def _validate_manifest(data_dir: str, data_list: str, args: argparse.Namespace) -> Tuple[int, List[str]]:
    errors: List[str] = []
    try:
        with open(data_list, "r", encoding="utf-8") as handle:
            entries = json.load(handle)
    except Exception as exc:
        return 0, ["data list {} could not be read: {}".format(data_list, exc)]
    if not isinstance(entries, list):
        return 0, ["data list must contain a JSON array of filenames"]
    if not entries:
        return 0, ["data list is empty"]
    if args.limit < 0:
        errors.append("limit must be >= 0")
    selected = entries if args.limit == 0 else entries[: args.limit]
    for index, entry in enumerate(selected):
        if not isinstance(entry, str) or not entry:
            errors.append("manifest entry {} is not a non-empty filename".format(index))
            continue
        if os.path.isabs(entry):
            errors.append("manifest entry {} must be relative to data_dir, got absolute path {!r}".format(index, entry))
            continue
        normalized_entry = os.path.normpath(entry)
        if normalized_entry == ".." or normalized_entry.startswith(".." + os.sep):
            errors.append("manifest entry {} escapes data_dir: {!r}".format(index, entry))
            continue
        if not normalized_entry.lower().endswith(".npz"):
            errors.append("manifest entry {} is not an .npz filename: {!r}".format(index, entry))
            continue
        path = Path(os.path.join(data_dir, normalized_entry))
        if not path.is_file():
            errors.append("manifest entry {} resolves to missing file {}".format(index, path))
            continue
        errors.extend(_validate_record(path, args))
    return len(selected), errors


def _print_defaults() -> None:
    print("Default model-ready tensor contract:")
    for line in (
        "ego_current_state=(10,)",
        "ego_agent_future=(80,3)",
        "neighbor_agents_past=(32,21,11)",
        "neighbor_agents_future=(>=10,80,3)",
        "lanes=(70,20,12), lanes_speed_limit=(70,1), lanes_has_speed_limit=(70,1) bool",
        "route_lanes=(25,20,12), route_lanes_speed_limit=(25,1), route_lanes_has_speed_limit=(25,1) bool",
        "static_objects=(5,10)",
    ):
        print("  " + line)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parser().parse_args(argv)
    if args.print_defaults:
        _print_defaults()
        return 0
    if not args.check_normalization and not args.check_manifest:
        _parser().error("provide --check-normalization, --check-manifest, or --print-defaults")
    errors: List[str] = []
    for name in (
        "predicted_neighbor_num", "future_len", "time_len", "agent_num",
        "agent_state_dim", "static_objects_num", "static_objects_state_dim",
        "lane_num", "lane_len", "lane_state_dim", "route_num", "route_len",
        "route_state_dim",
    ):
        _positive(name, getattr(args, name), errors)
    if args.limit < 0:
        errors.append("limit must be >= 0")
    if args.check_normalization:
        errors.extend(_validate_normalization(args.check_normalization, args.predicted_neighbor_num))
        if not errors:
            print("OK normalization: {}".format(args.check_normalization))
    if args.check_manifest:
        if not args.data_list:
            errors.append("--data-list is required with --check-manifest")
        else:
            count, manifest_errors = _validate_manifest(args.check_manifest, args.data_list, args)
            errors.extend(manifest_errors)
            if not manifest_errors:
                print("OK manifest: checked {} record(s) under {}".format(count, args.check_manifest))
    if errors:
        for error in errors:
            print("ERROR: " + error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
