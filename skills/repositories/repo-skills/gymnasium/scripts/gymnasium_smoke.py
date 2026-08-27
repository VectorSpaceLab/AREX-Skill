#!/usr/bin/env python3
"""Small Gymnasium smoke checks for import, env loop, spaces, and vectorization."""

from __future__ import annotations

import argparse
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run small Gymnasium smoke checks without training or downloads."
    )
    parser.add_argument("--env-id", default="CartPole-v1", help="registered env ID to use")
    parser.add_argument("--seed", type=int, default=123, help="reset seed")
    parser.add_argument("--steps", type=int, default=3, help="single-env steps to run")
    parser.add_argument(
        "--vector-envs", type=int, default=2, help="number of vector envs for make_vec"
    )
    parser.add_argument(
        "--skip-vector", action="store_true", help="skip the vectorized environment smoke"
    )
    return parser.parse_args()


def run_single_env(gym: Any, env_id: str, seed: int, steps: int) -> None:
    env = gym.make(env_id)
    try:
        observation, info = env.reset(seed=seed)
        print(f"single_env_reset type={type(observation).__name__} info_keys={sorted(info.keys())}")
        for index in range(steps):
            action = env.action_space.sample()
            observation, reward, terminated, truncated, info = env.step(action)
            print(
                "single_env_step "
                f"i={index} reward={float(reward):.3f} "
                f"terminated={bool(terminated)} truncated={bool(truncated)}"
            )
            if terminated or truncated:
                observation, info = env.reset()
    finally:
        env.close()


def run_spaces(gym: Any) -> None:
    import numpy as np

    space = gym.spaces.Dict(
        {
            "position": gym.spaces.Box(-1.0, 1.0, shape=(2,), dtype=np.float32),
            "choice": gym.spaces.Discrete(3),
        }
    )
    sample = space.sample()
    flat = gym.spaces.flatten(space, sample)
    restored = gym.spaces.unflatten(space, flat)
    print(
        "spaces_smoke "
        f"contains={space.contains(sample)} flat_shape={getattr(flat, 'shape', None)} "
        f"restored={space.contains(restored)}"
    )


def run_vector(gym: Any, env_id: str, seed: int, num_envs: int) -> None:
    envs = gym.make_vec(env_id, num_envs=num_envs, vectorization_mode="sync")
    try:
        observations, infos = envs.reset(seed=seed)
        actions = envs.action_space.sample()
        observations, rewards, terminations, truncations, infos = envs.step(actions)
        print(
            "vector_smoke "
            f"obs_shape={getattr(observations, 'shape', None)} "
            f"rewards_shape={getattr(rewards, 'shape', None)} "
            f"done_count={int((terminations | truncations).sum())} "
            f"autoreset={envs.metadata.get('autoreset_mode')}"
        )
    finally:
        envs.close()


def main() -> int:
    args = parse_args()
    try:
        import gymnasium as gym
    except Exception as exc:
        print(f"failed_import: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"gymnasium_version={getattr(gym, '__version__', 'unknown')}")
    print(f"env_spec={gym.spec(args.env_id).id}")
    run_single_env(gym, args.env_id, args.seed, args.steps)
    run_spaces(gym)
    if not args.skip_vector:
        run_vector(gym, args.env_id, args.seed, args.vector_envs)
    print("gymnasium_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
