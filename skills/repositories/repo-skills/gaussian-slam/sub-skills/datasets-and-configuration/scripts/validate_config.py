#!/usr/bin/env python3
"""Validate Gaussian-SLAM YAML inheritance and RGB-D data preconditions.

This script deliberately imports no Gaussian-SLAM, PyTorch, OpenCV, Open3D,
or CUDA modules. It validates one or more explicit config paths and exits 1
when the effective YAML or an available dataset fixture is invalid.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on the caller env
    print("ERROR: PyYAML is required to validate YAML configs: %s" % exc, file=sys.stderr)
    raise SystemExit(2)


DATASET_ALIASES = {"replica", "tum_rgbd", "scan_net", "scannetpp"}
REQUIRED_TOP_LEVEL = (
    "project_name",
    "dataset_name",
    "checkpoint_path",
    "use_wandb",
    "frame_limit",
    "seed",
    "mapping",
    "tracking",
    "cam",
    "data",
)
REQUIRED_CAM = ("H", "W", "fx", "fy", "cx", "cy", "depth_scale")
INHERIT_WARNING = "inherit_from is not file-relative; accepted repository-root-relative fallback: {}"


class Result:
    def __init__(self, requested: Path):
        self.requested = requested
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.notes: List[str] = []
        self.effective: Optional[Dict[str, Any]] = None
        self.resolved_path: Optional[Path] = None
        self.inheritance_chain: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


class ConfigLoader:
    """Safe YAML loader with file-relative inheritance and cycle detection."""

    def __init__(self, result: Result):
        self.result = result
        self.cache: Dict[Path, Dict[str, Any]] = {}
        self.stack: List[Path] = []

    def resolve_inherit(self, raw: str, declaring_file: Path) -> Optional[Path]:
        candidate = Path(raw).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()

        file_relative = (declaring_file.parent / candidate).resolve()
        if file_relative.is_file():
            return file_relative

        # Existing repository configs historically spell the repo-root-relative
        # path as configs/<dataset>/<default>.yaml. Search ancestors of the
        # declaring file first so validation is independent of the caller's
        # current working directory, then retain the source loader's cwd form.
        for ancestor in declaring_file.parents:
            repo_relative = (ancestor / candidate).resolve()
            if repo_relative.is_file():
                self.result.warning(INHERIT_WARNING.format(raw))
                return repo_relative
        cwd_relative = (Path.cwd() / candidate).resolve()
        if cwd_relative.is_file():
            self.result.warning(INHERIT_WARNING.format(raw))
            return cwd_relative

        return file_relative

    def load(self, path: Path) -> Optional[Dict[str, Any]]:
        path = path.expanduser().resolve()
        if path in self.stack:
            cycle = " -> ".join(str(item) for item in self.stack + [path])
            self.result.error("inheritance cycle: %s" % cycle)
            return None
        if path in self.cache:
            return self.cache[path]
        if not path.is_file():
            self.result.error("config file not found: %s" % path)
            return None

        self.stack.append(path)
        self.result.inheritance_chain.append(str(path))
        try:
            try:
                with path.open("r", encoding="utf-8") as handle:
                    child = yaml.safe_load(handle)
            except (OSError, yaml.YAMLError) as exc:
                self.result.error("cannot parse %s: %s" % (path, exc))
                return None
            if child is None:
                self.result.error("config is empty: %s" % path)
                return None
            if not isinstance(child, dict):
                self.result.error("config must contain a YAML mapping: %s" % path)
                return None

            merged: Dict[str, Any] = {}
            inherit_from = child.get("inherit_from")
            if inherit_from is not None:
                if not isinstance(inherit_from, str) or not inherit_from.strip():
                    self.result.error("inherit_from must be a non-empty string in %s" % path)
                else:
                    base_path = self.resolve_inherit(inherit_from, path)
                    if base_path is not None:
                        base = self.load(base_path)
                        if base is not None:
                            merged = deep_merge(merged, base)
            merged = deep_merge(merged, child)
            self.cache[path] = merged
            return merged
        finally:
            self.stack.pop()


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        elif isinstance(value, dict):
            out[key] = deep_merge({}, value)
        else:
            out[key] = value
    return out


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def require_mapping(config: Dict[str, Any], key: str, result: Result) -> Optional[Dict[str, Any]]:
    value = config.get(key)
    if not isinstance(value, dict):
        result.error("top-level '%s' must be a mapping" % key)
        return None
    return value


def validate_effective_config(config: Any, result: Result) -> Optional[str]:
    if not isinstance(config, dict):
        result.error("effective config must be a YAML mapping")
        return None

    for key in REQUIRED_TOP_LEVEL:
        if key not in config:
            result.error("missing required top-level key '%s'" % key)

    dataset_name = config.get("dataset_name")
    if not isinstance(dataset_name, str) or dataset_name not in DATASET_ALIASES:
        result.error(
            "dataset_name must be exactly one of %s (got %r)"
            % (", ".join(sorted(DATASET_ALIASES)), dataset_name)
        )
        dataset_name = None

    for key in ("mapping", "tracking", "cam", "data"):
        if key in config:
            require_mapping(config, key, result)

    if "project_name" in config and (not isinstance(config["project_name"], str) or not config["project_name"].strip()):
        result.error("project_name must be a non-empty string")
    if "use_wandb" in config and not isinstance(config["use_wandb"], bool):
        result.error("use_wandb must be boolean")
    if "seed" in config and not is_integer(config["seed"]):
        result.error("seed must be an integer")
    if "frame_limit" in config and (not is_integer(config["frame_limit"]) or config["frame_limit"] < -1):
        result.error("frame_limit must be an integer >= -1")
    if "checkpoint_path" in config and config["checkpoint_path"] is not None and not isinstance(config["checkpoint_path"], str):
        result.error("checkpoint_path must be a string or null")

    cam = config.get("cam") if isinstance(config.get("cam"), dict) else {}
    for key in REQUIRED_CAM:
        if key not in cam:
            result.error("missing required cam.%s" % key)
    for key in ("H", "W"):
        if key in cam and (not is_integer(cam[key]) or cam[key] <= 0):
            result.error("cam.%s must be a positive integer" % key)
    for key in ("fx", "fy", "depth_scale"):
        if key in cam and (not is_number(cam[key]) or float(cam[key]) <= 0):
            result.error("cam.%s must be a positive number" % key)
    for key in ("cx", "cy"):
        if key in cam and not is_number(cam[key]):
            result.error("cam.%s must be a finite number" % key)
    crop_edge = cam.get("crop_edge", 0)
    if not is_integer(crop_edge) or crop_edge < 0:
        result.error("cam.crop_edge must be an integer >= 0")
    elif is_integer(cam.get("H")) and is_integer(cam.get("W")) and 2 * crop_edge >= min(cam["H"], cam["W"]):
        result.error("cam.crop_edge removes the configured image")
    if "distortion" in cam:
        distortion = cam["distortion"]
        if not isinstance(distortion, (list, tuple)) or len(distortion) not in (4, 5) or not all(is_number(item) for item in distortion):
            result.error("cam.distortion must contain four or five finite numbers")

    data = config.get("data") if isinstance(config.get("data"), dict) else {}
    for key in ("scene_name", "input_path", "output_path"):
        if key not in data:
            result.error("missing required data.%s" % key)
        elif not isinstance(data[key], str) or not data[key].strip():
            result.error("data.%s must be a non-empty string" % key)
    if "frame_limit" in data and (not is_integer(data["frame_limit"]) or data["frame_limit"] < -1):
        result.error("data.frame_limit must be an integer >= -1 when present")
    if dataset_name == "scannetpp":
        if not isinstance(data.get("use_train_split"), bool):
            result.error("scannetpp requires boolean data.use_train_split")
    elif "use_train_split" in data:
        result.warning("data.use_train_split is ignored for dataset %s" % dataset_name)

    return dataset_name


def finite_floats(values: Sequence[str]) -> bool:
    try:
        return all(math.isfinite(float(value)) for value in values)
    except (TypeError, ValueError):
        return False


def numeric_id(path: Path) -> Optional[int]:
    match = re.fullmatch(r"\d+", path.stem)
    return int(match.group(0)) if match else None


def read_noncomment_lines(path: Path, result: Result) -> List[Tuple[int, str]]:
    rows: List[Tuple[int, str]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, 1):
                stripped = raw.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                rows.append((line_number, stripped))
    except OSError as exc:
        result.error("cannot read %s: %s" % (path, exc))
    return rows


def validate_matrix_file(path: Path, result: Result, label: str) -> bool:
    rows = read_noncomment_lines(path, result)
    values: List[str] = []
    for _, row in rows:
        values.extend(row.split())
    if len(values) != 16 or not finite_floats(values):
        result.error("%s must contain exactly 16 finite numbers: %s" % (label, path))
        return False
    return True


def validate_replica(root: Path, result: Result) -> None:
    results = root / "results"
    if not results.is_dir():
        result.error("Replica data missing directory: %s" % results)
        return
    colors = sorted(results.glob("frame*.jpg"))
    depths = sorted(results.glob("depth*.png"))
    trajectory = root / "traj.txt"
    if not trajectory.is_file():
        result.error("Replica pose file missing: %s" % trajectory)
    else:
        rows = read_noncomment_lines(trajectory, result)
        for line_number, row in rows:
            values = row.split()
            if len(values) != 16 or not finite_floats(values):
                result.error("Replica traj.txt line %d is not a finite 4x4 matrix" % line_number)
                break
    if len(colors) != len(depths):
        result.error("Replica RGB/depth frame count mismatch: %d vs %d" % (len(colors), len(depths)))
    pose_count = None
    if trajectory.is_file():
        pose_count = len(read_noncomment_lines(trajectory, result))
        if pose_count != len(colors):
            result.error("Replica RGB/pose frame count mismatch: %d vs %d" % (len(colors), pose_count))
    color_ids = [path.stem[len("frame"):] for path in colors]
    depth_ids = [path.stem[len("depth"):] for path in depths]
    if color_ids != depth_ids:
        result.error("Replica RGB/depth identifiers do not pair")
    result.note("Replica records: rgb=%d depth=%d poses=%s" % (len(colors), len(depths), pose_count if pose_count is not None else "missing"))


def validate_tum_rows(path: Path, result: Result, pose: bool = False) -> List[Tuple[float, str]]:
    rows = read_noncomment_lines(path, result)
    parsed: List[Tuple[float, str]] = []
    previous: Optional[float] = None
    for line_number, row in rows:
        values = row.split()
        expected = 8 if pose else 2
        numeric_values = values[:expected] if pose else values[:1]
        if len(values) < expected or not finite_floats(numeric_values):
            result.error("TUM %s line %d has malformed fields" % (path.name, line_number))
            continue
        timestamp = float(values[0])
        if previous is not None and timestamp < previous:
            result.warning("TUM %s timestamps are not monotonic at line %d" % (path.name, line_number))
        previous = timestamp
        if pose:
            quaternion = [float(value) for value in values[4:8]]
            if math.sqrt(sum(value * value for value in quaternion)) <= 1e-12:
                result.error("TUM %s line %d has a zero quaternion" % (path.name, line_number))
            parsed.append((timestamp, ""))
        else:
            if not values[1].strip():
                result.error("TUM %s line %d has an empty path" % (path.name, line_number))
            parsed.append((timestamp, values[1]))
    return parsed


def nearest_delta(value: float, values: Sequence[float]) -> float:
    return min(abs(item - value) for item in values) if values else math.inf


def validate_tum(root: Path, result: Result) -> None:
    image_path, depth_path = root / "rgb.txt", root / "depth.txt"
    pose_path = root / "groundtruth.txt"
    if not pose_path.is_file():
        pose_path = root / "pose.txt"
    for path in (image_path, depth_path):
        if not path.is_file():
            result.error("TUM file missing: %s" % path)
    if not pose_path.is_file():
        result.error("TUM pose file missing: groundtruth.txt or pose.txt in %s" % root)
    if not image_path.is_file() or not depth_path.is_file() or not pose_path.is_file():
        return

    images = validate_tum_rows(image_path, result)
    depths = validate_tum_rows(depth_path, result)
    poses = validate_tum_rows(pose_path, result, pose=True)
    depth_times = [item[0] for item in depths]
    pose_times = [item[0] for item in poses]
    unmatched = 0
    for timestamp, image_name in images:
        if nearest_delta(timestamp, depth_times) >= 0.08 or nearest_delta(timestamp, pose_times) >= 0.08:
            unmatched += 1
        else:
            for relative in (image_name,):
                if not (root / relative).is_file():
                    result.error("TUM RGB path missing: %s" % (root / relative))
                    break
    for _, relative in depths:
        if not (root / relative).is_file():
            result.error("TUM depth path missing: %s" % (root / relative))
            break
    if unmatched:
        result.error("TUM RGB records without depth+pose association within 0.08s: %d" % unmatched)
    if len(images) != len(depths) or len(images) != len(poses):
        result.warning("TUM list counts differ: rgb=%d depth=%d poses=%d; timestamp association is required" % (len(images), len(depths), len(poses)))
    result.note("TUM records: rgb=%d depth=%d poses=%d associated=%d" % (len(images), len(depths), len(poses), len(images) - unmatched))


def validate_scannet(root: Path, result: Result) -> None:
    color_dir, depth_dir, pose_dir = root / "color", root / "depth", root / "pose"
    for directory in (color_dir, depth_dir, pose_dir):
        if not directory.is_dir():
            result.error("ScanNet data missing directory: %s" % directory)
    if not all(directory.is_dir() for directory in (color_dir, depth_dir, pose_dir)):
        return
    colors = sorted(color_dir.glob("*.jpg"), key=lambda path: numeric_id(path) if numeric_id(path) is not None else math.inf)
    depths = sorted(depth_dir.glob("*.png"), key=lambda path: numeric_id(path) if numeric_id(path) is not None else math.inf)
    poses = sorted(pose_dir.glob("*.txt"), key=lambda path: numeric_id(path) if numeric_id(path) is not None else math.inf)
    if not (len(colors) == len(depths) == len(poses)):
        result.error("ScanNet RGB/depth/pose frame count mismatch: %d/%d/%d" % (len(colors), len(depths), len(poses)))
    color_ids = {path.stem for path in colors}
    depth_ids = {path.stem for path in depths}
    pose_ids = {path.stem for path in poses}
    if color_ids != depth_ids or color_ids != pose_ids:
        result.error("ScanNet RGB/depth/pose identifiers do not match")
    for pose_path in poses:
        validate_matrix_file(pose_path, result, "ScanNet pose")
    result.note("ScanNet records: rgb=%d depth=%d poses=%d" % (len(colors), len(depths), len(poses)))


def validate_scannetpp(root: Path, config: Dict[str, Any], result: Result) -> None:
    dslr = root / "dslr"
    split_path = dslr / "train_test_lists.json"
    cams_path = dslr / "nerfstudio" / "transforms_undistorted.json"
    for path in (split_path, cams_path):
        if not path.is_file():
            result.error("ScanNet++ metadata missing: %s" % path)
    if not split_path.is_file() or not cams_path.is_file():
        return
    try:
        with split_path.open("r", encoding="utf-8") as handle:
            split = json.load(handle)
        with cams_path.open("r", encoding="utf-8") as handle:
            cameras = json.load(handle)
    except (OSError, ValueError) as exc:
        result.error("cannot parse ScanNet++ metadata: %s" % exc)
        return
    if not isinstance(split, dict):
        result.error("ScanNet++ train_test_lists.json must be an object")
        return
    for key in ("train", "test"):
        if not isinstance(split.get(key), list) or not all(isinstance(item, str) for item in split.get(key, [])):
            result.error("ScanNet++ split '%s' must be a list of strings" % key)
    use_train = config.get("data", {}).get("use_train_split")
    selected_key = "train" if use_train else "test"
    selected = split.get(selected_key, [])
    frames_key = "frames" if use_train else "test_frames"
    frames = cameras.get(frames_key) if isinstance(cameras, dict) else None
    if not isinstance(frames, list):
        result.error("ScanNet++ camera metadata must contain list '%s'" % frames_key)
        return
    frame_by_name = {}
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict) or not isinstance(frame.get("file_path"), str):
            result.error("ScanNet++ %s[%d] lacks a string file_path" % (frames_key, index))
            continue
        frame_by_name[frame["file_path"]] = frame
    missing_metadata = [name for name in selected if name not in frame_by_name]
    if missing_metadata:
        result.error("ScanNet++ split names missing from %s: %s" % (frames_key, ", ".join(missing_metadata[:5])))
    image_dir, depth_dir = dslr / "undistorted_images", dslr / "undistorted_depths"
    if not image_dir.is_dir() or not depth_dir.is_dir():
        result.error("ScanNet++ undistorted image/depth directories are missing")
    checked = 0
    for name in selected:
        frame = frame_by_name.get(name)
        if frame is None:
            continue
        image_path = image_dir / name
        depth_name = name.replace(".JPG", ".png")
        depth_path = depth_dir / depth_name
        if not image_path.is_file():
            result.error("ScanNet++ RGB path missing: %s" % image_path)
        if not depth_path.is_file():
            result.error("ScanNet++ depth path missing (expected .JPG -> .png): %s" % depth_path)
        matrix = frame.get("transform_matrix")
        if not isinstance(matrix, list) or len(matrix) != 4 or any(not isinstance(row, list) or len(row) != 4 for row in matrix) or not all(is_number(value) for row in matrix for value in row):
            result.error("ScanNet++ frame has malformed transform_matrix: %s" % name)
        checked += 1
    # GaussianSLAM passes {**config["data"], **config["cam"]} to the
    # dataset. The supplied ScanNet++ scene configs therefore put the useful
    # limit under data; retain the top-level fallback for hand-written configs.
    frame_limit = config.get("data", {}).get("frame_limit", config.get("frame_limit", -1))
    if use_train and is_integer(frame_limit) and frame_limit >= 0 and frame_limit > len(selected):
        result.error("ScanNet++ train frame_limit %d exceeds selected train frames %d" % (frame_limit, len(selected)))
    if not use_train and is_integer(frame_limit) and frame_limit >= 0:
        result.warning("ScanNet++ test split ignores frame_limit in the source loader")
    result.note("ScanNet++ split=%s frames=%d metadata=%d checked=%d" % (selected_key, len(selected), len(frames), checked))


def inspect_data(root: Path, dataset: str, config: Dict[str, Any], result: Result) -> None:
    if dataset == "replica":
        validate_replica(root, result)
    elif dataset == "tum_rgbd":
        validate_tum(root, result)
    elif dataset == "scan_net":
        validate_scannet(root, result)
    elif dataset == "scannetpp":
        validate_scannetpp(root, config, result)


def validate_one(requested: Path, path_base: Path, require_data: bool) -> Result:
    result = Result(requested)
    loader = ConfigLoader(result)
    result.resolved_path = requested.expanduser().resolve()
    result.effective = loader.load(result.resolved_path)
    if result.effective is None:
        return result
    dataset = validate_effective_config(result.effective, result)
    if dataset is None or result.errors:
        return result

    data = result.effective["data"]
    input_path = Path(data["input_path"]).expanduser()
    output_path = Path(data["output_path"]).expanduser()
    if not input_path.is_absolute():
        result.warning("data.input_path is relative; resolving it against %s -> %s" % (path_base, (path_base / input_path).resolve()))
    if not output_path.is_absolute():
        result.warning("data.output_path is relative; resolving it against %s -> %s" % (path_base, (path_base / output_path).resolve()))
    input_root = input_path if input_path.is_absolute() else path_base / input_path
    input_root = input_root.resolve()
    if not input_root.exists():
        message = "dataset input path does not exist: %s" % input_root
        if require_data:
            result.error(message)
        else:
            result.warning(message + " (YAML-only validation; use --require-data to fail)")
        return result
    if not input_root.is_dir():
        result.error("dataset input path is not a directory: %s" % input_root)
        return result
    inspect_data(input_root, dataset, result.effective or {}, result)
    return result


def result_dict(result: Result) -> Dict[str, Any]:
    effective = result.effective or {}
    return {
        "requested": str(result.requested),
        "resolved_config": str(result.resolved_path) if result.resolved_path else None,
        "inheritance_chain": result.inheritance_chain,
        "dataset_name": effective.get("dataset_name"),
        "scene_name": effective.get("data", {}).get("scene_name") if isinstance(effective.get("data"), dict) else None,
        "errors": result.errors,
        "warnings": result.warnings,
        "notes": result.notes,
        "valid": not result.errors,
    }


def print_result(result: Result) -> None:
    status = "PASS" if not result.errors else "FAIL"
    print("[%s] %s" % (status, result.requested))
    if result.resolved_path:
        print("  resolved: %s" % result.resolved_path)
    if result.effective and isinstance(result.effective.get("dataset_name"), str):
        data = result.effective.get("data", {})
        print("  dataset: %s scene=%s" % (result.effective["dataset_name"], data.get("scene_name")))
    for item in result.inheritance_chain:
        print("  inherited/loaded: %s" % item)
    for message in result.notes:
        print("  note: %s" % message)
    for message in result.warnings:
        print("  warning: %s" % message)
    for message in result.errors:
        print("  error: %s" % message)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Gaussian-SLAM YAML/data contracts without CUDA imports")
    parser.add_argument("configs", nargs="+", help="one or more explicit YAML config paths")
    parser.add_argument("--path-base", default=".", help="base for checking relative data paths (default: current directory)")
    parser.add_argument("--require-data", action="store_true", help="fail when the input path or required data files are absent")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable results")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    path_base = Path(args.path_base).expanduser().resolve()
    if not path_base.is_dir():
        print("ERROR: --path-base is not a directory: %s" % path_base, file=sys.stderr)
        return 2
    results = [validate_one(Path(config), path_base, args.require_data) for config in args.configs]
    if args.as_json:
        print(json.dumps([result_dict(result) for result in results], indent=2, sort_keys=True))
    else:
        for result in results:
            print_result(result)
    return 1 if any(result.errors for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
