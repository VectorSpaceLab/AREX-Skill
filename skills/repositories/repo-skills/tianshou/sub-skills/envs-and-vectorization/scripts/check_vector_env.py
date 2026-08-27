#!/usr/bin/env python3
"""Smoke-check Tianshou vector envs with Gymnasium CartPole.

This helper validates environment factories, reset/step return shapes, done-id
reset handling, and optional subprocess construction. It does not train a policy
and does not require optional Atari, MuJoCo, EnvPool, VizDoom, Box2D, Ray, or
PettingZoo dependencies.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import Any


def make_cartpole() -> Any:
    """Create a fresh CartPole env through a top-level factory."""
    import gymnasium as gym

    return gym.make("CartPole-v1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a bounded Tianshou vector-env smoke check on CartPole-v1.",
    )
    parser.add_argument("--num-envs", type=int, default=2, help="number of vectorized envs")
    parser.add_argument("--steps", type=int, default=5, help="maximum vector steps to run")
    parser.add_argument("--seed", type=int, default=42, help="base seed for vector envs")
    parser.add_argument(
        "--subproc",
        action="store_true",
        help="also use SubprocVectorEnv; factories must be subprocess-safe",
    )
    parser.add_argument(
        "--context",
        choices=("fork", "spawn"),
        default=None,
        help="optional multiprocessing context for --subproc",
    )
    return parser


def run_smoke(
    vector_env_cls: type,
    subproc_vector_env_cls: type,
    env_fns: list[Callable[[], Any]],
    *,
    steps: int,
    seed: int,
    context: str | None = None,
) -> dict[str, object]:
    import numpy as np

    kwargs = {"context": context} if vector_env_cls is subproc_vector_env_cls and context else {}
    envs = vector_env_cls(env_fns, **kwargs)
    try:
        envs.seed(seed)
        obs, infos = envs.reset(seed=seed)
        if len(obs) != len(env_fns):
            raise RuntimeError(f"reset returned {len(obs)} observations for {len(env_fns)} envs")
        if len(infos) != len(env_fns):
            raise RuntimeError(f"reset returned {len(infos)} info entries for {len(env_fns)} envs")

        total_resets = 0
        for _ in range(steps):
            actions = np.array([space.sample() for space in envs.action_space])
            obs, rew, terminated, truncated, step_infos = envs.step(actions)
            if not (len(obs) == len(rew) == len(terminated) == len(truncated) == len(step_infos)):
                raise RuntimeError("step outputs have inconsistent leading dimensions")
            done = np.logical_or(terminated, truncated)
            if np.any(done):
                done_ids = np.where(done)[0]
                envs.reset(done_ids)
                total_resets += int(len(done_ids))
        return {
            "backend": vector_env_cls.__name__,
            "env_num": len(envs),
            "obs_shape": tuple(np.shape(obs)),
            "steps": steps,
            "resets_after_done": total_resets,
        }
    finally:
        envs.close()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.num_envs < 1:
        raise SystemExit("--num-envs must be >= 1")
    if args.steps < 1:
        raise SystemExit("--steps must be >= 1")

    try:
        from tianshou.env import DummyVectorEnv, SubprocVectorEnv
    except ImportError as exception:
        raise SystemExit(
            "Missing Tianshou runtime dependency. Install tianshou with Gymnasium support "
            "before running the smoke check."
        ) from exception

    env_fns = [make_cartpole for _ in range(args.num_envs)]
    results = [
        run_smoke(
            DummyVectorEnv,
            SubprocVectorEnv,
            env_fns,
            steps=args.steps,
            seed=args.seed,
        ),
    ]
    if args.subproc:
        results.append(
            run_smoke(
                SubprocVectorEnv,
                SubprocVectorEnv,
                env_fns,
                steps=args.steps,
                seed=args.seed,
                context=args.context,
            ),
        )

    for result in results:
        print(
            "{backend}: env_num={env_num} obs_shape={obs_shape} "
            "steps={steps} resets_after_done={resets_after_done}".format(**result),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
