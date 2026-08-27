#!/usr/bin/env python3
"""Run a short random-policy smoke rollout in a robosuite env.

This helper prints action-space facts and a compact observation summary.
It is intentionally bounded and non-interactive.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from typing import Iterable

import numpy as np

import robosuite as suite


DEFAULT_ENV = "Lift"
DEFAULT_ROBOTS = "Panda"
DEFAULT_CAMERA = "agentview"


def _parse_bool(text: str) -> bool:
    if isinstance(text, bool):
        return text
    value = text.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got {text!r}")


def _parse_jsonish_list(text: str):
    import json

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Expected JSON list or string, got {text!r}") from exc
    return value


def _maybe_parse_list_or_scalar(text: str):
    text = text.strip()
    if text.startswith("["):
        return _parse_jsonish_list(text)
    return text


def _summarize_obs(obs: OrderedDict, limit: int = 12) -> str:
    parts = []
    for idx, (key, value) in enumerate(obs.items()):
        if idx >= limit:
            parts.append("...")
            break
        shape = getattr(value, "shape", None)
        dtype = getattr(value, "dtype", type(value).__name__)
        parts.append(f"{key}:{shape}:{dtype}")
    return ", ".join(parts)


def _resolve_robots(text: str):
    if text.startswith("["):
        return _parse_jsonish_list(text)
    return text


def build_env(args):
    robots = _resolve_robots(args.robots)
    has_offscreen_renderer = args.has_offscreen_renderer
    camera_names = args.camera_names
    if args.use_camera_obs and not has_offscreen_renderer:
        print("note: camera observations requested; enabling offscreen renderer")
        has_offscreen_renderer = True
    if args.use_camera_obs and camera_names is None:
        print(f"note: no camera names provided; using {DEFAULT_CAMERA}")
        camera_names = DEFAULT_CAMERA

    kwargs = dict(
        env_name=args.env_name,
        robots=robots,
        env_configuration=args.env_configuration,
        gripper_types=_maybe_parse_list_or_scalar(args.gripper_types),
        use_object_obs=args.use_object_obs,
        use_camera_obs=args.use_camera_obs,
        has_renderer=args.has_renderer,
        has_offscreen_renderer=has_offscreen_renderer,
        render_camera=args.render_camera,
        reward_shaping=args.reward_shaping,
        control_freq=args.control_freq,
        horizon=args.horizon,
        ignore_done=args.ignore_done,
        seed=args.seed,
    )
    if camera_names is not None:
        kwargs["camera_names"] = _maybe_parse_list_or_scalar(camera_names)
    if args.camera_heights is not None:
        kwargs["camera_heights"] = args.camera_heights
    if args.camera_widths is not None:
        kwargs["camera_widths"] = args.camera_widths
    if args.camera_depths is not None:
        kwargs["camera_depths"] = args.camera_depths
    return suite.make(**kwargs)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-name", default=DEFAULT_ENV, help="Registered robosuite env name.")
    parser.add_argument("--robots", default=DEFAULT_ROBOTS, help="Robot string or JSON list, e.g. Panda or [\"Sawyer\", \"Panda\"]")
    parser.add_argument("--env-configuration", default="default", help="Task configuration such as default, opposed, parallel, or single-robot.")
    parser.add_argument("--gripper-types", default="default", help="Gripper string or JSON list; default broadcasts per robot.")
    parser.add_argument("--use-object-obs", type=_parse_bool, default=True, help="Enable low-dimensional object observations.")
    parser.add_argument("--use-camera-obs", type=_parse_bool, default=False, help="Enable camera observations.")
    parser.add_argument("--has-renderer", type=_parse_bool, default=False, help="Open an on-screen viewer.")
    parser.add_argument("--has-offscreen-renderer", type=_parse_bool, default=False, help="Enable offscreen rendering.")
    parser.add_argument("--render-camera", default=DEFAULT_CAMERA, help="Viewer camera name.")
    parser.add_argument("--camera-names", default=None, help="Camera name or JSON list for camera observations.")
    parser.add_argument("--camera-heights", type=int, default=84, help="Camera height.")
    parser.add_argument("--camera-widths", type=int, default=84, help="Camera width.")
    parser.add_argument("--camera-depths", type=_parse_bool, default=False, help="Request depth channels for camera obs.")
    parser.add_argument("--reward-shaping", type=_parse_bool, default=False, help="Enable dense rewards.")
    parser.add_argument("--control-freq", type=int, default=20, help="Control frequency in Hz.")
    parser.add_argument("--horizon", type=int, default=25, help="Episode horizon.")
    parser.add_argument("--ignore-done", type=_parse_bool, default=False, help="Ignore horizon termination.")
    parser.add_argument("--seed", type=int, default=0, help="Environment seed.")
    parser.add_argument("--steps", type=int, default=3, help="Number of random steps to execute.")
    parser.add_argument("--action-scale", type=float, default=0.2, help="Uniform action scale inside action bounds.")
    args = parser.parse_args(argv)

    env = build_env(args)
    try:
        obs = env.reset()
        low, high = env.action_spec
        print(f"env={args.env_name}")
        print(f"robots={[r.robot_model.__class__.__name__ for r in env.robots]}")
        print(f"action_dim={env.action_dim}")
        print(f"action_spec_shape={low.shape}")
        print(f"obs_keys={list(obs.keys())[:12]}")
        print(f"obs_summary={_summarize_obs(obs)}")

        total_reward = 0.0
        for step in range(args.steps):
            center = (low + high) / 2.0
            span = (high - low) / 2.0
            action = center + np.random.uniform(-1.0, 1.0, size=low.shape) * span * args.action_scale
            obs, reward, done, info = env.step(action)
            total_reward += reward
            print(
                f"step={step} action_shape={action.shape} reward={reward:.6f} done={done} "
                f"obs_keys={len(obs)} sample={_summarize_obs(obs, limit=6)}"
            )
            if done:
                break
        print(f"rollout_return={total_reward:.6f}")
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
