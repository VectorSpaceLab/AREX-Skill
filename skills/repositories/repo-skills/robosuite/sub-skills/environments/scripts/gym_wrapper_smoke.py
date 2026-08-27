#!/usr/bin/env python3
"""Smoke-test robosuite's GymWrapper with a Lift/Panda env.

This helper creates a standard Lift env, wraps it with GymWrapper,
resets once, samples one action, and prints basic wrapper facts.
"""

from __future__ import annotations

import argparse


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0, help="Environment seed.")
    parser.add_argument("--flatten-obs", type=lambda x: str(x).lower() in {"1", "true", "yes", "y", "on"}, default=True, help="Return a flat observation vector.")
    args = parser.parse_args(argv)

    try:
        import gymnasium as gym  # noqa: F401
    except Exception as exc:  # pragma: no cover - explicit runtime guard
        raise SystemExit(
            "gymnasium is required for this smoke test. Install gymnasium, then rerun this helper."
        ) from exc

    import robosuite as suite
    from robosuite.wrappers import GymWrapper

    env = GymWrapper(
        suite.make(
            "Lift",
            robots="Panda",
            use_camera_obs=False,
            use_object_obs=True,
            has_renderer=False,
            has_offscreen_renderer=False,
            reward_shaping=True,
            control_freq=20,
            horizon=5,
            seed=args.seed,
        ),
        flatten_obs=args.flatten_obs,
    )

    try:
        obs, info = env.reset(seed=args.seed)
        action = env.action_space.sample()
        obs2, reward, terminated, truncated, info = env.step(action)

        print(f"wrapper={env.name}")
        print(f"action_space_shape={getattr(env.action_space, 'shape', None)}")
        print(f"obs_space_type={type(env.observation_space).__name__}")
        print(f"obs_space_shape={getattr(env.observation_space, 'shape', None)}")
        print(f"reset_obs_shape={getattr(obs, 'shape', None)}")
        print(f"step_obs_shape={getattr(obs2, 'shape', None)}")
        print(f"action_shape={getattr(action, 'shape', None)}")
        print(f"reward={reward:.6f} terminated={terminated} truncated={truncated}")
        print(f"reset_info_keys={list(info.keys())}")
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
