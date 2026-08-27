#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.
# This helper is a distilled, dependency-light TorchRL env smoke check.

from __future__ import annotations

import argparse
import contextlib
from typing import Sequence

import torchrl
from torchrl.envs import PendulumEnv, TransformedEnv, check_env_specs, step_mdp
from torchrl.envs.transforms import StepCounter


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a CPU-safe TorchRL PendulumEnv rollout smoke check."
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=3,
        help="Number of rollout steps to collect. Must be positive. Default: 3.",
    )
    parser.add_argument(
        "--check-specs",
        dest="check_specs",
        action="store_true",
        default=True,
        help="Run check_env_specs before the rollout. Enabled by default.",
    )
    parser.add_argument(
        "--no-check-specs",
        dest="check_specs",
        action="store_false",
        help="Skip check_env_specs and only run rollout plus step_mdp.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.steps < 1:
        raise SystemExit("--steps must be a positive integer")

    env = TransformedEnv(PendulumEnv(), StepCounter(max_steps=max(args.steps, 1)))
    try:
        if args.check_specs:
            check_env_specs(env, seed=0)

        rollout = env.rollout(max_steps=args.steps)
        if "next" not in rollout.keys():
            raise RuntimeError("rollout is missing the required 'next' transition entry")

        transition = rollout[0]
        next_root = step_mdp(
            transition,
            reward_keys=env.reward_keys,
            done_keys=env.done_keys,
            action_keys=env.action_keys,
        )
        nested_keys = set(next_root.keys(include_nested=True, leaves_only=True))
        has_observation = "observation" in nested_keys or {"th", "thdot"}.issubset(
            nested_keys
        )
        if not has_observation:
            raise RuntimeError("step_mdp output is missing next-state observation keys")
        if not any(
            key == "done" or (isinstance(key, tuple) and key[-1] == "done")
            for key in nested_keys
        ):
            raise RuntimeError("step_mdp output is missing a done key")

        print(
            "torchrl-env-smoke-ok "
            f"version={getattr(torchrl, '__version__', 'unknown')} "
            f"steps={args.steps} "
            f"rollout_batch={tuple(rollout.batch_size)} "
            f"step_mdp_keys={sorted(map(str, nested_keys))}"
        )
    finally:
        with contextlib.suppress(Exception):
            env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
