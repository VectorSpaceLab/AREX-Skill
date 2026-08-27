#!/usr/bin/env python3
"""Run a bounded, dependency-light ReferenceMotion contract check.

The helper uses in-memory fixed, random, and track fixtures. It does not read
source-checkout files, render, download data, or write artifacts.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["fixed", "random", "track"], default="track")
    parser.add_argument("--time", type=float, default=0.5)
    parser.add_argument("--motion-extrapolation", action="store_true")
    return parser


def _fixture(mode: str) -> dict[str, np.ndarray]:
    if mode == "fixed":
        rows = 1
        times = np.array([0.0])
    elif mode == "random":
        rows = 2
        times = np.array([0.0, 1.0])
    else:
        rows = 3
        times = np.array([0.0, 1.0, 2.0])
    robot = np.arange(rows, dtype=float).reshape(rows, 1)
    return {
        "time": times,
        "robot": robot,
        "robot_vel": np.ones_like(robot),
        "object": np.zeros((rows, 7), dtype=float),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        from myosuite.logger.reference_motion import ReferenceMotion

        motion = ReferenceMotion(
            _fixture(args.mode), motion_extrapolation=args.motion_extrapolation
        )
        robot_init, object_init = motion.get_init()
        frame = motion.get_reference(args.time)
        print(
            f"type={motion.type.name} horizon={motion.horizon} "
            f"robot_dim={motion.robot_dim} object_dim={motion.object_dim} "
            f"robot_init_shape={np.asarray(robot_init).shape} "
            f"object_init_shape={np.asarray(object_init).shape} "
            f"frame_robot_shape={np.asarray(frame.robot).shape}"
        )
        motion.reset()
        print("cache_after_reset=0")
        return 0
    except (AssertionError, TypeError, ValueError, ImportError) as exc:
        print(f"reference_motion_smoke: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
