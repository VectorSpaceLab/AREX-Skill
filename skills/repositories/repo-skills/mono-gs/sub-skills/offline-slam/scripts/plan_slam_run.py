#!/usr/bin/env python3
"""
Print a safe MonoGS `slam.py` command and preflight warnings.

This helper never starts SLAM. It reads the selected YAML config, classifies the
workflow, checks common repository/data preconditions when requested, and prints
copyable command suggestions.
"""

import argparse
import glob
import shlex
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:  # noqa: BLE001
    print(f"ERROR: PyYAML is required: {exc}", file=sys.stderr)
    raise SystemExit(2)


def update_recursive(base, override):
    for key, value in (override or {}).items():
        if isinstance(value, dict):
            if key not in base or not isinstance(base[key], dict):
                base[key] = {}
            update_recursive(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path):
    path = Path(path).resolve()
    data = yaml.safe_load(path.read_text()) or {}
    parent_cfg = {}
    inherit_from = data.get("inherit_from")
    if inherit_from:
        parent = (path.parent / inherit_from).resolve()
        if not parent.exists():
            for ancestor in [path.parent] + list(path.parents):
                candidate = (ancestor / inherit_from).resolve()
                if candidate.exists():
                    parent = candidate
                    break
        parent_cfg = load_config(parent)
    update_recursive(parent_cfg, data)
    return parent_cfg


def dataset_exists(repo_root, cfg):
    dataset = cfg.get("Dataset", {})
    if dataset.get("type") == "realsense":
        return True, "live RealSense config: no offline dataset required"
    dataset_path = dataset.get("dataset_path")
    if not dataset_path:
        return False, "Dataset.dataset_path is missing"
    root = Path(dataset_path)
    if not root.is_absolute():
        root = repo_root / root
    if not root.exists():
        return False, f"dataset_path does not exist: {root}"
    dtype = dataset.get("type")
    if dtype == "tum":
        ok = (root / "rgb.txt").exists() and (root / "depth.txt").exists() and ((root / "groundtruth.txt").exists() or (root / "pose.txt").exists())
        return ok, "TUM manifests found" if ok else "TUM root must contain rgb.txt, depth.txt, and groundtruth.txt or pose.txt"
    if dtype == "replica":
        color = glob.glob(str(root / "results" / "frame*.jpg"))
        depth = glob.glob(str(root / "results" / "depth*.png"))
        ok = bool(color) and bool(depth) and (root / "traj.txt").exists()
        return ok, "Replica frames and traj.txt found" if ok else "Replica root must contain results/frame*.jpg, results/depth*.png, and traj.txt"
    if dtype == "euroc":
        ok = bool(glob.glob(str(root / "mav0" / "cam0" / "data" / "*.png"))) and bool(glob.glob(str(root / "mav0" / "cam1" / "data" / "*.png"))) and (root / "mav0" / "state_groundtruth_estimate0" / "data.csv").exists()
        return ok, "EuRoC stereo frames and ground truth CSV found" if ok else "EuRoC root must contain cam0/cam1 data and state_groundtruth_estimate0/data.csv"
    return False, f"Unknown Dataset.type: {dtype}"


def classify(cfg):
    dataset = cfg.get("Dataset", {})
    dtype = dataset.get("type")
    sensor = dataset.get("sensor_type")
    if dtype == "tum" and sensor == "monocular":
        return "monocular TUM"
    if dtype == "tum" and sensor == "depth":
        return "RGB-D TUM"
    if dtype == "replica":
        return "RGB-D Replica"
    if dtype == "euroc":
        return "stereo EuRoC"
    if dtype == "realsense":
        return "live RealSense (route to live-demo)"
    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Plan a MonoGS offline SLAM command without running it.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="MonoGS repository root")
    parser.add_argument("--config", required=True, type=Path, help="Config path, absolute or relative to --repo-root")
    parser.add_argument("--eval", action="store_true", help="Plan an evaluation run with slam.py --eval")
    parser.add_argument("--headless", action="store_true", help="Warn if the selected config still enables the GUI")
    parser.add_argument("--check-files", action="store_true", help="Check repository and dataset files")
    parser.add_argument("--disable-wandb", action="store_true", help="Prefix evaluation command with WANDB_MODE=disabled")
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    config = args.config if args.config.is_absolute() else repo / args.config
    warnings = []
    errors = []

    if args.check_files:
        for rel in ["slam.py", "utils", "gaussian_splatting", "gui"]:
            if not (repo / rel).exists():
                errors.append(f"repo root missing {rel}")

    try:
        cfg = load_config(config)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot load config: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    workflow = classify(cfg)
    dataset = cfg.get("Dataset", {})
    results = cfg.get("Results", {})

    if dataset.get("type") == "realsense":
        warnings.append("This is a live RealSense config; use the live-demo sub-skill instead of offline-slam.")
    if args.headless and not args.eval and results.get("use_gui") is not False:
        warnings.append("The config enables Results.use_gui; create a copied config with Results.use_gui: false for a non-eval headless run. slam.py has no --headless flag.")
    if args.eval and not args.disable_wandb:
        warnings.append("slam.py --eval sets use_wandb=True. Use --disable-wandb here or set WANDB_MODE=disabled if no W&B login/network is available.")
    if workflow == "RGB-D Replica" and not str(config).endswith("_sp.yaml") and dataset.get("single_thread") is not True:
        warnings.append("For serialized Replica debugging, prefer an *_sp.yaml config that sets Dataset.single_thread: true.")

    if args.check_files:
        ok, detail = dataset_exists(repo, cfg)
        (warnings if ok else errors).append(detail)

    rel_config = config
    try:
        rel_config = config.relative_to(repo)
    except ValueError:
        pass
    command_parts = ["python", "slam.py", "--config", str(rel_config)]
    if args.eval:
        command_parts.append("--eval")
    command = " ".join(shlex.quote(p) for p in command_parts)
    if args.eval and args.disable_wandb:
        command = "WANDB_MODE=disabled " + command

    print(f"Workflow: {workflow}")
    print(f"Dataset.type: {dataset.get('type')}")
    print(f"Dataset.sensor_type: {dataset.get('sensor_type')}")
    print(f"Dataset.dataset_path: {dataset.get('dataset_path')}")
    print("Suggested command from the MonoGS repository root:")
    print(command)
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")
    if errors:
        print("Errors:")
        for item in errors:
            print(f"- {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
