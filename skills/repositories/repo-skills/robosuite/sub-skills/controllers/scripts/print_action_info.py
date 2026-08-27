#!/usr/bin/env python3
"""Print JSON action-split information for a robosuite env / robot / controller setup.

This helper intentionally avoids rendering and only creates a lightweight env
instance long enough to inspect the action layout.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np


def to_jsonable(value: Any):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print JSON action-split information for a robosuite env.")
    parser.add_argument("--environment", default="Lift", help="Environment name passed to robosuite.make().")
    parser.add_argument("--env-configuration", default=None, help="Optional env_configuration for multi-arm envs.")
    parser.add_argument("--robots", nargs="+", required=True, help="Robot names passed to robosuite.make().")
    parser.add_argument(
        "--controller",
        default=None,
        help="Composite controller preset name or custom JSON path. Omit to use the robot default.",
    )
    parser.add_argument("--base-types", nargs="+", default=None, help="Optional base override(s).")
    parser.add_argument("--gripper-types", nargs="+", default=None, help="Optional gripper override(s).")
    parser.add_argument("--control-freq", type=int, default=20, help="Control frequency used to create the env.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent level for stdout.")
    return parser.parse_args()


def build_env_kwargs(args: argparse.Namespace, controller_configs: Any) -> dict:
    env_kwargs = {
        "env_name": args.environment,
        "robots": args.robots,
        "controller_configs": controller_configs,
        "has_renderer": False,
        "has_offscreen_renderer": False,
        "ignore_done": True,
        "use_camera_obs": False,
        "reward_shaping": False,
        "control_freq": args.control_freq,
    }
    if args.env_configuration is not None:
        env_kwargs["env_configuration"] = args.env_configuration
    if args.base_types is not None:
        env_kwargs["base_types"] = args.base_types
    if args.gripper_types is not None:
        env_kwargs["gripper_types"] = args.gripper_types
    return env_kwargs


def collect_robot_info(robot) -> dict:
    controller = getattr(robot, "composite_controller", None)
    if controller is None:
        action_split_indexes = getattr(robot, "_action_split_indexes", {})
    else:
        action_split_indexes = getattr(controller, "_action_split_indexes", getattr(robot, "_action_split_indexes", {}))

    split_json = {part: [int(start), int(end)] for part, (start, end) in action_split_indexes.items()}
    action_limits_low, action_limits_high = robot.action_limits

    controller_name = None
    if controller is not None:
        controller_name = getattr(controller, "name", controller.__class__.__name__)

    info = {
        "robot": robot.name,
        "controller": controller_name,
        "action_dim": int(robot.action_dim),
        "action_limits": {
            "low": to_jsonable(action_limits_low),
            "high": to_jsonable(action_limits_high),
        },
        "action_split_indexes": split_json,
    }

    if controller is not None and hasattr(controller, "composite_controller_specific_config"):
        info["composite_controller_specific_config"] = to_jsonable(controller.composite_controller_specific_config)

    return info


def main() -> int:
    args = parse_args()

    try:
        import robosuite as suite
        from robosuite.controllers import load_composite_controller_config
    except Exception as exc:  # pragma: no cover - import failure should surface clearly at runtime
        raise SystemExit(f"Failed to import robosuite: {exc}")

    controller_configs = [load_composite_controller_config(controller=args.controller, robot=robot) for robot in args.robots]
    controller_config_payload: Any = controller_configs[0] if len(controller_configs) == 1 else controller_configs
    env = None
    try:
        env = suite.make(**build_env_kwargs(args, controller_config_payload))
        env.reset()

        payload = {
            "environment": args.environment,
            "env_configuration": args.env_configuration,
            "robots": args.robots,
            "controller_input": args.controller,
            "base_types": args.base_types,
            "gripper_types": args.gripper_types,
            "control_freq": args.control_freq,
            "robots_info": [collect_robot_info(robot) for robot in env.robots],
        }
        if len(controller_configs) == 1:
            payload["controller_config"] = to_jsonable(controller_configs[0])
        else:
            payload["controller_configs"] = to_jsonable(controller_configs)
        print(json.dumps(to_jsonable(payload), indent=args.indent))
        return 0
    finally:
        if env is not None:
            env.close()


if __name__ == "__main__":
    raise SystemExit(main())
