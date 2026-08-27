#!/usr/bin/env python3
"""Validate a Gaussian-SLAM config/CLI plan without starting SLAM.

This script only reads YAML and prints diagnostics. It never imports the
repository runtime, allocates CUDA tensors, downloads data, starts SLAM, logs
into W&B, or submits a job.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


REQUIRED_ROOT = ("dataset_name", "data", "mapping", "tracking", "cam", "seed", "use_wandb")
REQUIRED_DATA = ("scene_name", "input_path", "output_path")
REQUIRED_MAPPING = (
    "new_submap_every", "map_every", "iterations", "new_submap_iterations",
    "new_submap_points_num", "new_submap_gradient_points_num",
    "new_frame_sample_size", "new_points_radius", "current_view_opt_iterations",
    "alpha_thre", "pruning_thre", "submap_using_motion_heuristic",
)
REQUIRED_TRACKING = (
    "w_color_loss", "iterations", "cam_rot_lr", "cam_trans_lr", "odometry_type",
    "help_camera_initialization", "init_err_ratio", "odometer_method",
    "filter_alpha", "filter_outlier_depth", "alpha_thre", "soft_alpha",
    "mask_invalid_depth",
)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Safely inspect a Gaussian-SLAM config and documented CLI overrides."
    )
    p.add_argument("config_path", help="YAML config to inspect; no runtime is started")
    p.add_argument("--input_path", default=None, help="planned data.input_path override")
    p.add_argument("--output_path", default=None, help="planned data.output_path override")
    p.add_argument("--seed", type=int, default=None, help="planned seed override")
    p.add_argument("--track_w_color_loss", type=float, default=None)
    p.add_argument("--gt_camera", action="store_true")
    p.add_argument("--track_iters", type=int, default=None)
    p.add_argument("--map_every", type=int, default=None)
    p.add_argument("--map_iters", type=int, default=None)
    p.add_argument("--new_submap_every", type=int, default=None)
    p.add_argument("--check_input", action="store_true", help="check that the planned input path exists")
    p.add_argument("--json", action="store_true", help="emit a JSON report")
    return p


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required by this checker") from exc
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("top-level YAML value must be a mapping")
    inherit = value.get("inherit_from")
    # Match repository behavior: the path is opened as written, not relative
    # to the child file. This makes a working-directory error visible.
    if inherit:
        parent = load_yaml(Path(str(inherit)))

        def merge(base: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
            result = dict(base)
            for key, child_value in child.items():
                if isinstance(child_value, dict) and isinstance(result.get(key), dict):
                    result[key] = merge(result[key], child_value)
                else:
                    result[key] = child_value
            return result

        # Recursively merge nested mappings, as io_utils.update_recursive does.
        return merge(parent, value)
    return value


def missing(mapping: Any, keys: tuple[str, ...], prefix: str) -> list[str]:
    if not isinstance(mapping, dict):
        return [prefix]
    return [f"{prefix}.{key}" for key in keys if key not in mapping]


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    report: dict[str, Any] = {
        "config": args.config_path,
        "safe_only": True,
        "runtime_started": False,
        "errors": [],
        "warnings": [],
        "planned_overrides": {},
    }
    config_path = Path(args.config_path)
    if not config_path.is_file():
        report["errors"].append(f"config does not exist: {config_path}")
    else:
        try:
            cfg = load_yaml(config_path)
        except Exception as exc:  # report diagnostics rather than a traceback
            report["errors"].append(f"config could not be loaded: {exc}")
            cfg = {}
        report["missing"] = (
            missing(cfg, REQUIRED_ROOT, "config")
            + missing(cfg.get("data"), REQUIRED_DATA, "data")
            + missing(cfg.get("mapping"), REQUIRED_MAPPING, "mapping")
            + missing(cfg.get("tracking"), REQUIRED_TRACKING, "tracking")
        )
        if report["missing"]:
            report["warnings"].append("required merged fields are missing; use a scene-specific config")
        if cfg.get("dataset_name") not in {"replica", "tum_rgbd", "scan_net", "scannetpp"}:
            report["warnings"].append("dataset_name is not one of the repository adapters")
        report["effective"] = {
            "dataset_name": cfg.get("dataset_name"),
            "scene_name": cfg.get("data", {}).get("scene_name") if isinstance(cfg.get("data"), dict) else None,
            "input_path": cfg.get("data", {}).get("input_path") if isinstance(cfg.get("data"), dict) else None,
            "output_path": cfg.get("data", {}).get("output_path") if isinstance(cfg.get("data"), dict) else None,
            "seed": cfg.get("seed"),
            "odometry_type": cfg.get("tracking", {}).get("odometry_type") if isinstance(cfg.get("tracking"), dict) else None,
            "use_wandb": cfg.get("use_wandb"),
        }
    for name in ("input_path", "output_path", "seed", "track_iters", "map_every", "map_iters", "new_submap_every"):
        value = getattr(args, name)
        if value is not None:
            report["planned_overrides"][name] = value
    if args.track_w_color_loss is not None:
        report["planned_overrides"]["track_w_color_loss"] = args.track_w_color_loss
        report["warnings"].append("--track_w_color_loss is parsed by run_slam.py but not applied; edit YAML")
    if args.gt_camera:
        report["planned_overrides"]["gt_camera"] = True
        report["warnings"].append("--gt_camera is parsed but ineffective; use tracking.odometry_type: gt in YAML")
    if args.seed == 0:
        report["warnings"].append("--seed 0 is ignored by the source truthiness check; use YAML seed: 0")
    for name in ("map_every", "map_iters", "new_submap_every"):
        if getattr(args, name) == 0:
            report["warnings"].append(f"--{name} 0 is ignored by the source truthiness check")
    if args.input_path:
        planned_input = Path(args.input_path)
        if args.check_input and not planned_input.exists():
            report["errors"].append(f"planned input path does not exist: {planned_input}")
    elif args.check_input and isinstance(report.get("effective"), dict):
        input_value = report["effective"].get("input_path")
        if input_value and not Path(str(input_value)).exists():
            report["errors"].append(f"configured input path does not exist: {input_value}")
    if os.environ.get("DISABLE_WANDB") == "true":
        report["warnings"].append("W&B is forced off by DISABLE_WANDB=true")
    report["warnings"].append("CUDA and extension readiness are not proved by this config-only checker")
    report["ok"] = not report["errors"]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"safe check: {'PASS' if report['ok'] else 'FAIL'} (runtime_started=false)")
        for key in ("effective", "planned_overrides"):
            if key in report:
                print(f"{key}: {report[key]}")
        for item in report.get("missing", []):
            print(f"missing: {item}")
        for item in report["warnings"]:
            print(f"warning: {item}")
        for item in report["errors"]:
            print(f"error: {item}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
