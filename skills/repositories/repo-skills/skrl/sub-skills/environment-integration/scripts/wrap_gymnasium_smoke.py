#!/usr/bin/env python3
"""Run one offline Gymnasium Pendulum reset/step through a skrl wrapper.

This is intentionally a bounded CPU smoke: it creates no external simulator,
performs no training, downloads nothing, and always closes the environment.
Use it to verify that one selected framework extra and the public ``wrap_env``
entry point can consume a current Gymnasium API environment.
"""

from __future__ import annotations

import argparse
from typing import Any

import gymnasium as gym
import numpy as np


FRAMEWORKS = ("torch", "jax", "warp")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test skrl's public wrapper with a local Gymnasium Pendulum environment."
    )
    parser.add_argument(
        "--framework",
        choices=FRAMEWORKS,
        default="torch",
        help="Framework wrapper and action type to use (default: torch).",
    )
    parser.add_argument(
        "--num-envs",
        type=int,
        default=1,
        help="Create this many synchronous Gymnasium environments (default: 1).",
    )
    return parser


def _load_wrapper(framework: str):
    """Return the selected public ``wrap_env`` and an action builder."""
    if framework == "torch":
        import torch
        from skrl.envs.wrappers.torch import wrap_env

        def make_action(shape: tuple[int, ...], device: Any) -> Any:
            return torch.zeros(shape, dtype=torch.float32, device=device)

        return wrap_env, make_action

    if framework == "jax":
        import jax.numpy as jnp
        from skrl.envs.wrappers.jax import wrap_env

        def make_action(shape: tuple[int, ...], device: Any) -> Any:
            # The wrapper performs the host conversion needed by Gymnasium and
            # places the converted response on its configured JAX device.
            del device
            return jnp.zeros(shape, dtype=jnp.float32)

        return wrap_env, make_action

    import warp as wp
    from skrl.envs.wrappers.warp import wrap_env

    def make_action(shape: tuple[int, ...], device: Any) -> Any:
        return wp.zeros(shape, dtype=wp.float32, device=device)

    return wrap_env, make_action


def run(framework: str, num_envs: int) -> int:
    if num_envs < 1:
        raise ValueError("--num-envs must be at least 1")

    wrap_env, make_action = _load_wrapper(framework)
    original_env = None
    wrapped = None
    try:
        if num_envs == 1:
            original_env = gym.make("Pendulum-v1")
        else:
            # Synchronous vectorization avoids subprocesses and is suitable for
            # a deterministic, offline smoke check.
            original_env = gym.make_vec("Pendulum-v1", num_envs=num_envs, vectorization_mode="sync")

        # Make the check CPU-only even on a host whose framework default is an
        # accelerator. The actual skrl wrapper honors a source environment's
        # public ``device`` attribute when one is supplied.
        setattr(original_env.unwrapped, "device", "cpu")
        wrapped = wrap_env(original_env, wrapper="gymnasium", verbose=False)
        observation, info = wrapped.reset()
        if not isinstance(info, dict):
            raise TypeError(f"reset info must be a dict, got {type(info).__name__}")

        action_features = int(np.prod(wrapped.action_space.shape or (1,)))
        action_shape = (wrapped.num_envs, action_features)
        action = make_action(action_shape, wrapped.device)
        observation2, reward, terminated, truncated, _ = wrapped.step(action)

        if wrapped.num_envs != num_envs:
            raise AssertionError(f"expected num_envs={num_envs}, got {wrapped.num_envs}")
        if observation is None or observation2 is None:
            raise AssertionError("wrapper returned no observation")
        if tuple(reward.shape) != (num_envs, 1):
            raise AssertionError(f"expected reward shape {(num_envs, 1)}, got {tuple(reward.shape)}")
        if tuple(terminated.shape) != (num_envs, 1) or tuple(truncated.shape) != (num_envs, 1):
            raise AssertionError("termination flags do not have the expected batch shape")

        print(
            "ok: framework={framework} wrapper={wrapper} num_envs={num_envs} "
            "observation_shape={observation_shape} reward_shape={reward_shape} device={device}".format(
                framework=framework,
                wrapper=type(wrapped).__name__,
                num_envs=wrapped.num_envs,
                observation_shape=tuple(observation.shape),
                reward_shape=tuple(reward.shape),
                device=wrapped.device,
            )
        )
        return 0
    finally:
        if wrapped is not None:
            wrapped.close()
        elif original_env is not None:
            original_env.close()


def main() -> int:
    args = _parser().parse_args()
    try:
        return run(args.framework, args.num_envs)
    except (ImportError, ModuleNotFoundError) as exc:
        print(
            f"missing optional dependency for --framework {args.framework}: {exc}",
            flush=True,
        )
        return 2
    except Exception as exc:
        print(f"smoke failed: {type(exc).__name__}: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
