#!/usr/bin/env python
"""Headless camera-observation smoke test for robosuite.

This helper creates a small env with camera RGB, optional depth, and optional segmentation
observations, prints the camera-related keys, and offers MUJOCO_GL advice if offscreen
initialization fails.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Dict

import numpy as np

import robosuite as suite
from robosuite.controllers import load_composite_controller_config


def build_env(args: argparse.Namespace):

    controller_configs = load_composite_controller_config(controller=args.controller, robot=args.robot)
    env_kwargs: Dict[str, Any] = dict(
        env_name=args.environment,
        robots=args.robot,
        controller_configs=controller_configs,
        has_renderer=False,
        has_offscreen_renderer=True,
        ignore_done=True,
        use_camera_obs=True,
        use_object_obs=args.use_object_obs,
        camera_names=args.camera,
        camera_heights=args.height,
        camera_widths=args.width,
        camera_depths=args.depth,
        camera_segmentations=None if args.no_segmentation else args.segmentation_level,
        control_freq=args.control_freq,
        hard_reset=False,
        seed=args.seed,
    )
    return suite.make(**env_kwargs)


def print_gl_advice() -> None:
    backend = os.environ.get("MUJOCO_GL")
    if backend:
        print(f"MUJOCO_GL={backend}")
    else:
        print(
            "MUJOCO_GL is unset. If headless offscreen init fails, try MUJOCO_GL=egl on Linux GPUs "
            "or MUJOCO_GL=osmesa for a software fallback."
        )


def describe_obs(label: str, obs: Dict[str, np.ndarray], camera: str) -> None:
    prefix = f"{camera}_"
    image_keys = sorted(k for k in obs if k.startswith(prefix) and k.endswith("_image"))
    depth_keys = sorted(k for k in obs if k.startswith(prefix) and k.endswith("_depth"))
    seg_keys = sorted(k for k in obs if k.startswith(prefix) and "_segmentation_" in k)
    print(f"{label}: {len(obs)} total keys")
    print("  image keys:", image_keys)
    print("  depth keys:", depth_keys)
    print("  seg keys:", seg_keys)
    for key in image_keys + depth_keys + seg_keys:
        value = obs[key]
        print(f"  {key}: shape={value.shape}, dtype={value.dtype}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", default="Lift", help="robosuite env name")
    parser.add_argument("--robot", default="Panda", help="Single robot name for the env")
    parser.add_argument("--camera", default="agentview", help="Fixed camera name to inspect")
    parser.add_argument("--height", type=int, default=32, help="Camera height in pixels")
    parser.add_argument("--width", type=int, default=32, help="Camera width in pixels")
    parser.add_argument("--control-freq", type=int, default=20, help="Control frequency for the env")
    parser.add_argument("--controller", default="BASIC", help="Composite controller name")
    parser.add_argument("--depth", action=argparse.BooleanOptionalAction, default=True, help="Enable depth obs")
    parser.add_argument(
        "--segmentation-level",
        choices=["instance", "class", "element"],
        default="instance",
        help="Segmentation level to request when enabled",
    )
    parser.add_argument(
        "--no-segmentation",
        action="store_true",
        help="Disable segmentation observations entirely",
    )
    parser.add_argument(
        "--use-object-obs",
        action="store_true",
        help="Also request object-state observations",
    )
    parser.add_argument("--steps", type=int, default=1, help="Number of zero-action steps to run")
    parser.add_argument("--seed", type=int, default=None, help="Optional environment seed")
    args = parser.parse_args()

    print_gl_advice()
    try:
        env = build_env(args)
    except Exception:
        print("\nOffscreen renderer initialization failed.")
        print_gl_advice()
        raise

    try:
        obs = env.reset()
        describe_obs("reset", obs, args.camera)

        low, _ = env.action_spec
        zero_action = np.zeros_like(low)
        for step in range(args.steps):
            obs, _, _, _ = env.step(zero_action)
            describe_obs(f"step {step + 1}", obs, args.camera)
    finally:
        env.close()


if __name__ == "__main__":
    main()
