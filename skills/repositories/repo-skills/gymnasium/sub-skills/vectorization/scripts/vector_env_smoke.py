#!/usr/bin/env python3
"""Small Gymnasium vector environment smoke check.

This script is adapted from Gymnasium's vector training tutorial idea: keep the
batched environment mechanics, omit algorithm training, and print the contracts
a future agent should inspect when debugging vector loops.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import Any


def _make_cartpole_env():
    import gymnasium as gym

    return gym.make("CartPole-v1")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test a tiny Gymnasium CartPole vector environment."
    )
    parser.add_argument(
        "--constructor",
        choices=("make_vec", "sync-vector-env", "async-vector-env"),
        default="make_vec",
        help="How to construct the vector environment.",
    )
    parser.add_argument(
        "--mode",
        choices=("sync", "async"),
        default="sync",
        help="Vectorization mode for --constructor make_vec.",
    )
    parser.add_argument(
        "--num-envs",
        type=int,
        default=2,
        help="Number of CartPole sub-environments to create.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=4,
        help="Number of batched steps to run.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=123,
        help="Base reset/action-space seed.",
    )
    parser.add_argument(
        "--autoreset-mode",
        choices=("NextStep", "SameStep", "Disabled"),
        default="NextStep",
        help="Gymnasium AutoresetMode value used by sync/async vectorizers.",
    )
    parser.add_argument(
        "--shared-memory",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use shared memory for async construction where supported.",
    )
    return parser


def _shape_of(value: Any) -> Any:
    if hasattr(value, "shape"):
        return tuple(value.shape)
    if isinstance(value, dict):
        return {key: _shape_of(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_shape_of(item) for item in value)
    if isinstance(value, list):
        return [ _shape_of(item) for item in value ]
    return type(value).__name__


def _summarize_infos(infos: dict[str, Any]) -> str:
    if not infos:
        return "{}"

    parts = []
    for key in sorted(infos):
        value = infos[key]
        if key.startswith("_"):
            try:
                parts.append(f"{key}=mask:{value.astype(int).tolist()}")
            except AttributeError:
                parts.append(f"{key}=mask:{value}")
        else:
            parts.append(f"{key}:shape={_shape_of(value)}")
    return "{" + ", ".join(parts) + "}"


def _make_envs(args: argparse.Namespace):
    import gymnasium as gym
    from gymnasium.vector import AsyncVectorEnv, SyncVectorEnv

    autoreset_mode = gym.vector.AutoresetMode(args.autoreset_mode)

    if args.constructor == "make_vec":
        return gym.make_vec(
            "CartPole-v1",
            num_envs=args.num_envs,
            vectorization_mode=args.mode,
            vector_kwargs={"autoreset_mode": autoreset_mode},
        )

    env_fns = [_make_cartpole_env for _ in range(args.num_envs)]
    if args.constructor == "sync-vector-env":
        return SyncVectorEnv(env_fns, autoreset_mode=autoreset_mode)

    return AsyncVectorEnv(
        env_fns,
        shared_memory=args.shared_memory,
        autoreset_mode=autoreset_mode,
    )


def _run(args: argparse.Namespace) -> int:
    if args.num_envs < 1:
        raise ValueError("--num-envs must be at least 1")
    if args.steps < 1:
        raise ValueError("--steps must be at least 1")

    envs = _make_envs(args)
    try:
        envs.action_space.seed(args.seed)
        observations, infos = envs.reset(seed=args.seed)
        print(f"env_class={type(envs).__name__}")
        print(f"num_envs={envs.num_envs}")
        print(f"single_action_space={envs.single_action_space}")
        print(f"action_space={envs.action_space}")
        print(f"single_observation_space={envs.single_observation_space}")
        print(f"observation_space={envs.observation_space}")
        print(f"autoreset_mode={envs.metadata.get('autoreset_mode')}")
        print(f"reset_observation_shape={_shape_of(observations)}")
        print(f"reset_info_keys={sorted(infos)}")

        for step_index in range(args.steps):
            actions = envs.action_space.sample()
            observations, rewards, terminations, truncations, infos = envs.step(actions)
            done_mask = terminations | truncations
            print(
                "step={step} action_shape={action_shape} obs_shape={obs_shape} "
                "reward_shape={reward_shape} terminated={terminated} "
                "truncated={truncated} done={done} infos={infos}".format(
                    step=step_index + 1,
                    action_shape=_shape_of(actions),
                    obs_shape=_shape_of(observations),
                    reward_shape=_shape_of(rewards),
                    terminated=terminations.astype(int).tolist(),
                    truncated=truncations.astype(int).tolist(),
                    done=done_mask.astype(int).tolist(),
                    infos=_summarize_infos(infos),
                )
            )

            if str(envs.metadata.get("autoreset_mode")) == "AutoresetMode.DISABLED" and done_mask.any():
                observations, infos = envs.reset(options={"reset_mask": done_mask})
                print(
                    f"partial_reset mask={done_mask.astype(int).tolist()} "
                    f"obs_shape={_shape_of(observations)} info_keys={sorted(infos)}"
                )

    finally:
        envs.close()

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return _run(args)
    except ImportError as exc:
        print(
            "Gymnasium is required to run the smoke check after argument parsing: "
            f"{exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
