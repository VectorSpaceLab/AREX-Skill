#!/usr/bin/env python3
"""Validate Diffusion Planner preprocessing outputs without nuPlan.

The validator checks paths, the generated .npz filename manifest, record
shapes, finite values, and normalization vector dimensions. ``--make-fixture``
creates a small synthetic, schema-valid fixture for parser/validator tests;
it is not a nuPlan data substitute.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path, PurePath
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


DEFAULTS = {
    "agent_num": 32,
    "static_num": 5,
    "lane_num": 70,
    "lane_len": 20,
    "route_num": 25,
    "route_len": 20,
    "past_steps": 21,
    "future_steps": 80,
}

REQUIRED_KEYS = {
    "map_name",
    "token",
    "ego_current_state",
    "ego_agent_future",
    "neighbor_agents_past",
    "neighbor_agents_future",
    "static_objects",
    "lanes",
    "lanes_speed_limit",
    "lanes_has_speed_limit",
    "route_lanes",
    "route_lanes_speed_limit",
    "route_lanes_has_speed_limit",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Check Diffusion Planner .npz records, filename manifest, "
            "paths, and normalization dimensions without nuPlan."
        )
    )
    p.add_argument("--data-dir", type=Path, help="directory containing processed .npz records")
    p.add_argument("--manifest", type=Path, help="JSON array of processed .npz filenames")
    p.add_argument("--normalization", type=Path, help="normalization JSON used by training")
    p.add_argument("--raw-data-path", type=Path, help="optional raw nuPlan data directory to check")
    p.add_argument("--map-path", type=Path, help="optional nuPlan map directory to check")
    p.add_argument("--save-path", type=Path, help="optional processed output directory to check writable")
    p.add_argument("--limit", type=int, help="validate at most this many manifest entries")
    p.add_argument("--agent-num", type=int, default=DEFAULTS["agent_num"])
    p.add_argument("--static-num", type=int, default=DEFAULTS["static_num"])
    p.add_argument("--lane-num", type=int, default=DEFAULTS["lane_num"])
    p.add_argument("--lane-len", type=int, default=DEFAULTS["lane_len"])
    p.add_argument("--route-num", type=int, default=DEFAULTS["route_num"])
    p.add_argument("--route-len", type=int, default=DEFAULTS["route_len"])
    p.add_argument("--past-steps", type=int, default=DEFAULTS["past_steps"])
    p.add_argument("--future-steps", type=int, default=DEFAULTS["future_steps"])
    p.add_argument(
        "--make-fixture",
        type=Path,
        metavar="DIR",
        help="create and validate a synthetic fixture under DIR, then exit",
    )
    return p


def positive_options(args: argparse.Namespace) -> List[str]:
    names = [
        "agent_num",
        "static_num",
        "lane_num",
        "lane_len",
        "route_num",
        "route_len",
        "past_steps",
        "future_steps",
    ]
    return [name for name in names if getattr(args, name) <= 0]


def check_dir(path: Path, label: str, writable: bool, errors: List[str]) -> None:
    if not path.exists():
        errors.append(f"{label} does not exist: {path}")
        return
    if not path.is_dir():
        errors.append(f"{label} is not a directory: {path}")
        return
    if not os.access(path, os.R_OK):
        errors.append(f"{label} is not readable: {path}")
    if writable and not os.access(path, os.W_OK):
        errors.append(f"{label} is not writable: {path}")


def safe_manifest_name(value: object) -> Tuple[bool, str]:
    if not isinstance(value, str):
        return False, "entry is not a string"
    path = PurePath(value)
    if not value or path.is_absolute() or path.name != value:
        return False, "must be a relative basename, not an absolute or nested path"
    if ".." in path.parts:
        return False, "must not contain '..'"
    if not value.endswith(".npz"):
        return False, "must end with .npz"
    return True, ""


def expected_shapes(args: argparse.Namespace) -> Dict[str, Tuple[int, ...]]:
    return {
        "ego_current_state": (10,),
        "ego_agent_future": (args.future_steps, 3),
        "neighbor_agents_past": (args.agent_num, args.past_steps, 11),
        "neighbor_agents_future": (args.agent_num, args.future_steps, 3),
        "static_objects": (args.static_num, 10),
        "lanes": (args.lane_num, args.lane_len, 12),
        "lanes_speed_limit": (args.lane_num, 1),
        "lanes_has_speed_limit": (args.lane_num, 1),
        "route_lanes": (args.route_num, args.route_len, 12),
        "route_lanes_speed_limit": (args.route_num, 1),
        "route_lanes_has_speed_limit": (args.route_num, 1),
    }


def check_normalization(path: Path, errors: List[str]) -> None:
    if not path.exists():
        errors.append(f"normalization file does not exist: {path}")
        return
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read normalization JSON {path}: {exc}")
        return
    if not isinstance(value, dict):
        errors.append("normalization JSON must be an object")
        return
    lengths = {
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
    for key, length in lengths.items():
        entry = value.get(key)
        if not isinstance(entry, dict):
            errors.append(f"normalization entry {key!r} must be an object")
            continue
        for stat in ("mean", "std"):
            if stat not in entry:
                errors.append(f"normalization entry {key!r} is missing {stat!r}")
                continue
            try:
                array = np.asarray(entry[stat], dtype=np.float64)
            except (TypeError, ValueError) as exc:
                errors.append(f"normalization {key}.{stat} is not numeric: {exc}")
                continue
            if array.shape != (length,):
                errors.append(
                    f"normalization {key}.{stat} has shape {array.shape}; expected {(length,)}"
                )
            elif not np.all(np.isfinite(array)):
                errors.append(f"normalization {key}.{stat} contains non-finite values")
            elif stat == "std" and np.any(array <= 0):
                errors.append(f"normalization {key}.std must be strictly positive")


def check_record(
    path: Path, shapes: Dict[str, Tuple[int, ...]], errors: List[str], index: int
) -> bool:
    try:
        with np.load(path, allow_pickle=False) as data:
            keys = set(data.files)
            missing = sorted(REQUIRED_KEYS - keys)
            if missing:
                errors.append(f"{path.name}: missing keys {missing}")
                return False
            extra = sorted(keys - REQUIRED_KEYS)
            if extra:
                print(f"warning: {path.name}: ignoring extra keys {extra}")
            for key, shape in shapes.items():
                array = data[key]
                if array.shape != shape:
                    errors.append(
                        f"{path.name}: {key} has shape {array.shape}; expected {shape}"
                    )
                    continue
                if key.endswith("has_speed_limit") and array.dtype != np.bool_:
                    errors.append(
                        f"{path.name}: {key} has dtype {array.dtype}; expected bool"
                    )
                elif np.issubdtype(array.dtype, np.number) and not np.all(np.isfinite(array)):
                    errors.append(f"{path.name}: {key} contains non-finite values")
            for key in ("map_name", "token"):
                array = data[key]
                if array.shape != () or not isinstance(array.item(), (str, bytes)):
                    errors.append(f"{path.name}: {key} must be a scalar string")
    except (OSError, ValueError, EOFError) as exc:
        errors.append(f"{path.name}: cannot read safely as an npz: {exc}")
        return False
    return True


def check_manifest(
    data_dir: Path,
    manifest_path: Path,
    shapes: Dict[str, Tuple[int, ...]],
    limit: Optional[int],
    errors: List[str],
) -> int:
    if not manifest_path.exists():
        errors.append(f"manifest does not exist: {manifest_path}")
        return 0
    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            entries = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read manifest JSON {manifest_path}: {exc}")
        return 0
    if not isinstance(entries, list):
        errors.append("manifest must be a JSON array of .npz filenames")
        return 0
    if not entries:
        errors.append("manifest is empty; no processed scenarios were produced")
        return 0
    seen = set()
    valid_names: List[str] = []
    for index, entry in enumerate(entries):
        ok, reason = safe_manifest_name(entry)
        if not ok:
            errors.append(f"manifest entry {index}: {reason}: {entry!r}")
            continue
        if entry in seen:
            errors.append(f"manifest contains duplicate entry: {entry}")
            continue
        seen.add(entry)
        valid_names.append(entry)
    if limit is not None:
        valid_names = valid_names[:limit]
    checked = 0
    for name in valid_names:
        record = data_dir / name
        if not record.exists():
            errors.append(f"manifest entry is missing from data directory: {name}")
            continue
        if not record.is_file():
            errors.append(f"manifest entry is not a regular file: {name}")
            continue
        if check_record(record, shapes, errors, checked):
            checked += 1
    return checked


def fixture_normalization() -> Dict[str, Dict[str, List[float]]]:
    lengths = {
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
    return {key: {"mean": [0.0] * n, "std": [1.0] * n} for key, n in lengths.items()}


def make_fixture(root: Path, args: argparse.Namespace) -> Tuple[Path, Path, Path]:
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"refusing to overwrite non-empty fixture directory: {root}")
    root.mkdir(parents=True, exist_ok=True)
    data_dir = root / "data"
    data_dir.mkdir()
    arrays = {
        "map_name": np.asarray("fixture-map"),
        "token": np.asarray("fixture-token"),
        "ego_current_state": np.zeros((10,), dtype=np.float32),
        "ego_agent_future": np.zeros((args.future_steps, 3), dtype=np.float32),
        "neighbor_agents_past": np.zeros((args.agent_num, args.past_steps, 11), dtype=np.float32),
        "neighbor_agents_future": np.zeros((args.agent_num, args.future_steps, 3), dtype=np.float32),
        "static_objects": np.zeros((args.static_num, 10), dtype=np.float32),
        "lanes": np.zeros((args.lane_num, args.lane_len, 12), dtype=np.float32),
        "lanes_speed_limit": np.zeros((args.lane_num, 1), dtype=np.float32),
        "lanes_has_speed_limit": np.zeros((args.lane_num, 1), dtype=np.bool_),
        "route_lanes": np.zeros((args.route_num, args.route_len, 12), dtype=np.float32),
        "route_lanes_speed_limit": np.zeros((args.route_num, 1), dtype=np.float32),
        "route_lanes_has_speed_limit": np.zeros((args.route_num, 1), dtype=np.bool_),
    }
    np.savez(data_dir / "fixture-map_fixture-token.npz", **arrays)
    manifest = root / "diffusion_planner_training.json"
    with manifest.open("w", encoding="utf-8") as handle:
        json.dump(["fixture-map_fixture-token.npz"], handle, indent=2)
    normalization = root / "normalization.json"
    with normalization.open("w", encoding="utf-8") as handle:
        json.dump(fixture_normalization(), handle, indent=2)
    return data_dir, manifest, normalization


def validate(args: argparse.Namespace) -> int:
    errors: List[str] = []
    invalid = positive_options(args)
    if invalid:
        errors.append("these dimension options must be positive: " + ", ".join(invalid))
    if args.limit is not None and args.limit <= 0:
        errors.append("--limit must be positive")
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    check_dir(args.data_dir, "data directory", False, errors)
    if args.raw_data_path is not None:
        check_dir(args.raw_data_path, "raw data path", False, errors)
    if args.map_path is not None:
        check_dir(args.map_path, "map path", False, errors)
    if args.save_path is not None:
        check_dir(args.save_path, "save path", True, errors)
    check_normalization(args.normalization, errors)
    checked = 0
    if args.data_dir.exists():
        checked = check_manifest(
            args.data_dir,
            args.manifest,
            expected_shapes(args),
            args.limit,
            errors,
        )
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"validated {checked} processed record(s), manifest, paths, and normalization")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    if args.make_fixture is not None:
        try:
            data_dir, manifest, normalization = make_fixture(args.make_fixture, args)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        args.data_dir = data_dir
        args.manifest = manifest
        args.normalization = normalization
        print(f"created synthetic fixture under {args.make_fixture}")
    elif args.data_dir is None or args.manifest is None or args.normalization is None:
        parser().error("--data-dir, --manifest, and --normalization are required unless --make-fixture is used")
    return validate(args)


if __name__ == "__main__":
    raise SystemExit(main())
