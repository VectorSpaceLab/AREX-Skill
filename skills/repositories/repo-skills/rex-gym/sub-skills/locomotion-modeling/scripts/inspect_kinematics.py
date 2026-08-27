#!/usr/bin/env python3
"""Run a bounded, deterministic Kinematics.solve diagnostic."""

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


def vector(values, low, high, label):
    return [bounded(value, low, high, label) for value in values]


def parser():
    p = argparse.ArgumentParser(
        description="Inspect Rex-Gym inverse kinematics without starting PyBullet.")
    p.add_argument("--orientation", nargs=3, type=finite_float, metavar=("ROLL", "PITCH", "YAW"),
                   default=[0.0, 0.0, 0.0],
                   help="roll, pitch, yaw in radians (each between -3.2 and 3.2)")
    p.add_argument("--position", nargs=3, type=finite_float, metavar=("X", "Y", "Z"),
                   default=[0.0, 0.0, 0.0],
                   help="base position in metres (each between -2 and 2)")
    p.add_argument("--frames", nargs=12, type=finite_float, metavar="F",
                   help="optional 12 values for four FR/FL/RR/RL frame rows in metres")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        orientation = vector(args.orientation, -3.2, 3.2, "orientation")
        position = vector(args.position, -2.0, 2.0, "position")
        frames = None
        if args.frames is not None:
            frames = vector(args.frames, -2.0, 2.0, "frame")
            frames = [frames[i:i + 3] for i in range(0, 12, 3)]
    except argparse.ArgumentTypeError as exc:
        print("Invalid arguments: {}".format(exc), file=sys.stderr)
        return 2

    try:
        import numpy as np
        from rex_gym.model.kinematics import Kinematics
    except (ImportError, ModuleNotFoundError) as exc:
        print("Missing Rex-Gym/NumPy dependency: {}. Install the public runtime "
              "before running this diagnostic.".format(exc), file=sys.stderr)
        return 2

    try:
        solver = Kinematics()
        result = solver.solve(np.asarray(orientation), np.asarray(position),
                              None if frames is None else np.asarray(frames))
        angles = [np.asarray(item).reshape(-1).tolist() for item in result[:4]]
        transformed = np.asarray(result[4])
        payload = {
            "orientation_rad": orientation,
            "position_m": position,
            "leg_order": ["FR", "FL", "RR", "RL"],
            "angles_shape": [len(item) for item in angles],
            "angles": angles,
            "transformed_frames_shape": list(transformed.shape),
            "transformed_frames": transformed.tolist(),
            "command_order": ["FL", "FR", "RL", "RR"],
            "command_shape": [12],
        }
    except (TypeError, ValueError, ArithmeticError) as exc:
        print("Kinematics diagnostic failed: {}".format(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
