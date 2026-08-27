#!/usr/bin/env python3
"""Bounded, headless MyoSuite environment smoke check.

This adapts the repository's environment inspection idea without opening a
viewer, loading policies, fetching assets, or writing rollout files.

Examples:
  python environment_smoke.py --list
  python environment_smoke.py --env-id myoElbowPose1D6MRandom-v0 --steps 3
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import numpy as np


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-id", default="myoElbowPose1D6MRandom-v0")
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--render", choices=["none"], default="none")
    parser.add_argument("--list", action="store_true", help="list registered MyoSuite IDs and exit")
    parser.add_argument(
        "--check-determinism",
        action="store_true",
        help="repeat a bounded rollout with identical seeds and compare results",
    )
    return parser


def _import_gym():
    try:
        from myosuite.utils import gym
    except Exception as exc:  # pragma: no cover - diagnostic branch
        raise RuntimeError(
            "MyoSuite could not import its Gym compatibility layer. Install the "
            "base package with Gymnasium (<1.3) and MuJoCo, then retry."
        ) from exc
    return gym


def _summary(value: Any) -> str:
    array = np.asarray(value)
    return f"shape={array.shape} dtype={array.dtype}"


def _rollout(gym, env_id: str, steps: int, seed: int) -> list[tuple[np.ndarray, float, bool, bool]]:
    if steps < 0:
        raise ValueError("--steps must be non-negative")
    try:
        env = gym.make(env_id)
    except Exception as exc:
        raise RuntimeError(
            f"Could not create {env_id!r}. Check the exact registered ID and ensure "
            "the MyoSuite model asset submodules/package data are available."
        ) from exc

    records: list[tuple[np.ndarray, float, bool, bool]] = []
    try:
        # MyoSuite's task reset implementations own target/reset randomization;
        # seed the unwrapped task as well as the Gymnasium-facing reset call.
        # This preserves deterministic random-task checks across fresh instances.
        env.action_space.seed(seed)
        if hasattr(env, "unwrapped") and hasattr(env.unwrapped, "seed"):
            env.unwrapped.seed(seed)
        reset_result = env.reset(seed=seed)
        observation = reset_result[0] if isinstance(reset_result, tuple) else reset_result
        print(f"env_id={env_id} observation={_summary(observation)} action={env.action_space}")
        for index in range(steps):
            action = env.action_space.sample()
            result = env.step(action)
            if len(result) != 5:
                raise RuntimeError(
                    "This smoke helper expects a Gymnasium 5-value step result; "
                    "inspect the installed legacy Gym compatibility before adapting it."
                )
            observation, reward, terminated, truncated, _info = result
            records.append((np.array(observation, copy=True), float(reward), bool(terminated), bool(truncated)))
            print(
                f"step={index + 1} observation={_summary(observation)} "
                f"reward={float(reward):.6g} terminated={bool(terminated)} truncated={bool(truncated)}"
            )
            if terminated or truncated:
                break
    finally:
        env.close()
    return records


def _assert_same(left, right) -> None:
    if len(left) != len(right):
        raise AssertionError(f"rollout lengths differ: {len(left)} != {len(right)}")
    for index, (a, b) in enumerate(zip(left, right)):
        np.testing.assert_allclose(a[0], b[0], err_msg=f"observation differs at step {index}")
        np.testing.assert_equal(a[1:], b[1:])


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    gym = _import_gym()
    if args.list:
        ids = sorted(str(env_id) for env_id in gym.envs.registry.keys() if str(env_id).startswith("myo"))
        print(f"registered_myo_envs={len(ids)}")
        print("\n".join(ids))
        return 0

    first = _rollout(gym, args.env_id, args.steps, args.seed)
    if args.check_determinism:
        second = _rollout(gym, args.env_id, args.steps, args.seed)
        _assert_same(first, second)
        print("determinism=pass")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, ValueError) as exc:
        print(f"environment_smoke: error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
