#!/usr/bin/env python3
"""Evaluate bounded, fixed-phase Rex-Gym gait trajectories."""

import argparse
import json
import math
import sys


def finite_float(text):
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a number")
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be finite")
    return value


def bounded(value, low, high, label):
    if value < low or value > high:
        raise argparse.ArgumentTypeError("{} must be in [{}, {}]".format(label, low, high))
    return value


def phase_value(text):
    return bounded(finite_float(text), 0.0, 1.0, "phase")


def parser():
    p = argparse.ArgumentParser(
        description="Inspect fixed-phase Bezier gait samples without wall-clock timing or PyBullet.")
    p.add_argument("--mode", choices=("walk", "gallop"), default="walk",
                   help="gait phase offset pattern")
    p.add_argument("--phase", nargs="+", type=phase_value,
                   default=[0.0, 0.25, 0.5, 0.75, 1.0],
                   help="one or more normalized phases in [0, 1]")
    p.add_argument("--v", type=finite_float, default=0.6,
                   help="bounded trajectory scale in [-2, 2]")
    p.add_argument("--angle", type=finite_float, default=0.0,
                   help="step angle in degrees, bounded to [-180, 180]")
    p.add_argument("--w-rot", type=finite_float, default=0.0,
                   help="bounded rotational trajectory scale in [-2, 2]")
    p.add_argument("--direction", type=int, choices=(-1, 1), default=1,
                   help="swing direction")
    p.add_argument("--center", nargs=3, type=finite_float,
                   metavar=("X", "Y", "Z"), default=[0.115, -0.0925, -0.2],
                   help="FR center-to-foot frame in metres")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        v = bounded(args.v, -2.0, 2.0, "v")
        angle = bounded(args.angle, -180.0, 180.0, "angle")
        w_rot = bounded(args.w_rot, -2.0, 2.0, "w-rot")
        center = [bounded(value, -2.0, 2.0, "center") for value in args.center]
    except argparse.ArgumentTypeError as exc:
        print("Invalid arguments: {}".format(exc), file=sys.stderr)
        return 2

    try:
        import numpy as np
        from rex_gym.model.gait_planner import GaitPlanner
    except (ImportError, ModuleNotFoundError) as exc:
        print("Missing Rex-Gym/NumPy dependency: {}. Install the public runtime "
              "before running this diagnostic.".format(exc), file=sys.stderr)
        return 2

    try:
        planner = GaitPlanner(args.mode)
        samples = []
        for phase in args.phase:
            point = planner.step_trajectory(
                phase, v, angle, w_rot, np.asarray(center), args.direction)
            point = np.asarray(point).reshape(-1)
            samples.append({"phase": phase, "offset_m": point.tolist()})
        payload = {
            "mode": args.mode,
            "phase_offsets": np.asarray(getattr(planner, "_offset")).tolist(),
            "stance_swing_split": 0.5,
            "angle_unit": "degrees",
            "center_m": center,
            "samples": samples,
            "sample_shape": [3],
            "loop_output_shape": [4, 3],
            "note": "step_trajectory is used so samples are deterministic; loop is clock-driven.",
        }
    except (TypeError, ValueError, ArithmeticError) as exc:
        print("Gait diagnostic failed: {}".format(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
