#!/usr/bin/env python3
"""Validate a tiny RLlib PPOConfig without long training by default.

This helper adapts Ray RLlib's getting-started custom corridor example into a
config-only smoke check. It imports RLlib, defines a tiny Gymnasium environment,
registers it through Tune, validates the Gymnasium tuple/space contract, and can
validate a PPOConfig. It does not build or train an Algorithm unless explicitly
requested.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import RLlib and validate a tiny PPOConfig/custom Gymnasium env."
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run import, custom env, Tune registration, and PPOConfig.validate checks.",
    )
    parser.add_argument(
        "--build-algo",
        action="store_true",
        help="Also build and immediately stop the PPO Algorithm. This starts Ray actors.",
    )
    parser.add_argument(
        "--train-one-iteration",
        action="store_true",
        help="Run one tiny training iteration after building. This may take longer.",
    )
    parser.add_argument(
        "--corridor-length",
        type=int,
        default=5,
        help="Goal position for the tiny custom corridor env.",
    )
    parser.add_argument(
        "--num-env-runners",
        type=int,
        default=0,
        help="EnvRunner actors for the PPOConfig. Use 0 for local config smoke checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary instead of human-readable lines.",
    )
    return parser


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import gymnasium as gym
        import numpy as np
        import ray
        from ray.rllib.algorithms.ppo import PPOConfig
        from ray.tune.registry import register_env
    except ModuleNotFoundError as exc:
        missing = exc.name or "required RLlib dependency"
        raise SystemExit(
            f"Missing dependency {missing!r}. Install the narrow RLlib extras first: "
            "pip install 'ray[rllib]' torch"
        ) from exc

    class TinyCorridor(gym.Env):
        metadata = {"render_modes": []}

        def __init__(self, config: dict[str, Any] | None = None):
            config = config or {}
            self.end_pos = int(config.get("corridor_length", args.corridor_length))
            if self.end_pos < 1:
                raise ValueError("corridor_length must be >= 1")
            self.cur_pos = 0
            self.action_space = gym.spaces.Discrete(2)
            self.observation_space = gym.spaces.Box(
                low=0.0,
                high=float(self.end_pos),
                shape=(1,),
                dtype=np.float32,
            )

        def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
            super().reset(seed=seed)
            self.cur_pos = 0
            return np.array([self.cur_pos], dtype=np.float32), {}

        def step(self, action: int):
            if not self.action_space.contains(action):
                raise ValueError(f"action {action!r} is outside {self.action_space}")
            if action == 1:
                self.cur_pos += 1
            elif self.cur_pos > 0:
                self.cur_pos -= 1
            terminated = self.cur_pos >= self.end_pos
            truncated = False
            reward = 1.0 if terminated else -0.1
            return (
                np.array([self.cur_pos], dtype=np.float32),
                reward,
                terminated,
                truncated,
                {},
            )

    env = TinyCorridor({"corridor_length": args.corridor_length})
    obs, info = env.reset(seed=0)
    next_obs, reward, terminated, truncated, step_info = env.step(1)
    if not env.observation_space.contains(obs):
        raise AssertionError("reset observation is outside observation_space")
    if not env.observation_space.contains(next_obs):
        raise AssertionError("step observation is outside observation_space")

    register_env("tiny_corridor_smoke", lambda env_config: TinyCorridor(env_config))

    config = (
        PPOConfig()
        .environment(
            "tiny_corridor_smoke",
            env_config={"corridor_length": args.corridor_length},
        )
        .env_runners(num_env_runners=args.num_env_runners)
        .training(
            train_batch_size_per_learner=128,
            minibatch_size=64,
            num_epochs=1,
            model={"fcnet_hiddens": [16]},
        )
    )
    config.validate()

    summary: dict[str, Any] = {
        "ray_version": ray.__version__,
        "validated": True,
        "built_algo": False,
        "trained_iterations": 0,
        "env_name": "tiny_corridor_smoke",
        "corridor_length": args.corridor_length,
        "num_env_runners": args.num_env_runners,
        "reset_info_type": type(info).__name__,
        "step_info_type": type(step_info).__name__,
        "first_reward": reward,
        "first_terminated": terminated,
        "first_truncated": truncated,
    }

    algo = None
    try:
        if args.build_algo or args.train_one_iteration:
            algo = config.build_algo()
            summary["built_algo"] = True
        if args.train_one_iteration:
            result = algo.train()
            summary["trained_iterations"] = 1
            summary["result_keys_sample"] = sorted(result.keys())[:12]
    finally:
        if algo is not None:
            algo.stop()
        if args.build_algo or args.train_one_iteration:
            ray.shutdown()

    return summary


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.train_one_iteration:
        args.build_algo = True
    if not args.validate and not args.build_algo and not args.train_one_iteration:
        parser.print_help()
        return 0

    summary = run_smoke(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("RLlib PPOConfig smoke check passed")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
