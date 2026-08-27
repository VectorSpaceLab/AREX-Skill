#!/usr/bin/env python3
"""Run a tiny, deterministic LiDAR/FMCW scan smoke without repository assets."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a temporary two-sensor IR-SIM scene and inspect scan payloads."
    )
    parser.add_argument(
        "--sensor-type",
        choices=("lidar2d", "fmcw_lidar2d", "both"),
        default="both",
        help="Payload to inspect; both also checks robot-id convenience selection.",
    )
    parser.add_argument("--steps", type=int, default=1, help="Headless steps (default: 1).")
    parser.add_argument("--seed", type=int, default=7, help="IR-SIM RNG seed.")
    return parser


def _write_config(path: Path, sensor_type: str) -> None:
    sensor_blocks = {
        "lidar2d": """      - name: lidar2d
        range_min: 0.0
        range_max: 4.0
        angle_range: 0.0
        number: 1
        noise: false
        offset: [0.0, 0.0, 0.0]
""",
        "fmcw_lidar2d": """      - name: fmcw_lidar2d
        range_min: 0.0
        range_max: 4.0
        angle_range: 0.0
        number: 1
        noise: false
        motion_compensate: true
        offset: [0.0, 0.0, 0.0]
""",
    }
    sensors = (
        sensor_blocks["lidar2d"] + sensor_blocks["fmcw_lidar2d"]
        if sensor_type == "both"
        else sensor_blocks[sensor_type]
    )
    path.write_text(
        """world:
  width: 6
  height: 4
  step_time: 0.1
  sample_time: 0.1
  offset: [0, 0]
  collision_mode: unobstructed
  control_mode: auto
robot:
  - kinematics: {name: diff}
    shape: {name: circle, radius: 0.2}
    state: [1.0, 2.0, 0.0]
    static: true
    sensors:
"""
        + sensors
        + """obstacle:
  - shape: {name: circle, radius: 0.25}
    state: [3.0, 2.0, 0.0]
    static: true
""",
        encoding="utf-8",
    )


def main() -> int:
    args = _parser().parse_args()
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")

    os.environ.setdefault("MPLBACKEND", "Agg")
    import irsim
    from irsim.util.random import set_seed

    set_seed(args.seed)
    with tempfile.TemporaryDirectory(prefix="irsim-scan-smoke-") as tmp:
        config = Path(tmp) / "scene.yaml"
        _write_config(config, args.sensor_type)
        env = irsim.make(str(config), display=False, save_ani=False)
        try:
            for _ in range(args.steps):
                env.step()
            robot = env.robot_list[0]
            sensors = {sensor.sensor_type: sensor for sensor in robot.sensors}
            if args.sensor_type == "both":
                selected = env.get_lidar_scan(0)
                if "velocity" not in selected or "valid" in selected:
                    raise AssertionError("robot-id convenience scan did not select standard LiDAR")
                targets = [sensors["lidar2d"], sensors["fmcw_lidar2d"]]
            else:
                targets = [sensors[args.sensor_type]]

            result = {}
            for sensor in targets:
                scan = sensor.get_scan()
                ranges = scan["ranges"]
                if ranges.shape != (sensor.number,):
                    raise AssertionError("range array has an unexpected shape")
                if sensor.sensor_type == "fmcw_lidar2d":
                    if scan["valid"].shape != ranges.shape:
                        raise AssertionError("FMCW validity mask has an unexpected shape")
                    result[sensor.sensor_type] = {
                        "valid": int(scan["valid"].sum()),
                        "radial_velocity_shape": list(scan["radial_velocity"].shape),
                        "range": float(ranges[0]),
                    }
                else:
                    if scan["velocity"].shape != (2, sensor.number):
                        raise AssertionError("standard velocity array has an unexpected shape")
                    result[sensor.sensor_type] = {
                        "range": float(ranges[0]),
                        "velocity_shape": list(scan["velocity"].shape),
                    }
            print(json.dumps(result, sort_keys=True))
        finally:
            env.end()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
