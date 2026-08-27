#!/usr/bin/env python3
"""Validate a saved SplaTAM reconstruction result directory.

This helper checks file presence and array shapes in params.npz. It does not
import torch, allocate CUDA tensors, open Open3D, or judge reconstruction quality.

Example:
  python sub-skills/reconstruction/scripts/check_result_bundle.py \
    --result-dir experiments/Replica/room0_0 --require-params
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


CORE_KEYS = [
    "means3D",
    "rgb_colors",
    "unnorm_rotations",
    "logit_opacities",
    "log_scales",
]
CAMERA_KEYS = [
    "intrinsics",
    "w2c",
    "org_width",
    "org_height",
    "gt_w2c_all_frames",
]
POSE_KEYS = ["cam_unnorm_rots", "cam_trans"]


def shape_of(value: Any) -> list[int] | str:
    try:
        return list(np.asarray(value).shape)
    except Exception:
        return "unavailable"


def validate_params(path: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {"path": str(path), "keys": {}, "num_gaussians": None}
    if not path.exists():
        return [f"missing params file: {path}"], summary

    try:
        params = dict(np.load(path, allow_pickle=True))
    except Exception as exc:
        return [f"could not load params file: {type(exc).__name__}: {exc}"], summary

    for key in CORE_KEYS + CAMERA_KEYS + POSE_KEYS:
        if key in params:
            summary["keys"][key] = shape_of(params[key])
        else:
            severity = "missing core key" if key in CORE_KEYS else "missing metadata key"
            errors.append(f"{severity}: {key}")

    if "means3D" in params:
        means = np.asarray(params["means3D"])
        if means.ndim != 2 or means.shape[1] != 3:
            errors.append(f"means3D should have shape [N, 3], got {means.shape}")
        else:
            summary["num_gaussians"] = int(means.shape[0])

    if "rgb_colors" in params and "means3D" in params:
        if np.asarray(params["rgb_colors"]).shape[0] != np.asarray(params["means3D"]).shape[0]:
            errors.append("rgb_colors length does not match means3D length")

    if "unnorm_rotations" in params:
        rots = np.asarray(params["unnorm_rotations"])
        if rots.ndim != 2 or rots.shape[1] != 4:
            errors.append(f"unnorm_rotations should have shape [N, 4], got {rots.shape}")

    if "logit_opacities" in params and "means3D" in params:
        if np.asarray(params["logit_opacities"]).shape[0] != np.asarray(params["means3D"]).shape[0]:
            errors.append("logit_opacities length does not match means3D length")

    if "log_scales" in params:
        scales = np.asarray(params["log_scales"])
        if scales.ndim != 2 or scales.shape[1] not in (1, 3):
            errors.append(f"log_scales should have shape [N, 1] or [N, 3], got {scales.shape}")

    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SplaTAM result directory files and params.npz schema.")
    parser.add_argument("--result-dir", required=True, type=Path, help="Directory such as <workdir>/<run_name>.")
    parser.add_argument("--require-params", action="store_true", help="Fail if params.npz is missing.")
    parser.add_argument("--require-config-copy", action="store_true", help="Fail if config.py copy is missing.")
    parser.add_argument("--require-ply", action="store_true", help="Fail if splat.ply is missing.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args()

    result_dir = args.result_dir
    errors: list[str] = []
    summary: dict[str, Any] = {"result_dir": str(result_dir), "files": {}, "params": None}

    if not result_dir.exists() or not result_dir.is_dir():
        errors.append(f"result directory does not exist or is not a directory: {result_dir}")
    else:
        for filename in ["config.py", "params.npz", "splat.ply"]:
            p = result_dir / filename
            summary["files"][filename] = p.exists()

        if args.require_config_copy and not (result_dir / "config.py").exists():
            errors.append("missing config.py copy")
        if args.require_ply and not (result_dir / "splat.ply").exists():
            errors.append("missing splat.ply")

        params_path = result_dir / "params.npz"
        if params_path.exists() or args.require_params:
            param_errors, param_summary = validate_params(params_path)
            errors.extend(param_errors)
            summary["params"] = param_summary

    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "summary": summary}, indent=2))
    else:
        print(f"Result directory: {result_dir}")
        for filename, present in summary["files"].items():
            print(f"  {filename}: {'present' if present else 'missing'}")
        if summary.get("params"):
            print(f"  params summary: {summary['params']}")
        if errors:
            print("Errors:")
            for error in errors:
                print(f"  - {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
