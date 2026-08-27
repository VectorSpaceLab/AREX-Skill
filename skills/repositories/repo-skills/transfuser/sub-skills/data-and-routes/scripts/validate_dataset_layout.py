#!/usr/bin/env python3
"""Validate a TransFuser Scenario/Town/Route dataset tree locally.

The checker verifies names, synchronized frame ids, and JSON contracts.  It
does not decode images, load NumPy, import CARLA, download data, or modify the
provided tree.
"""
from __future__ import print_function

import argparse
import json
import os
import re
import shutil
import sys
import tempfile

TOWNS = frozenset(
    ["Town01", "Town02", "Town03", "Town04", "Town05", "Town06", "Town07", "Town10HD"]
)
MODALITIES = {
    "rgb": re.compile(r"^(\d{4})\.png$"),
    "depth": re.compile(r"^(\d{4})\.png$"),
    "semantics": re.compile(r"^(\d{4})\.png$"),
    "lidar": re.compile(r"^(\d{4})\.npy$"),
    "topdown": re.compile(r"^encoded_(\d{4})\.png$"),
    "label_raw": re.compile(r"^(\d{4})\.json$"),
    "measurements": re.compile(r"^(\d{4})\.json$"),
}
REQUIRED_MEASUREMENT_FIELDS = (
    "x", "y", "theta", "speed", "target_speed", "x_command", "y_command",
    "command", "waypoints", "steer", "throttle", "brake", "junction",
    "vehicle_hazard", "light_hazard", "walker_hazard", "stop_sign_hazard",
    "angle", "ego_matrix",
)
REQUIRED_LABEL_FIELDS = (
    "class", "extent", "position", "yaw", "num_points", "distance", "speed", "brake", "id", "ego_matrix",
)
SCENARIO_ALIASES = {
    "s1": "Scenario1", "s3": "Scenario3", "s4": "Scenario4", "s7": "Scenario7",
    "s8": "Scenario8", "s9": "Scenario9", "s10": "Scenario10",
    "scenario1": "Scenario1", "scenario3": "Scenario3", "scenario4": "Scenario4",
    "scenario7": "Scenario7", "scenario8": "Scenario8", "scenario9": "Scenario9",
    "scenario10": "Scenario10",
}


def _is_matrix(value):
    return isinstance(value, list) and len(value) == 4 and all(
        isinstance(row, list) and len(row) == 4 for row in value
    )


def _frame_ids(directory, pattern):
    if not os.path.isdir(directory):
        return set(), []
    ids = set()
    unexpected = []
    for name in sorted(os.listdir(directory)):
        match = pattern.match(name)
        if match:
            ids.add(match.group(1))
        else:
            unexpected.append(name)
    return ids, unexpected


def _validate_measurement(path, errors):
    try:
        with open(path, "r") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        errors.append("{}: invalid measurement JSON: {}".format(path, exc))
        return
    if not isinstance(data, dict):
        errors.append("{}: measurement must be a JSON object".format(path))
        return
    missing = [field for field in REQUIRED_MEASUREMENT_FIELDS if field not in data]
    if missing:
        errors.append("{}: measurement missing {}".format(path, ", ".join(missing)))
    if "waypoints" in data and not isinstance(data["waypoints"], list):
        errors.append("{}: waypoints must be a list".format(path))
    if "ego_matrix" in data and not _is_matrix(data["ego_matrix"]):
        errors.append("{}: ego_matrix must be a 4x4 list".format(path))


def _validate_label(path, errors):
    try:
        with open(path, "r") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        errors.append("{}: invalid label JSON: {}".format(path, exc))
        return
    if not isinstance(data, list):
        errors.append("{}: label_raw must be a JSON list".format(path))
        return
    for index, label in enumerate(data):
        if not isinstance(label, dict):
            errors.append("{}: label[{}] must be an object".format(path, index))
            continue
        missing = [field for field in REQUIRED_LABEL_FIELDS if field not in label]
        if missing:
            errors.append("{}: label[{}] missing {}".format(path, index, ", ".join(missing)))
        if "ego_matrix" in label and not _is_matrix(label["ego_matrix"]):
            errors.append("{}: label[{}].ego_matrix must be a 4x4 list".format(path, index))


def validate_dataset(root, expected_town=None, require_windows=False, min_frames=1):
    result = {"path": os.path.abspath(root), "errors": [], "warnings": [], "stats": {
        "scenarios": 0, "towns": 0, "routes": 0, "usable_routes": 0, "frames": 0,
    }}
    if not os.path.isdir(root):
        result["errors"].append("dataset root is not a directory: {}".format(root))
        return result

    scenario_dirs = sorted(
        os.path.join(root, name) for name in os.listdir(root)
        if not name.startswith(".") and os.path.isdir(os.path.join(root, name))
    )
    result["stats"]["scenarios"] = len(scenario_dirs)
    if not scenario_dirs:
        result["errors"].append("dataset root contains no scenario directories")

    seen_towns = set()
    for scenario_dir in scenario_dirs:
        scenario_name = os.path.basename(scenario_dir)
        logical_scenario = SCENARIO_ALIASES.get(scenario_name.lower())
        if logical_scenario is None and scenario_name.lower() not in ("left", "right", "ll", "lr", "rl", "rr"):
            result["warnings"].append("unrecognized scenario directory {}; treating it as a label".format(scenario_name))
        town_dirs = sorted(
            os.path.join(scenario_dir, name) for name in os.listdir(scenario_dir)
            if not name.startswith(".") and os.path.isdir(os.path.join(scenario_dir, name))
        )
        for town_dir in town_dirs:
            town = os.path.basename(town_dir)
            seen_towns.add(town)
            if town not in TOWNS:
                result["errors"].append("unsupported town directory: {}/{}".format(scenario_name, town))
            if expected_town and town != expected_town:
                result["errors"].append("town {} does not match expected {}".format(town, expected_town))
            route_dirs = sorted(
                os.path.join(town_dir, name) for name in os.listdir(town_dir)
                if not name.startswith(".") and os.path.isdir(os.path.join(town_dir, name))
            )
            if not route_dirs:
                result["warnings"].append("{} contains no route directories".format(town_dir))
            for route_dir in route_dirs:
                result["stats"]["routes"] += 1
                route_errors_before = len(result["errors"])
                missing_dirs = [name for name in MODALITIES if not os.path.isdir(os.path.join(route_dir, name))]
                for modality in missing_dirs:
                    result["errors"].append("{} missing modality directory {}".format(route_dir, modality))
                ids_by_modality = {}
                for modality, pattern in MODALITIES.items():
                    directory = os.path.join(route_dir, modality)
                    ids, unexpected = _frame_ids(directory, pattern)
                    ids_by_modality[modality] = ids
                    if unexpected:
                        result["warnings"].append("{} has unexpected file names: {}".format(
                            os.path.join(route_dir, modality), ", ".join(unexpected[:5])
                        ))
                present_sets = list(ids_by_modality.values())
                if not any(present_sets):
                    result["errors"].append("{} contains no recognized frame files".format(route_dir))
                    continue
                common = set.intersection(*present_sets)
                union = set.union(*present_sets)
                if len(common) != len(union) or any(ids != common for ids in present_sets):
                    for modality in sorted(ids_by_modality):
                        missing = sorted(union - ids_by_modality[modality])
                        if missing:
                            result["errors"].append("{} missing frame ids {}".format(
                                os.path.join(route_dir, modality), ", ".join(missing)
                            ))
                frame_count = len(common)
                result["stats"]["frames"] += frame_count
                if frame_count < min_frames:
                    result["errors"].append("{} has {} synchronized frames; need at least {}".format(
                        route_dir, frame_count, min_frames
                    ))
                if require_windows and frame_count < 10:
                    result["errors"].append(
                        "{} has {} frames; default seq_len=1/pred_len=4 needs at least 10 for one conservative window".format(
                            route_dir, frame_count
                        )
                    )
                for frame_id in sorted(common):
                    _validate_measurement(
                        os.path.join(route_dir, "measurements", frame_id + ".json"), result["errors"]
                    )
                    _validate_label(
                        os.path.join(route_dir, "label_raw", frame_id + ".json"), result["errors"]
                    )
                if len(result["errors"]) == route_errors_before:
                    result["stats"]["usable_routes"] += 1

    result["stats"]["towns"] = len(seen_towns)
    if not seen_towns:
        result["errors"].append("dataset contains no town directories")
    return result


def _fixture_measurement():
    return {
        "x": 0, "y": 0, "theta": 0, "speed": 0, "target_speed": 4,
        "x_command": 0, "y_command": 1, "command": 4, "waypoints": [],
        "steer": 0, "throttle": 0, "brake": 1, "junction": False,
        "vehicle_hazard": [False], "light_hazard": False, "walker_hazard": [False],
        "stop_sign_hazard": False, "angle": 0, "ego_matrix": [[1, 0, 0, 0]] * 4,
    }


def _fixture_label():
    return [{
        "class": "Car", "extent": [1, 1, 1], "position": [0, 0, 0], "yaw": 0,
        "num_points": -1, "distance": -1, "speed": 0, "brake": 0, "id": 1,
        "ego_matrix": [[1, 0, 0, 0]] * 4,
    }]


def run_self_test():
    root = tempfile.mkdtemp(prefix="transfuser-layout-")
    try:
        route = os.path.join(root, "s8", "Town03", "route000")
        for modality in MODALITIES:
            os.makedirs(os.path.join(route, modality))
        for frame in range(10):
            stem = "{:04d}".format(frame)
            open(os.path.join(route, "rgb", stem + ".png"), "wb").close()
            open(os.path.join(route, "depth", stem + ".png"), "wb").close()
            open(os.path.join(route, "semantics", stem + ".png"), "wb").close()
            open(os.path.join(route, "lidar", stem + ".npy"), "wb").close()
            open(os.path.join(route, "topdown", "encoded_" + stem + ".png"), "wb").close()
            with open(os.path.join(route, "measurements", stem + ".json"), "w") as handle:
                json.dump(_fixture_measurement(), handle)
            with open(os.path.join(route, "label_raw", stem + ".json"), "w") as handle:
                json.dump(_fixture_label(), handle)
        result = validate_dataset(root, expected_town="Town03", require_windows=True)
        assert not result["errors"], result
        assert result["stats"]["usable_routes"] == 1, result
        return {"self_test": "passed", "frames": result["stats"]["frames"]}
    finally:
        shutil.rmtree(root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", help="dataset root containing scenario directories")
    parser.add_argument("--town", choices=sorted(TOWNS), help="require this town for every route")
    parser.add_argument("--min-frames", type=int, default=1, help="minimum synchronized frames per route (default: 1)")
    parser.add_argument("--require-windows", action="store_true", help="require at least 10 frames for default seq_len=1/pred_len=4")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--self-test", action="store_true", help="run a tiny 10-frame fixture check")
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0
    if not args.root:
        parser.error("provide a dataset root or use --self-test")
    if args.min_frames < 1:
        parser.error("--min-frames must be positive")
    result = validate_dataset(args.root, args.town, args.require_windows, args.min_frames)
    payload = {"ok": not result["errors"], "result": result}
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("[{}] {}".format("OK" if payload["ok"] else "ERROR", result["path"]))
        for message in result["errors"]:
            print("  error: {}".format(message))
        for message in result["warnings"]:
            print("  warning: {}".format(message))
        print("  stats: {}".format(json.dumps(result["stats"], sort_keys=True)))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
