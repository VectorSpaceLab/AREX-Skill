#!/usr/bin/env python3
"""Safely preflight a TransFuser training setup.

This helper checks paths, dataset layout, split coverage, DDP launch variables,
and optionally imports the legacy runtime/CUDA stack. It never trains, creates a
model, downloads weights, launches torchrun, or mutates the dataset.

Examples:
  python validate_training_setup.py --dataset-root DATA --setting 02_05_withheld \
      --backbone transFuser --parallel-training 0 --strict
  python validate_training_setup.py --repo-root CHECKOUT --check-runtime \
      --dataset-root DATA --parallel-training 0
"""

from __future__ import print_function

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


BACKBONES = ("transFuser", "late_fusion", "latentTF", "geometric_fusion")
SETTINGS = ("all", "02_05_withheld", "eval")
MODALITIES = {
    "rgb": lambda frame: "%04d.png" % frame,
    "depth": lambda frame: "%04d.png" % frame,
    "semantics": lambda frame: "%04d.png" % frame,
    "topdown": lambda frame: "encoded_%04d.png" % frame,
    "lidar": lambda frame: "%04d.npy" % frame,
    "measurements": lambda frame: "%04d.json" % frame,
}
LABEL_FIELDS = (
    "id", "ego_matrix", "num_points", "position", "extent", "yaw", "speed", "brake"
)
MEASUREMENT_FIELDS = (
    "ego_matrix", "steer", "throttle", "brake", "light_hazard", "speed",
    "theta", "x", "y", "x_command", "y_command",
)


class Reporter(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.notes = []

    def error(self, message):
        self.errors.append(message)
        print("ERROR: " + message)

    def warning(self, message):
        self.warnings.append(message)
        print("WARNING: " + message)

    def note(self, message):
        self.notes.append(message)
        print("OK: " + message)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Validate TransFuser paths, split coverage, data filenames, DDP "
            "variables, and optionally the CUDA/import runtime. No training "
            "or downloads are performed."
        )
    )
    parser.add_argument("--repo-root", help="TransFuser checkout; required by --check-runtime")
    parser.add_argument("--dataset-root", help="Dataset root containing scenario/town/route directories")
    parser.add_argument("--setting", choices=SETTINGS, default="all")
    parser.add_argument("--backbone", default="transFuser")
    parser.add_argument("--image-architecture", default="regnety_032")
    parser.add_argument("--lidar-architecture", default="regnety_032")
    parser.add_argument("--parallel-training", type=int, choices=(0, 1), default=0)
    parser.add_argument("--use-point-pillars", type=int, choices=(0, 1), default=0)
    parser.add_argument("--use-target-point-image", type=int, choices=(0, 1), default=1)
    parser.add_argument("--multitask", type=int, choices=(0, 1), default=1)
    parser.add_argument("--seq-len", type=int, default=1)
    parser.add_argument("--pred-len", type=int, default=4)
    parser.add_argument("--max-routes", type=int, default=20,
                        help="Maximum route directories to inspect; 0 means all")
    parser.add_argument("--max-samples", type=int, default=20,
                        help="Maximum candidate frames to inspect; 0 means all")
    parser.add_argument("--check-runtime", action="store_true",
                        help="Import CUDA/OpenMMLab/TransFuser modules without building a model")
    parser.add_argument("--strict", action="store_true",
                        help="Return nonzero for warnings as well as errors")
    parser.add_argument("--json", dest="json_path",
                        help="Also write a JSON report to this explicit path")
    return parser.parse_args(argv)


def _is_dir(path):
    return path.is_dir()


def _scenario_town_roots(root):
    """Return (scenario, town, town_path) entries matching GlobalConfig's tree."""
    entries = []
    if not root.is_dir():
        return entries
    for scenario in sorted(p for p in root.iterdir() if p.is_dir()):
        for town in sorted(p for p in scenario.iterdir() if p.is_dir()):
            entries.append((scenario.name, town.name, town))
    return entries


def _split_towns(town_roots, setting):
    if setting == "02_05_withheld":
        val = [x for x in town_roots if "Town02" in x[1] or "Town05" in x[1]]
        train = [x for x in town_roots if x not in val]
        return train, val
    if setting == "eval":
        return [], []
    # The source uses every scenario as training and first scenario as the
    # nominal val group, although train.py does not validate for setting=all.
    train = list(town_roots)
    first_scenario = town_roots[0][0] if town_roots else None
    val = [x for x in town_roots if x[0] == first_scenario]
    return train, val


def _route_list(town_entries):
    routes = []
    for scenario, town, town_path in town_entries:
        for route in sorted(p for p in town_path.iterdir() if p.is_dir()):
            routes.append((scenario, town, route.name, route))
    return routes


def _candidate_frames(lidar_dir, pred_len, seq_len):
    try:
        num_seq = len(list(lidar_dir.iterdir()))
    except OSError:
        return []
    # Matches range(2, num_seq - pred_len - seq_len - 2) in CARLA_Data.
    return list(range(2, num_seq - pred_len - seq_len - 2))


def _check_json(path, required, reporter, label):
    try:
        with path.open("r") as handle:
            value = json.load(handle)
    except Exception as exc:
        reporter.error("%s is not valid JSON (%s): %s" % (label, path, exc))
        return None
    if not isinstance(value, (dict, list)):
        reporter.error("%s must decode to an object or list: %s" % (label, path))
        return value
    if isinstance(value, dict):
        missing = [key for key in required if key not in value]
        if missing:
            reporter.error("%s is missing keys %s: %s" % (label, ", ".join(missing), path))
    return value


def check_dataset(args, reporter):
    if not args.dataset_root:
        reporter.warning("No --dataset-root supplied; skipped dataset tree and sample checks")
        return {"train_towns": 0, "val_towns": 0, "routes": 0, "samples": 0}

    root = Path(args.dataset_root).expanduser()
    if not root.exists():
        reporter.error("dataset root does not exist: %s" % root)
        return {"train_towns": 0, "val_towns": 0, "routes": 0, "samples": 0}
    if not root.is_dir():
        reporter.error("dataset root is not a directory: %s" % root)
        return {"train_towns": 0, "val_towns": 0, "routes": 0, "samples": 0}

    town_roots = _scenario_town_roots(root)
    if not town_roots:
        reporter.error("dataset has no scenario/town directories under %s" % root)
        return {"train_towns": 0, "val_towns": 0, "routes": 0, "samples": 0}

    train_towns, val_towns = _split_towns(town_roots, args.setting)
    if args.setting == "eval":
        reporter.warning("setting=eval leaves train/validation lists unset; it is not a train.py dataset setting")
    elif not train_towns:
        reporter.error("training split is empty for setting=%s" % args.setting)
    if args.setting == "02_05_withheld" and not val_towns:
        reporter.error("02_05_withheld found no Town02/Town05 validation town names")
    if args.setting == "02_05_withheld" and not train_towns:
        reporter.error("02_05_withheld excluded every town; no training data remains")

    route_entries = _route_list(town_roots)
    if args.max_routes > 0:
        route_entries = route_entries[:args.max_routes]
    if not route_entries:
        reporter.error("no route directories found below scenario/town directories")

    expected_future = args.seq_len + args.pred_len
    samples_seen = 0
    eligible_routes = 0
    missing_counts = Counter()
    checked_sample_paths = set()

    for scenario, town, route_name, route in route_entries:
        missing_modality_dirs = [name for name in MODALITIES if not (route / name).is_dir()]
        if missing_modality_dirs:
            reporter.error("%s/%s/%s is missing modality directories: %s" %
                           (scenario, town, route_name, ", ".join(missing_modality_dirs)))
            continue
        frames = _candidate_frames(route / "lidar", args.pred_len, args.seq_len)
        if not frames:
            missing_counts["too_short"] += 1
            reporter.warning("route has no eligible frames after loader margins: %s" % route)
            continue
        eligible_routes += 1
        for frame in frames:
            if args.max_samples > 0 and samples_seen >= args.max_samples:
                break
            samples_seen += 1
            # Current-frame modalities.
            required_paths = []
            for modality, formatter in MODALITIES.items():
                required_paths.append((modality, route / modality / formatter(frame)))
            # Current and future labels.
            for offset in range(expected_future):
                label_frame = frame + offset
                required_paths.append(("label_raw", route / "label_raw" / ("%04d.json" % label_frame)))
            for kind, path in required_paths:
                if not path.is_file():
                    key = "%s:%s" % (kind, path.name)
                    missing_counts[key] += 1
                    if key not in checked_sample_paths:
                        reporter.error("sample %s frame %04d is missing %s: %s" %
                                       (route, frame, kind, path))
                        checked_sample_paths.add(key)

            measurements = route / "measurements" / ("%04d.json" % frame)
            if measurements.is_file():
                _check_json(measurements, MEASUREMENT_FIELDS, reporter, "measurement")
            labels = route / "label_raw" / ("%04d.json" % frame)
            if labels.is_file():
                parsed = _check_json(labels, (), reporter, "label")
                if isinstance(parsed, list):
                    if not parsed:
                        reporter.error("label list is empty; ego object is required: %s" % labels)
                    for idx, obj in enumerate(parsed[:20]):
                        if not isinstance(obj, dict):
                            reporter.error("label entry %d is not an object: %s" % (idx, labels))
                            continue
                        missing = [key for key in LABEL_FIELDS if key not in obj]
                        if missing:
                            reporter.error("label entry %d is missing keys %s: %s" %
                                           (idx, ", ".join(missing), labels))
            # Only inspect a bounded sample set, but continue route coverage.
        if args.max_samples > 0 and samples_seen >= args.max_samples:
            # route-level coverage is enough after the bounded sample budget.
            continue

    if samples_seen == 0 and args.setting != "eval":
        reporter.error("no candidate training samples were inspected")
    reporter.note("dataset split: %d train town roots, %d validation town roots; inspected %d/%d routes and %d samples" %
                  (len(train_towns), len(val_towns), len(route_entries), eligible_routes, samples_seen))
    if missing_counts:
        reporter.note("dataset findings: %s" % dict(missing_counts))
    return {
        "train_towns": len(train_towns),
        "val_towns": len(val_towns),
        "routes": len(route_entries),
        "eligible_routes": eligible_routes,
        "samples": samples_seen,
        "findings": dict(missing_counts),
    }


def check_cli_contract(args, reporter):
    if args.backbone not in BACKBONES:
        reporter.error("unsupported backbone %r; choose one of %s" % (args.backbone, ", ".join(BACKBONES)))
    if args.seq_len != 1:
        reporter.warning("seq_len=%d is outside the verified transformer contract; current GPT code supports sequence length 1" % args.seq_len)
    if args.pred_len <= 0:
        reporter.error("pred_len must be positive")
    if args.use_point_pillars and args.backbone == "geometric_fusion":
        reporter.warning("PointPillars + geometric_fusion is a coupled path; verify raw-point and correspondence tensor shapes before training")
    if args.use_point_pillars:
        reporter.note("PointPillars selected: raw XYZI, num_points, torch-scatter, and fixed 40000-point padding must be available")
    if args.setting == "eval":
        reporter.warning("setting=eval is for model-only configuration and should not be used to construct CARLA_Data in train.py")
    if args.image_architecture == "" or args.lidar_architecture == "":
        reporter.error("image and LiDAR architecture names must be non-empty")


def _int_env(name, reporter):
    value = os.environ.get(name)
    if value is None:
        reporter.error("parallel training requires torchrun environment variable %s" % name)
        return None
    try:
        return int(value)
    except ValueError:
        reporter.error("DDP environment variable %s is not an integer: %r" % (name, value))
        return None


def check_ddp(args, reporter):
    if not args.parallel_training:
        for name in ("RANK", "LOCAL_RANK", "WORLD_SIZE"):
            if name in os.environ:
                reporter.warning("%s is set although --parallel-training=0; it will be ignored by the script" % name)
        reporter.note("single-GPU mode selected; launch with --parallel_training 0 and provide a visible CUDA device")
        return {"mode": "single", "rank": 0, "local_rank": 0, "world_size": 1}
    rank = _int_env("RANK", reporter)
    local_rank = _int_env("LOCAL_RANK", reporter)
    world_size = _int_env("WORLD_SIZE", reporter)
    if world_size is not None and world_size < 1:
        reporter.error("WORLD_SIZE must be >= 1")
    if rank is not None and world_size is not None and not (0 <= rank < world_size):
        reporter.error("RANK=%d is outside WORLD_SIZE=%d" % (rank, world_size))
    if local_rank is not None and local_rank < 0:
        reporter.error("LOCAL_RANK must be nonnegative")
    reporter.note("DDP mode requested; torchrun must provide RANK/LOCAL_RANK/WORLD_SIZE before train.py starts")
    return {"mode": "ddp", "rank": rank, "local_rank": local_rank, "world_size": world_size}


def _version(module):
    return getattr(module, "__version__", "unknown")


def check_runtime(args, reporter):
    if not args.check_runtime:
        return {"checked": False}
    if not args.repo_root:
        reporter.error("--check-runtime requires --repo-root pointing to the TransFuser checkout")
        return {"checked": True, "imports": {}}
    repo_root = Path(args.repo_root).expanduser().resolve()
    package_dir = repo_root / "team_code_transfuser"
    if not package_dir.is_dir():
        reporter.error("repo root does not contain team_code_transfuser: %s" % repo_root)
        return {"checked": True, "imports": {}}

    # Avoid leaving bytecode in a source checkout during a read-only probe.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(package_dir))
    imports = {}
    try:
        import torch
        imports["torch"] = _version(torch)
        if not torch.cuda.is_available():
            reporter.error("torch imported but CUDA is unavailable; training has no CPU substitute")
        else:
            device = torch.device("cuda:0")
            try:
                probe = torch.zeros((1,), device=device)
                del probe
                reporter.note("CUDA allocation passed on %s" % torch.cuda.get_device_name(device))
            except Exception as exc:
                reporter.error("CUDA allocation failed: %s" % exc)
    except Exception as exc:
        reporter.error("cannot import torch: %s" % exc)

    for name in ("mmcv", "mmdet", "mmseg", "mmcls", "torch_scatter", "timm"):
        try:
            module = __import__(name)
            imports[name] = _version(module)
        except Exception as exc:
            reporter.error("missing or broken optional/runtime dependency %s: %s" % (name, exc))

    for name in ("config", "data", "model", "train"):
        try:
            __import__(name)
            imports[name] = "imported"
        except Exception as exc:
            reporter.error("TransFuser module %s failed to import: %s" % (name, exc))
    reporter.note("runtime import probe completed without model construction or downloads")
    return {"checked": True, "imports": imports}


def write_json(path, args, dataset, ddp, runtime, reporter):
    payload = {
        "schema": "transfuser.training-preflight.v1",
        "arguments": vars(args),
        "dataset": dataset,
        "ddp": ddp,
        "runtime": runtime,
        "errors": reporter.errors,
        "warnings": reporter.warnings,
        "notes": reporter.notes,
    }
    output = Path(path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    print("WROTE: %s" % output)


def main(argv=None):
    args = parse_args(argv)
    reporter = Reporter()
    check_cli_contract(args, reporter)
    ddp = check_ddp(args, reporter)
    dataset = check_dataset(args, reporter)
    runtime = check_runtime(args, reporter)
    if args.json_path:
        write_json(args.json_path, args, dataset, ddp, runtime, reporter)
    print("SUMMARY: %d error(s), %d warning(s)" % (len(reporter.errors), len(reporter.warnings)))
    if reporter.errors or (args.strict and reporter.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
