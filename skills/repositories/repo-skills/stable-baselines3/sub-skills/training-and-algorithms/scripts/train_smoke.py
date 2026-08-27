#!/usr/bin/env python3
"""Run a tiny Stable-Baselines3 training smoke test.

The defaults avoid rendering, downloads, optional progress-bar packages, and CUDA.
"""

from __future__ import annotations

import argparse
from typing import Any

ALGORITHM_CHOICES = ("A2C", "DQN", "PPO")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny CPU Stable-Baselines3 training smoke test.")
    parser.add_argument(
        "--algorithm",
        choices=ALGORITHM_CHOICES,
        default="A2C",
        help="SB3 algorithm to smoke test. Defaults to A2C.",
    )
    parser.add_argument(
        "--env-id",
        default="CartPole-v1",
        help="Registered Gymnasium environment id. Defaults to CartPole-v1.",
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=16,
        help="Training timesteps. Defaults to 16 for a fast smoke check.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed for model and environment reset.")
    return parser


def get_model_class(algorithm: str) -> Any:
    from stable_baselines3 import A2C, DQN, PPO

    return {"A2C": A2C, "DQN": DQN, "PPO": PPO}[algorithm]


def smoke_kwargs(algorithm: str) -> dict[str, Any]:
    if algorithm == "PPO":
        return {"n_steps": 8, "batch_size": 8, "n_epochs": 1}
    if algorithm == "DQN":
        return {"learning_starts": 0, "buffer_size": 500, "train_freq": 1, "gradient_steps": 1}
    return {}


def main() -> int:
    args = build_parser().parse_args()
    if args.timesteps <= 0:
        raise SystemExit("--timesteps must be a positive integer")

    import gymnasium as gym

    env = gym.make(args.env_id)
    try:
        env.reset(seed=args.seed)
        model_class = get_model_class(args.algorithm)
        model = model_class(
            "MlpPolicy",
            env,
            seed=args.seed,
            device="cpu",
            verbose=0,
            **smoke_kwargs(args.algorithm),
        )
        model.learn(total_timesteps=args.timesteps, progress_bar=False)
        action_space = env.action_space.__class__.__name__
        observation_space = env.observation_space.__class__.__name__
        print(
            f"ok: algorithm={args.algorithm} env={args.env_id} "
            f"timesteps={args.timesteps} action_space={action_space} observation_space={observation_space}"
        )
    finally:
        env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
