#!/usr/bin/env python3
"""Run a bounded, deterministic Rex-Gym MotorModel conversion diagnostic."""

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


def parser():
    p = argparse.ArgumentParser(
        description="Inspect bounded position- or torque-mode motor conversion without PyBullet.")
    p.add_argument("--motors", type=int, choices=range(1, 19), default=3,
                   help="motor count, from 1 through 18")
    p.add_argument("--torque-control", action="store_true",
                   help="interpret command-value as PWM-like torque control")
    p.add_argument("--command-value", type=finite_float, default=0.25,
                   help="uniform target angle or PWM value in [-2, 2]")
    p.add_argument("--motor-angle", type=finite_float, default=0.0,
                   help="uniform observed motor angle in [-10, 10] radians")
    p.add_argument("--motor-velocity", type=finite_float, default=0.0,
                   help="uniform observed velocity in [-100, 100]")
    p.add_argument("--true-motor-velocity", type=finite_float, default=0.0,
                   help="uniform true velocity in [-100, 100]")
    p.add_argument("--kp", type=finite_float, default=1.2,
                   help="position proportional gain in [0, 100]")
    p.add_argument("--kd", type=finite_float, default=0.0,
                   help="position derivative gain in [0, 100]")
    p.add_argument("--strength", type=finite_float, default=1.0,
                   help="uniform actual-torque strength ratio in [0, 1]")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        command = bounded(args.command_value, -2.0, 2.0, "command-value")
        motor_angle = bounded(args.motor_angle, -10.0, 10.0, "motor-angle")
        motor_velocity = bounded(args.motor_velocity, -100.0, 100.0, "motor-velocity")
        true_velocity = bounded(args.true_motor_velocity, -100.0, 100.0,
                                "true-motor-velocity")
        kp = bounded(args.kp, 0.0, 100.0, "kp")
        kd = bounded(args.kd, 0.0, 100.0, "kd")
        strength = bounded(args.strength, 0.0, 1.0, "strength")
    except argparse.ArgumentTypeError as exc:
        print("Invalid arguments: {}".format(exc), file=sys.stderr)
        return 2

    try:
        import numpy as np
        from rex_gym.model.motor import MotorModel
    except (ImportError, ModuleNotFoundError) as exc:
        print("Missing Rex-Gym/NumPy dependency: {}. Install the public runtime "
              "before running this diagnostic.".format(exc), file=sys.stderr)
        return 2

    try:
        n = args.motors
        model = MotorModel(n, torque_control_enabled=args.torque_control,
                           kp=kp, kd=kd)
        model.set_strength_ratios(np.full(n, strength))
        command_vector = np.full(n, command)
        angle_vector = np.full(n, motor_angle)
        velocity_vector = np.full(n, motor_velocity)
        true_velocity_vector = np.full(n, true_velocity)
        actual, observed = model.convert_to_torque(
            command_vector, angle_vector, velocity_vector, true_velocity_vector)
        actual = np.asarray(actual).reshape(-1)
        observed = np.asarray(observed).reshape(-1)
        payload = {
            "motors": n,
            "control_mode": "torque" if args.torque_control else "position",
            "input_command_value": command,
            "input_shape": [n],
            "actual_torque_shape": list(actual.shape),
            "observed_torque_shape": list(observed.shape),
            "actual_torque": actual.tolist(),
            "observed_torque": observed.tolist(),
            "pwm_clip": [-1.0, 1.0],
            "strength_ratio": strength,
        }
    except (TypeError, ValueError, ArithmeticError) as exc:
        print("Motor diagnostic failed: {}".format(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
