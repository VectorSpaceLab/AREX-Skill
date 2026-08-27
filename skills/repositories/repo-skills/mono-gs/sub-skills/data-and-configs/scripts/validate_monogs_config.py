#!/usr/bin/env python3
"""Validate MonoGS YAML configs and dataset layouts.

Usage:
    python scripts/validate_monogs_config.py [--check-files] [--repo-root PATH] CONFIG [CONFIG ...]

The validator resolves recursive `inherit_from` entries, checks the core
`Results` / `Dataset` / `Training` fields used by MonoGS, and optionally
verifies dataset-specific file layouts.
"""

import argparse
import copy
import sys
from pathlib import Path

import yaml

ALLOWED_DATASET_TYPES = {"tum", "replica", "euroc", "realsense"}
ALLOWED_SENSOR_TYPES = {"monocular", "depth", "stereo"}
ALLOWED_SENSOR_BY_TYPE = {
    "tum": {"monocular", "depth"},
    "replica": {"depth"},
    "euroc": {"stereo"},
    "realsense": {"monocular", "depth"},
}

RESULT_BOOL_FIELDS = [
    "save_results",
    "save_trj",
    "use_gui",
    "eval_rendering",
    "use_wandb",
]
RESULT_STRING_FIELDS = ["save_dir"]
RESULT_NUMBER_FIELDS = ["save_trj_kf_intv"]

DATASET_BOOL_FIELDS = ["adaptive_pointsize"]
DATASET_NUMBER_FIELDS = ["pcd_downsample", "pcd_downsample_init", "point_size"]
DATASET_OPTIONAL_BOOL_FIELDS = ["single_thread"]

TRAINING_BOOL_FIELDS = ["single_thread", "spherical_harmonics"]
TRAINING_NUMBER_FIELDS = [
    "init_itr_num",
    "init_gaussian_update",
    "init_gaussian_reset",
    "init_gaussian_th",
    "init_gaussian_extent",
    "tracking_itr_num",
    "mapping_itr_num",
    "gaussian_update_every",
    "gaussian_update_offset",
    "gaussian_th",
    "gaussian_extent",
    "gaussian_reset",
    "size_threshold",
    "kf_interval",
    "window_size",
    "pose_window",
    "edge_threshold",
    "rgb_boundary_threshold",
    "kf_translation",
    "kf_min_translation",
    "kf_overlap",
]
TRAINING_LR_FIELDS = ["cam_rot_delta", "cam_trans_delta"]

TUM_CALIBRATION_FIELDS = [
    ("fx", "number"),
    ("fy", "number"),
    ("cx", "number"),
    ("cy", "number"),
    ("k1", "number"),
    ("k2", "number"),
    ("p1", "number"),
    ("p2", "number"),
    ("k3", "number"),
    ("width", "number"),
    ("height", "number"),
    ("depth_scale", "number"),
    ("distorted", "bool"),
]

EUROC_RAW_FIELDS = [
    ("fx", "number"),
    ("fy", "number"),
    ("cx", "number"),
    ("cy", "number"),
    ("k1", "number"),
    ("k2", "number"),
    ("p1", "number"),
    ("p2", "number"),
    ("k3", "number"),
]


def find_repo_root(anchor):
    anchor = anchor.resolve()
    for candidate in [anchor] + list(anchor.parents):
        if (candidate / "slam.py").is_file() and (candidate / "configs").is_dir():
            return candidate
    return Path.cwd().resolve()


def log_error(errors, label, message):
    errors.append("{}: {}".format(label, message))


def lookup(node, path):
    current = node
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def ensure_path(node, path, label, errors):
    found, value = lookup(node, path)
    if not found:
        log_error(errors, label, "missing {}".format(".".join(path)))
        return False, None
    return True, value


def ensure_mapping(node, path, label, errors):
    found, value = ensure_path(node, path, label, errors)
    if not found:
        return None
    if not isinstance(value, dict):
        log_error(errors, label, "{} must be a mapping".format(".".join(path)))
        return None
    return value


def ensure_bool(node, path, label, errors):
    found, value = ensure_path(node, path, label, errors)
    if not found:
        return None
    if not isinstance(value, bool):
        log_error(errors, label, "{} must be boolean".format(".".join(path)))
    return value


def ensure_number(node, path, label, errors):
    found, value = ensure_path(node, path, label, errors)
    if not found:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        log_error(errors, label, "{} must be numeric".format(".".join(path)))
    return value


def ensure_string(node, path, label, errors):
    found, value = ensure_path(node, path, label, errors)
    if not found:
        return None
    if not isinstance(value, str) or not value.strip():
        log_error(errors, label, "{} must be a non-empty string".format(".".join(path)))
    return value


def ensure_choice(node, path, label, errors, choices):
    value = ensure_string(node, path, label, errors)
    if value is None:
        return None
    if value not in choices:
        log_error(
            errors,
            label,
            "{} must be one of {}".format(".".join(path), ", ".join(sorted(choices))),
        )
    return value


def merge_dicts(base, overlay):
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def resolve_existing_path(raw_path, bases):
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    if candidate.exists():
        return candidate.resolve()
    for base in bases:
        test_path = (base / candidate).expanduser()
        if test_path.exists():
            return test_path.resolve()
    return None


def load_yaml_file(path):
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("{} must contain a top-level mapping".format(path))
    return data


def load_config(path, repo_root, cache, loading):
    resolved = resolve_existing_path(path, [Path.cwd().resolve(), repo_root])
    if resolved is None:
        raise FileNotFoundError("could not find config file: {}".format(path))
    resolved = resolved.resolve()
    if resolved in cache:
        return copy.deepcopy(cache[resolved])
    if resolved in loading:
        raise ValueError("inheritance cycle detected at {}".format(resolved))

    loading.add(resolved)
    try:
        data = load_yaml_file(resolved)
        inherit_from = data.get("inherit_from")
        base = {}
        if inherit_from:
            parent = resolve_existing_path(
                inherit_from,
                [resolved.parent, repo_root, Path.cwd().resolve()],
            )
            if parent is None:
                raise FileNotFoundError(
                    "could not resolve inherit_from '{}' from {}".format(
                        inherit_from, resolved
                    )
                )
            base = load_config(parent, repo_root, cache, loading)
        merged = merge_dicts(base, data)
        cache[resolved] = merged
        return copy.deepcopy(merged)
    finally:
        loading.discard(resolved)


def validate_common_sections(cfg, label, errors):
    results = ensure_mapping(cfg, ["Results"], label, errors)
    dataset = ensure_mapping(cfg, ["Dataset"], label, errors)
    training = ensure_mapping(cfg, ["Training"], label, errors)

    if results is None or dataset is None or training is None:
        return

    for field in RESULT_BOOL_FIELDS:
        ensure_bool(results, [field], label, errors)
    for field in RESULT_STRING_FIELDS:
        ensure_string(results, [field], label, errors)
    for field in RESULT_NUMBER_FIELDS:
        ensure_number(results, [field], label, errors)

    dataset_type = ensure_choice(
        dataset, ["type"], label, errors, ALLOWED_DATASET_TYPES
    )
    sensor_type = ensure_choice(
        dataset, ["sensor_type"], label, errors, ALLOWED_SENSOR_TYPES
    )

    for field in DATASET_BOOL_FIELDS:
        ensure_bool(dataset, [field], label, errors)
    for field in DATASET_NUMBER_FIELDS:
        ensure_number(dataset, [field], label, errors)
    for field in DATASET_OPTIONAL_BOOL_FIELDS:
        if field in dataset:
            ensure_bool(dataset, [field], label, errors)

    if dataset_type in ALLOWED_SENSOR_BY_TYPE and sensor_type is not None:
        if sensor_type not in ALLOWED_SENSOR_BY_TYPE[dataset_type]:
            log_error(
                errors,
                label,
                "Dataset.sensor_type '{}' is not valid for dataset type '{}'".format(
                    sensor_type, dataset_type
                ),
            )

    for field in TRAINING_BOOL_FIELDS:
        ensure_bool(training, [field], label, errors)
    for field in TRAINING_NUMBER_FIELDS:
        ensure_number(training, [field], label, errors)

    lr = ensure_mapping(training, ["lr"], label, errors)
    if lr is not None:
        for field in TRAINING_LR_FIELDS:
            ensure_number(lr, [field], label, errors)


def validate_tum_calibration(dataset, label, errors):
    calibration = ensure_mapping(dataset, ["Calibration"], label, errors)
    if calibration is None:
        return
    for field, kind in TUM_CALIBRATION_FIELDS:
        if kind == "bool":
            ensure_bool(calibration, [field], label, errors)
        else:
            ensure_number(calibration, [field], label, errors)


def validate_replica_calibration(dataset, label, errors):
    validate_tum_calibration(dataset, label, errors)


def validate_euroc_calibration(dataset, label, errors):
    calibration = ensure_mapping(dataset, ["Calibration"], label, errors)
    if calibration is None:
        return

    for camera in ["cam0", "cam1"]:
        camera_block = ensure_mapping(calibration, [camera], label, errors)
        if camera_block is None:
            continue

        for block_name in ["raw", "opt"]:
            block = ensure_mapping(camera_block, [block_name], label, errors)
            if block is None:
                continue
            for field, _kind in EUROC_RAW_FIELDS:
                ensure_number(block, [field], label, errors)

        rectification = ensure_mapping(camera_block, ["R"], label, errors)
        if rectification is None:
            continue
        rows = ensure_number(rectification, ["rows"], label, errors)
        cols = ensure_number(rectification, ["cols"], label, errors)
        if rows == 3 and cols == 3:
            pass
        elif rows is not None and cols is not None:
            log_error(
                errors,
                label,
                "Calibration.{}.R.rows and cols must both be 3".format(camera),
            )
        found, data = lookup(rectification, ["data"])
        if not found:
            log_error(errors, label, "Calibration.{}.R.data is missing".format(camera))
        elif not isinstance(data, (list, tuple)):
            log_error(errors, label, "Calibration.{}.R.data must be a sequence".format(camera))
        else:
            if len(data) != 9:
                log_error(
                    errors,
                    label,
                    "Calibration.{}.R.data must contain 9 values".format(camera),
                )
            for index, value in enumerate(data):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    log_error(
                        errors,
                        label,
                        "Calibration.{}.R.data[{}] must be numeric".format(camera, index),
                    )


def resolve_dataset_root(dataset_path, repo_root):
    return resolve_existing_path(dataset_path, [repo_root, Path.cwd().resolve()])


def validate_tum_files(dataset_root, label, errors):
    rgb_txt = dataset_root / "rgb.txt"
    depth_txt = dataset_root / "depth.txt"
    pose_txt = dataset_root / "groundtruth.txt"
    alt_pose_txt = dataset_root / "pose.txt"

    for required in [rgb_txt, depth_txt]:
        if not required.is_file():
            log_error(errors, label, "missing {}".format(required.name))

    if not pose_txt.is_file() and not alt_pose_txt.is_file():
        log_error(errors, label, "missing groundtruth.txt or pose.txt")

    if not rgb_txt.is_file() or not depth_txt.is_file():
        return

    def collect_relative_paths(manifest_path):
        paths = []
        with manifest_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts = stripped.split()
                if len(parts) < 2:
                    continue
                paths.append(parts[1])
        return paths

    rgb_entries = collect_relative_paths(rgb_txt)
    depth_entries = collect_relative_paths(depth_txt)

    if not rgb_entries:
        log_error(errors, label, "rgb.txt does not list any frames")
    if not depth_entries:
        log_error(errors, label, "depth.txt does not list any frames")

    for rel_path in rgb_entries:
        ref = Path(rel_path)
        target = ref if ref.is_absolute() else dataset_root / ref
        if not target.is_file():
            log_error(errors, label, "missing RGB frame referenced by rgb.txt: {}".format(rel_path))
            break

    for rel_path in depth_entries:
        ref = Path(rel_path)
        target = ref if ref.is_absolute() else dataset_root / ref
        if not target.is_file():
            log_error(errors, label, "missing depth frame referenced by depth.txt: {}".format(rel_path))
            break


def validate_replica_files(dataset_root, label, errors):
    results_dir = dataset_root / "results"
    traj_file = dataset_root / "traj.txt"

    if not results_dir.is_dir():
        log_error(errors, label, "missing results/ directory")
        return
    if not traj_file.is_file():
        log_error(errors, label, "missing traj.txt")
        return

    color_frames = sorted(results_dir.glob("frame*.jpg"))
    depth_frames = sorted(results_dir.glob("depth*.png"))

    if not color_frames:
        log_error(errors, label, "no frame*.jpg files found under results/")
    if not depth_frames:
        log_error(errors, label, "no depth*.png files found under results/")
    if color_frames and depth_frames and len(color_frames) != len(depth_frames):
        log_error(
            errors,
            label,
            "frame and depth counts differ under results/ ({} vs {})".format(
                len(color_frames), len(depth_frames)
            ),
        )

    with traj_file.open("r", encoding="utf-8") as handle:
        trajectory_lines = [line for line in handle if line.strip()]

    if color_frames and len(trajectory_lines) < len(color_frames):
        log_error(
            errors,
            label,
            "traj.txt has fewer lines than frame*.jpg files ({} vs {})".format(
                len(trajectory_lines), len(color_frames)
            ),
        )


def validate_euroc_files(dataset_root, label, errors, dataset):
    cam0 = dataset_root / "mav0" / "cam0" / "data"
    cam1 = dataset_root / "mav0" / "cam1" / "data"
    pose_csv = dataset_root / "mav0" / "state_groundtruth_estimate0" / "data.csv"

    if not cam0.is_dir():
        log_error(errors, label, "missing mav0/cam0/data")
    if not cam1.is_dir():
        log_error(errors, label, "missing mav0/cam1/data")
    if not pose_csv.is_file():
        log_error(errors, label, "missing mav0/state_groundtruth_estimate0/data.csv")

    if not cam0.is_dir() or not cam1.is_dir() or not pose_csv.is_file():
        return

    cam0_frames = sorted(cam0.glob("*.png"))
    cam1_frames = sorted(cam1.glob("*.png"))

    if not cam0_frames:
        log_error(errors, label, "no cam0 PNG frames found")
    if not cam1_frames:
        log_error(errors, label, "no cam1 PNG frames found")
    if cam0_frames and cam1_frames and len(cam0_frames) != len(cam1_frames):
        log_error(
            errors,
            label,
            "cam0 and cam1 frame counts differ ({} vs {})".format(
                len(cam0_frames), len(cam1_frames)
            ),
        )

    start_idx = dataset.get("start_idx")
    if start_idx is None:
        log_error(errors, label, "missing Dataset.start_idx")
    elif isinstance(start_idx, bool) or not isinstance(start_idx, int):
        log_error(errors, label, "Dataset.start_idx must be an integer")
    elif start_idx < 0:
        log_error(errors, label, "Dataset.start_idx must be non-negative")
    elif cam0_frames and start_idx >= len(cam0_frames):
        log_error(
            errors,
            label,
            "Dataset.start_idx must be smaller than the camera frame count ({} >= {})".format(
                start_idx, len(cam0_frames)
            ),
        )


def validate_real_sense_files(dataset, repo_root, label, errors, check_files):
    dataset_path = dataset.get("dataset_path")
    if not dataset_path:
        return
    if not check_files:
        return
    dataset_root = resolve_dataset_root(dataset_path, repo_root)
    if dataset_root is None or not dataset_root.is_dir():
        log_error(errors, label, "dataset_path does not exist: {}".format(dataset_path))


def validate_dataset_specific(cfg, label, repo_root, check_files, errors):
    dataset = ensure_mapping(cfg, ["Dataset"], label, errors)
    if dataset is None:
        return

    dataset_type = dataset.get("type")
    if not isinstance(dataset_type, str):
        return

    dataset_path = dataset.get("dataset_path")
    if dataset_type in {"tum", "replica", "euroc"}:
        if not dataset_path:
            log_error(errors, label, "missing Dataset.dataset_path")
            return
        if not isinstance(dataset_path, str) or not dataset_path.strip():
            log_error(errors, label, "Dataset.dataset_path must be a non-empty string")
            return

        if dataset_type == "tum":
            validate_tum_calibration(dataset, label, errors)
        elif dataset_type == "replica":
            validate_replica_calibration(dataset, label, errors)
        elif dataset_type == "euroc":
            validate_euroc_calibration(dataset, label, errors)

        if check_files:
            dataset_root = resolve_dataset_root(dataset_path, repo_root)
            if dataset_root is None or not dataset_root.is_dir():
                log_error(errors, label, "dataset_path does not exist: {}".format(dataset_path))
                return
            if dataset_type == "tum":
                validate_tum_files(dataset_root, label, errors)
            elif dataset_type == "replica":
                validate_replica_files(dataset_root, label, errors)
            elif dataset_type == "euroc":
                validate_euroc_files(dataset_root, label, errors, dataset)
    elif dataset_type == "realsense":
        if check_files:
            validate_real_sense_files(dataset, repo_root, label, errors, check_files)
    else:
        log_error(errors, label, "unsupported Dataset.type: {}".format(dataset_type))


def validate_config(raw_path, repo_root, cache, loading, check_files):
    errors = []
    try:
        cfg = load_config(raw_path, repo_root, cache, loading)
    except Exception as exc:
        log_error(errors, raw_path, str(exc))
        return errors

    validate_common_sections(cfg, raw_path, errors)
    validate_dataset_specific(cfg, raw_path, repo_root, check_files, errors)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate MonoGS YAML inheritance, required sections, and dataset layouts.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Also verify dataset-specific files and directories.",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Override the detected MonoGS repository root.",
    )
    parser.add_argument("configs", nargs="+", help="One or more MonoGS config files.")
    args = parser.parse_args(argv)

    if args.repo_root is not None:
        repo_root = Path(args.repo_root).expanduser().resolve()
    else:
        repo_root = find_repo_root(Path(__file__).resolve())

    cache = {}
    loading = set()
    any_errors = False

    for raw_path in args.configs:
        errors = validate_config(raw_path, repo_root, cache, loading, args.check_files)
        if errors:
            any_errors = True
            print("{}:".format(raw_path), file=sys.stderr)
            for error in errors:
                print("  - {}".format(error), file=sys.stderr)
        else:
            print("{}: ok".format(raw_path))

    return 1 if any_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
