#!/usr/bin/env python3
"""Offline checks for the DRL navigation environment contract.

This module intentionally uses only the Python standard library.  It does not
import ROS/Gazebo packages, read the source checkout, or start a process.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Iterable, List, Optional, Sequence, Tuple

GOAL_REACHED_DIST = 0.3
COLLISION_DIST = 0.35
TIME_DELTA = 0.1
DEFAULT_ENVIRONMENT_DIM = 20


class ContractError(ValueError):
    """Raised when a supplied value violates the offline contract."""


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must contain only numbers")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} contains a non-finite number")
    return result


def parse_array(raw: str, label: str) -> List[float]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractError(f"{label} must be a JSON array: {exc.msg}") from exc
    if not isinstance(value, list):
        raise ContractError(f"{label} must be a JSON array")
    return [_number(item, label) for item in value]


def validate_state(state: Sequence[float], environment_dim: int = DEFAULT_ENVIRONMENT_DIM) -> List[float]:
    if environment_dim <= 0:
        raise ContractError("environment_dim must be positive")
    expected = environment_dim + 4
    if len(state) != expected:
        raise ContractError(
            f"state length must be {expected} ({environment_dim} sensor bins + 4 robot values), "
            f"got {len(state)}"
        )
    values = [_number(item, "state") for item in state]
    sensors = values[:environment_dim]
    distance, theta, linear, angular = values[environment_dim:]
    if any(item < 0 for item in sensors):
        raise ContractError("sensor bins must be non-negative distances")
    if distance < 0:
        raise ContractError("goal distance must be non-negative")
    if not -math.pi - 1e-12 <= theta <= math.pi + 1e-12:
        raise ContractError("relative heading must be within [-pi, pi]")
    validate_action((linear, angular))
    return values


def validate_action(action: Sequence[float]) -> List[float]:
    if len(action) != 2:
        raise ContractError(f"action must contain exactly 2 values, got {len(action)}")
    values = [_number(item, "action") for item in action]
    linear, angular = values
    if not 0.0 <= linear <= 1.0:
        raise ContractError("linear action must be in [0, 1]")
    if not -1.0 <= angular <= 1.0:
        raise ContractError("angular action must be in [-1, 1]")
    return values


def make_gaps(environment_dim: int) -> List[Tuple[float, float]]:
    if environment_dim <= 0:
        raise ContractError("environment_dim must be positive")
    width = math.pi / environment_dim
    gaps: List[Tuple[float, float]] = [(-math.pi / 2 - 0.03, -math.pi / 2 + width)]
    for _ in range(environment_dim - 1):
        gaps.append((gaps[-1][1], gaps[-1][1] + width))
    lower, upper = gaps[-1]
    gaps[-1] = (lower, upper + 0.03)
    return gaps


def _point(point: Sequence[Any], index: int) -> Tuple[float, float, float]:
    if not isinstance(point, (list, tuple)) or len(point) < 3:
        raise ContractError(f"point {index} must have at least [x, y, z]")
    return (
        _number(point[0], f"point {index}"),
        _number(point[1], f"point {index}"),
        _number(point[2], f"point {index}"),
    )


def reduce_points(points: Iterable[Sequence[Any]], environment_dim: int = DEFAULT_ENVIRONMENT_DIM) -> List[float]:
    """Reproduce the callback's angular minimum reduction for safe finite data."""
    bins = [10.0] * environment_dim
    gaps = make_gaps(environment_dim)
    for index, raw_point in enumerate(points):
        x, y, z = _point(raw_point, index)
        if z <= -0.2:
            continue
        horizontal = math.hypot(x, y)
        if horizontal == 0.0:
            raise ContractError(f"point {index} has zero horizontal magnitude")
        # The source uses acos(x / horizontal) * sign(y), with sign(0)=0.
        cosine = max(-1.0, min(1.0, x / horizontal))
        beta = math.acos(cosine)
        if y > 0:
            beta *= 1.0
        elif y < 0:
            beta *= -1.0
        else:
            beta = 0.0
        distance = math.sqrt(x * x + y * y + z * z)
        for bin_index, (lower, upper) in enumerate(gaps):
            if lower <= beta < upper:
                bins[bin_index] = min(bins[bin_index], distance)
                break
    return bins


def collision_from_laser(laser: Sequence[float]) -> Tuple[bool, float]:
    if not laser:
        raise ContractError("laser array must not be empty")
    values = [_number(item, "laser") for item in laser]
    if any(item < 0 for item in values):
        raise ContractError("laser distances must be non-negative")
    minimum = min(values)
    return minimum < COLLISION_DIST, minimum


def reward(target: bool, collision: bool, action: Sequence[float], min_laser: float) -> float:
    values = validate_action(action)
    minimum = _number(min_laser, "min_laser")
    if minimum < 0:
        raise ContractError("min_laser must be non-negative")
    if target:
        return 100.0
    if collision:
        return -100.0
    proximity_penalty = 1.0 - minimum if minimum < 1.0 else 0.0
    return values[0] / 2.0 - abs(values[1]) / 2.0 - proximity_penalty / 2.0


def evaluate(distance: float, laser: Sequence[float], action: Sequence[float]) -> dict:
    distance_value = _number(distance, "distance")
    if distance_value < 0:
        raise ContractError("distance must be non-negative")
    validate_action(action)
    collision, minimum = collision_from_laser(laser)
    target = distance_value < GOAL_REACHED_DIST
    return {
        "distance": distance_value,
        "min_laser": minimum,
        "target": target,
        "collision": collision,
        "done": target or collision,
        "reward": reward(target, collision, action, minimum),
        "time_delta": TIME_DELTA,
    }


def _assert_raises(function, message: str) -> None:
    try:
        function()
    except ContractError:
        return
    raise AssertionError(message)


def self_test() -> None:
    state = [1.0] * 20 + [2.0, 0.0, 0.0, 0.0]
    validate_state(state)
    _assert_raises(lambda: validate_state([1.0] * 23), "23-value state was accepted")
    _assert_raises(lambda: validate_state([1.0] * 25), "25-value state was accepted")
    validate_action([0.0, -1.0])
    validate_action([1.0, 1.0])
    _assert_raises(lambda: validate_action([-1.0, 0.0]), "negative linear action was accepted")
    _assert_raises(lambda: validate_action([0.5, 1.1]), "out-of-range angular action was accepted")

    fixture = [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, -1.0, 0.0], [1.0, 0.0, -0.2]]
    bins = reduce_points(fixture)
    if bins[10] != 1.0 or bins[0] != 1.0 or sum(value != 10.0 for value in bins) != 2:
        raise AssertionError(f"unexpected synthetic bins: {bins}")

    if not collision_from_laser([0.349])[0]:
        raise AssertionError("0.349 did not collide")
    if collision_from_laser([0.35])[0]:
        raise AssertionError("0.35 incorrectly collided")
    if not evaluate(0.299, [10.0] * 20, [0.5, 0.0])["target"]:
        raise AssertionError("0.299 did not reach target")
    if evaluate(0.30, [10.0] * 20, [0.5, 0.0])["target"]:
        raise AssertionError("0.30 incorrectly reached target")
    if evaluate(0.1, [0.1] * 20, [0.5, 0.0])["reward"] != 100.0:
        raise AssertionError("target did not take reward priority")
    if evaluate(1.0, [0.1] * 20, [0.5, 0.0])["reward"] != -100.0:
        raise AssertionError("collision reward mismatch")


def _json_result(value: Any) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the ROS-free navigation state, action, sensor, and reward contract."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    state_parser = subparsers.add_parser("validate-state", help="validate a JSON state array")
    state_parser.add_argument("--state", required=True, help="JSON array")
    state_parser.add_argument("--environment-dim", type=int, default=DEFAULT_ENVIRONMENT_DIM)

    action_parser = subparsers.add_parser("validate-action", help="validate a JSON environment action")
    action_parser.add_argument("--action", required=True, help="JSON array [linear, angular]")

    points_parser = subparsers.add_parser("reduce-points", help="reduce JSON [x,y,z] points to distance bins")
    points_parser.add_argument("--points", required=True, help="JSON array of point arrays")
    points_parser.add_argument("--environment-dim", type=int, default=DEFAULT_ENVIRONMENT_DIM)

    eval_parser = subparsers.add_parser("evaluate", help="evaluate synthetic threshold and reward behavior")
    eval_parser.add_argument("--distance", required=True, type=float)
    eval_parser.add_argument("--laser", required=True, help="JSON array of laser distances")
    eval_parser.add_argument("--action", required=True, help="JSON array [linear, angular]")

    subparsers.add_parser("self-test", help="run deterministic tiny-fixture checks")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-state":
            _json_result({"ok": True, "length": len(validate_state(parse_array(args.state, "state"), args.environment_dim))})
        elif args.command == "validate-action":
            _json_result({"ok": True, "action": validate_action(parse_array(args.action, "action"))})
        elif args.command == "reduce-points":
            try:
                points = json.loads(args.points)
            except json.JSONDecodeError as exc:
                raise ContractError(f"points must be a JSON array: {exc.msg}") from exc
            if not isinstance(points, list):
                raise ContractError("points must be a JSON array")
            _json_result({"ok": True, "bins": reduce_points(points, args.environment_dim)})
        elif args.command == "evaluate":
            _json_result({"ok": True, **evaluate(args.distance, parse_array(args.laser, "laser"), parse_array(args.action, "action"))})
        else:
            self_test()
            _json_result({"ok": True, "self_test": "passed"})
        return 0
    except (ContractError, AssertionError) as exc:
        print(f"contract error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
