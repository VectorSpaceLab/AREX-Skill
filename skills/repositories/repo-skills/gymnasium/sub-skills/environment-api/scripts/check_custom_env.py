#!/usr/bin/env python3
"""Smoke-check a tiny custom Gymnasium environment.

This script is adapted from Gymnasium's GridWorld custom-environment tutorial
into a self-contained, dependency-light checker for the environment-api skill.
"""

from __future__ import annotations

import argparse
from typing import Any

DEMO_ENV_ID = "disco-env-api/GridWorldCheck-v0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a tiny custom Gymnasium Env and run one reset/step smoke."
    )
    parser.add_argument("--size", type=int, default=5, help="Grid side length, at least 2.")
    parser.add_argument("--seed", type=int, default=123, help="Seed passed to env.reset.")
    parser.add_argument(
        "--action",
        type=int,
        default=0,
        help="One Discrete(4) action to step after reset: 0 right, 1 up, 2 left, 3 down.",
    )
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=20,
        help="TimeLimit value used when registering the demo env.",
    )
    parser.add_argument(
        "--skip-check-env",
        action="store_true",
        help="Skip gymnasium.utils.env_checker.check_env.",
    )
    parser.add_argument(
        "--check-render",
        action="store_true",
        help="Include render checks in check_env by constructing the raw env with render_mode='ansi'.",
    )
    return parser.parse_args()


def import_runtime_dependencies():
    try:
        import numpy as np
        import gymnasium as gym
        from gymnasium import spaces
        from gymnasium.utils.env_checker import check_env
    except ModuleNotFoundError as error:
        missing_name = error.name or str(error)
        raise SystemExit(
            f"Missing required package {missing_name!r}. Install base Gymnasium with NumPy "
            "or run this script in an environment where `import gymnasium` works."
        ) from error

    return np, gym, spaces, check_env


def build_grid_world_env(np, gym, spaces):
    class GridWorldCheckEnv(gym.Env):
        """A tiny GridWorld-like environment for API validation."""

        metadata = {"render_modes": ["ansi"], "render_fps": 4}

        def __init__(self, size: int = 5, render_mode: str | None = None):
            if size < 2:
                raise ValueError("size must be at least 2")
            if render_mode is not None and render_mode not in self.metadata["render_modes"]:
                raise ValueError(
                    f"Unsupported render_mode={render_mode!r}; "
                    f"expected one of {self.metadata['render_modes']} or None"
                )

            self.size = int(size)
            self.render_mode = render_mode
            self.observation_space = spaces.Dict(
                {
                    "agent": spaces.Box(0, self.size - 1, shape=(2,), dtype=np.int64),
                    "target": spaces.Box(0, self.size - 1, shape=(2,), dtype=np.int64),
                }
            )
            self.action_space = spaces.Discrete(4)
            self._action_to_direction = {
                0: np.array([0, 1], dtype=np.int64),
                1: np.array([-1, 0], dtype=np.int64),
                2: np.array([0, -1], dtype=np.int64),
                3: np.array([1, 0], dtype=np.int64),
            }
            self._agent_location = np.array([0, 0], dtype=np.int64)
            self._target_location = np.array([self.size - 1, self.size - 1], dtype=np.int64)

        def _get_obs(self) -> dict[str, Any]:
            return {
                "agent": self._agent_location.copy(),
                "target": self._target_location.copy(),
            }

        def _get_info(self) -> dict[str, int]:
            return {
                "distance": int(
                    np.abs(self._agent_location - self._target_location).sum()
                )
            }

        def reset(
            self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None,
        ) -> tuple[dict[str, Any], dict[str, int]]:
            super().reset(seed=seed)
            self._agent_location = self.np_random.integers(
                0, self.size, size=2, dtype=np.int64
            )
            self._target_location = self._agent_location.copy()
            while np.array_equal(self._target_location, self._agent_location):
                self._target_location = self.np_random.integers(
                    0, self.size, size=2, dtype=np.int64
                )
            return self._get_obs(), self._get_info()

        def step(
            self, action: int
        ) -> tuple[dict[str, Any], float, bool, bool, dict[str, int]]:
            if not self.action_space.contains(action):
                raise ValueError(f"Invalid action {action!r} for {self.action_space}")

            direction = self._action_to_direction[int(action)]
            self._agent_location = np.clip(
                self._agent_location + direction, 0, self.size - 1
            ).astype(np.int64)
            terminated = bool(np.array_equal(self._agent_location, self._target_location))
            truncated = False
            reward = 1.0 if terminated else 0.0
            return self._get_obs(), reward, terminated, truncated, self._get_info()

        def render(self) -> str | None:
            if self.render_mode != "ansi":
                return None

            rows: list[str] = []
            for row_index in range(self.size):
                cells: list[str] = []
                for col_index in range(self.size):
                    location = np.array([row_index, col_index], dtype=np.int64)
                    if np.array_equal(location, self._agent_location):
                        cells.append("A")
                    elif np.array_equal(location, self._target_location):
                        cells.append("T")
                    else:
                        cells.append(".")
                rows.append(" ".join(cells))
            return "\n".join(rows)

    return GridWorldCheckEnv


def ensure_registered(gym, env_class, max_episode_steps: int) -> None:
    if DEMO_ENV_ID not in gym.registry:
        gym.register(
            id=DEMO_ENV_ID,
            entry_point=env_class,
            max_episode_steps=max_episode_steps,
        )


def main() -> int:
    args = parse_args()
    if args.size < 2:
        raise SystemExit("--size must be at least 2")

    np, gym, spaces, check_env = import_runtime_dependencies()
    env_class = build_grid_world_env(np, gym, spaces)

    if not args.skip_check_env:
        raw_env = env_class(
            size=args.size, render_mode="ansi" if args.check_render else None
        )
        check_env(raw_env, skip_render_check=not args.check_render)
        raw_env.close()
        print("check_env=passed")

    ensure_registered(gym, env_class, max_episode_steps=args.max_episode_steps)
    env = gym.make(DEMO_ENV_ID, size=args.size)
    try:
        observation, info = env.reset(seed=args.seed)
        action = int(args.action)
        if not env.action_space.contains(action):
            raise SystemExit(f"--action {action!r} is not contained in {env.action_space}")
        next_observation, reward, terminated, truncated, next_info = env.step(action)

        assert env.observation_space.contains(observation)
        assert env.observation_space.contains(next_observation)
        assert isinstance(info, dict)
        assert isinstance(next_info, dict)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)

        print(f"registered_id={DEMO_ENV_ID}")
        print(f"reset_observation_ok={env.observation_space.contains(observation)}")
        print(f"step_observation_ok={env.observation_space.contains(next_observation)}")
        print(f"reward={reward} terminated={terminated} truncated={truncated}")
        print(f"distance_before={info['distance']} distance_after={next_info['distance']}")
        print("smoke=passed")
    finally:
        env.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
