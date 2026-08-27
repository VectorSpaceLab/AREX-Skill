#!/usr/bin/env python3
"""Check a robosuite installation and run a bounded smoke test.

The helper verifies import metadata, prints registry sizes, creates a small
Lift/Panda environment, and optionally performs an offscreen camera smoke.
"""

from __future__ import annotations

import argparse
import os
import sys
from importlib.metadata import PackageNotFoundError, version

import numpy as np


def _bool(text: str) -> bool:
    value = str(text).strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean, got {text!r}")


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def import_check() -> object:
    print_header("import")
    try:
        dist_version = version("robosuite")
        print(f"distribution robosuite={dist_version}")
    except PackageNotFoundError:
        print("distribution robosuite=not-found")

    try:
        import robosuite as suite
        import mujoco
    except Exception as exc:
        raise SystemExit(f"failed to import robosuite or mujoco: {exc}") from exc

    print(f"robosuite.__version__={suite.__version__}")
    print(f"mujoco.__version__={mujoco.__version__}")
    print(f"environments={len(list(suite.ALL_ENVIRONMENTS))}")
    print(f"robots={len(list(suite.ALL_ROBOTS))}")
    return suite


def headless_smoke(suite: object, args: argparse.Namespace) -> None:
    print_header("headless env smoke")
    env = suite.make(
        args.environment,
        robots=args.robot,
        has_renderer=False,
        has_offscreen_renderer=False,
        use_camera_obs=False,
        use_object_obs=True,
        reward_shaping=True,
        horizon=args.horizon,
        seed=args.seed,
    )
    try:
        obs = env.reset()
        low, high = env.action_spec
        action = np.random.default_rng(args.seed).uniform(low, high)
        obs, reward, done, info = env.step(action)
        print(f"env={args.environment} robot={args.robot}")
        print(f"action_dim={env.action_dim}")
        print(f"action_shape={action.shape}")
        print(f"reward={reward:.6f} done={done}")
        print(f"obs_key_count={len(obs)} sample_keys={list(obs)[:8]}")
    finally:
        env.close()


def camera_smoke(suite: object, args: argparse.Namespace) -> None:
    print_header("offscreen camera smoke")
    print(f"MUJOCO_GL={os.environ.get('MUJOCO_GL', '<unset>')}")
    env = suite.make(
        args.environment,
        robots=args.robot,
        has_renderer=False,
        has_offscreen_renderer=True,
        use_camera_obs=True,
        use_object_obs=False,
        camera_names=args.camera,
        camera_heights=args.camera_size,
        camera_widths=args.camera_size,
        horizon=args.horizon,
        seed=args.seed,
    )
    try:
        obs = env.reset()
        key = f"{args.camera}_image"
        if key not in obs:
            raise SystemExit(f"expected camera key {key!r}, got keys {list(obs)}")
        print(f"{key}.shape={obs[key].shape}")
        print(f"{key}.dtype={obs[key].dtype}")
    finally:
        env.close()


def optional_imports() -> None:
    print_header("optional imports")
    for name in ["gymnasium", "h5py", "imageio", "hid", "mink", "usd"]:
        try:
            __import__(name)
        except Exception as exc:
            print(f"{name}: unavailable ({exc.__class__.__name__}: {exc})")
        else:
            print(f"{name}: available")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", default="Lift", help="Environment for smoke tests.")
    parser.add_argument("--robot", default="Panda", help="Robot for smoke tests.")
    parser.add_argument("--camera", default="agentview", help="Camera name for the offscreen smoke.")
    parser.add_argument("--camera-size", type=int, default=32, help="Square camera size for the offscreen smoke.")
    parser.add_argument("--horizon", type=int, default=5, help="Small horizon for smoke tests.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for smoke tests.")
    parser.add_argument("--camera-smoke", type=_bool, default=False, help="Run an offscreen camera smoke.")
    parser.add_argument("--skip-optional-imports", action="store_true", help="Skip optional dependency import checks.")
    args = parser.parse_args(argv)

    suite = import_check()
    if not args.skip_optional_imports:
        optional_imports()
    headless_smoke(suite, args)
    if args.camera_smoke:
        camera_smoke(suite, args)
    print("\nrobosuite installation smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
