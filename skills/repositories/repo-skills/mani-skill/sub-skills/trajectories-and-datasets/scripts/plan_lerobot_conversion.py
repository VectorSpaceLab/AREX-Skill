#!/usr/bin/env python3
"""Plan a ManiSkill-to-LeRobot conversion without writing any files."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
from pathlib import Path
from typing import Any

try:
    import h5py  # type: ignore
except Exception as exc:  # pragma: no cover - depends on user env
    h5py = None
    H5PY_ERROR = exc
else:
    H5PY_ERROR = None


def has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def shell_join(cmd: list[str]) -> str:
    return " \\\n  ".join(shlex.quote(x) for x in cmd)


def load_metadata(path: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    json_path = path.with_suffix(".json")
    if not path.exists():
        warnings.append(f"HDF5 file does not exist: {path}")
    if not json_path.exists():
        warnings.append(f"sibling JSON metadata file is missing: {json_path}")
        return {}, warnings
    try:
        return json.loads(json_path.read_text(encoding="utf-8")), warnings
    except Exception as exc:
        warnings.append(f"could not parse JSON metadata: {exc}")
        return {}, warnings


def inspect_h5(path: Path) -> tuple[dict[str, Any], list[str]]:
    info = {"traj_count": None, "rgb_cameras": [], "has_robot_state": False, "has_obs": False}
    warnings: list[str] = []
    if h5py is None:
        warnings.append(f"h5py import failed: {H5PY_ERROR}")
        return info, warnings
    if not path.exists():
        return info, warnings
    try:
        with h5py.File(path, "r") as f:
            keys = sorted(k for k in f.keys() if k.startswith("traj_"))
            info["traj_count"] = len(keys)
            if not keys:
                warnings.append("no HDF5 keys starting with 'traj_' were found")
                return info, warnings
            first = f[keys[0]]
            info["has_obs"] = "obs" in first
            if "obs" in first:
                obs = first["obs"]
                if "sensor_data" in obs:
                    cams = []
                    for camera_name in obs["sensor_data"].keys():
                        if "rgb" in obs["sensor_data"][camera_name]:
                            cams.append(camera_name)
                    info["rgb_cameras"] = cams
                info["has_robot_state"] = "agent" in obs and "qpos" in obs["agent"]
    except Exception as exc:
        warnings.append(f"could not inspect HDF5: {exc}")
    return info, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traj_path", type=Path, help="Path to a ManiSkill .h5 trajectory")
    parser.add_argument("output_dir", type=Path, help="Planned LeRobot output directory")
    parser.add_argument("--task-name", help="Task description to pass to the converter")
    parser.add_argument("--fps", type=int, default=30, help="Video/timestamp FPS")
    parser.add_argument("--chunks-size", type=int, default=1000, help="Episodes per parquet chunk")
    parser.add_argument("--image-size", default="640x480", help="Output image size as WIDTHxHEIGHT or square size")
    parser.add_argument("--robot-type", help="Robot type override")
    args = parser.parse_args()

    metadata, warnings = load_metadata(args.traj_path)
    h5_info, h5_warnings = inspect_h5(args.traj_path)
    warnings.extend(h5_warnings)

    env_info = metadata.get("env_info", {}) or {}
    task_name = args.task_name or env_info.get("env_id") or None

    cmd = [
        "python",
        "-m",
        "mani_skill.trajectory.convert_to_lerobot",
        "--traj-path",
        str(args.traj_path),
        "--output-dir",
        str(args.output_dir),
        "--fps",
        str(args.fps),
        "--chunks-size",
        str(args.chunks_size),
        "--image-size",
        args.image_size,
    ]
    if args.task_name:
        cmd.extend(["--task-name", args.task_name])
    if args.robot_type:
        cmd.extend(["--robot-type", args.robot_type])

    deps = {
        "pandas": has_module("pandas"),
        "pyarrow": has_module("pyarrow"),
        "lerobot": has_module("lerobot"),
        "cv2": has_module("cv2"),
        "h5py": h5py is not None,
    }
    if not deps["pandas"]:
        warnings.append("pandas is missing; the converter imports pandas before CLI help")
    if not deps["cv2"]:
        warnings.append("cv2/OpenCV is missing; video/image conversion will fail")
    if not deps["pyarrow"] and not deps["lerobot"]:
        warnings.append("pyarrow or full lerobot is missing; parquet writing is likely to fail")
    if not h5_info.get("rgb_cameras"):
        warnings.append("no RGB cameras detected in the first trajectory; LeRobot output may have no videos")
    if not h5_info.get("has_robot_state"):
        warnings.append("no obs/agent/qpos robot state detected in the first trajectory")

    print("Planned command (not executed):")
    print(shell_join(cmd))
    print("\nDetected metadata:")
    print(f"  env_id: {env_info.get('env_id')}")
    print(f"  task_name_used_by_default: {task_name}")
    print(f"  trajectory_count: {h5_info.get('traj_count')}")
    print(f"  rgb_cameras: {h5_info.get('rgb_cameras')}")
    print(f"  has_robot_state: {h5_info.get('has_robot_state')}")
    print("\nDependency visibility:")
    for name, present in deps.items():
        print(f"  {name}: {present}")
    fatal = not args.traj_path.exists() or not args.traj_path.with_suffix(".json").exists()
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    return 1 if fatal else 0


if __name__ == "__main__":
    raise SystemExit(main())
