#!/usr/bin/env python3
"""Smoke-test Gymnasium wrapper patterns without optional extras.

This script adapts the custom-wrapper tutorial into a tiny self-contained check.
It supports subclass-based wrappers and built-in transform wrappers on safe local
examples, then runs one reset/step and prints success signals.
"""

from __future__ import annotations

import argparse
from typing import SupportsFloat


def run_smoke(mode: str, seed: int) -> int:
    import numpy as np

    import gymnasium as gym
    from gymnasium import ActionWrapper, ObservationWrapper, RewardWrapper, spaces
    from gymnasium.wrappers import (
        ClipReward,
        FlattenObservation,
        RecordEpisodeStatistics,
        TimeLimit,
        TransformAction,
        TransformObservation,
        TransformReward,
    )

    class DictSignalEnv(gym.Env):
        """Tiny deterministic env with Dict observations and Discrete actions."""

        metadata = {"render_modes": []}

        def __init__(self, max_steps: int = 4):
            self.observation_space = spaces.Dict(
                {
                    "agent": spaces.Box(
                        low=-10.0, high=10.0, shape=(2,), dtype=np.float32
                    ),
                    "target": spaces.Box(
                        low=-10.0, high=10.0, shape=(2,), dtype=np.float32
                    ),
                }
            )
            self.action_space = spaces.Discrete(3)
            self.max_steps = max_steps
            self.steps = 0
            self.agent = np.zeros(2, dtype=np.float32)
            self.target = np.array([1.0, -1.0], dtype=np.float32)

        def _obs(self):
            return {"agent": self.agent.copy(), "target": self.target.copy()}

        def reset(self, *, seed: int | None = None, options: dict | None = None):
            super().reset(seed=seed)
            self.steps = 0
            self.agent = np.zeros(2, dtype=np.float32)
            self.target = np.array([1.0, -1.0], dtype=np.float32)
            return self._obs(), {"reset_seed": seed}

        def step(self, action):
            self.steps += 1
            move = np.array(
                [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]], dtype=np.float32
            )[int(action)]
            self.agent = np.clip(self.agent + move, -10.0, 10.0).astype(np.float32)
            distance = float(np.linalg.norm(self.target - self.agent))
            reward = -distance
            terminated = distance < 0.25
            truncated = self.steps >= self.max_steps
            return self._obs(), reward, terminated, truncated, {"distance": distance}

    class RelativePosition(ObservationWrapper):
        """Return target position relative to agent position."""

        def __init__(self, env):
            super().__init__(env)
            self.observation_space = spaces.Box(
                low=-20.0, high=20.0, shape=(2,), dtype=np.float32
            )

        def observation(self, observation):
            return (observation["target"] - observation["agent"]).astype(np.float32)

    class DiscreteToMove(ActionWrapper):
        """Map a small Discrete action space into the inner Discrete action ids."""

        def __init__(self, env):
            super().__init__(env)
            self.moves = [0, 1, 2]
            self.action_space = spaces.Discrete(len(self.moves))

        def action(self, action):
            return self.moves[int(action)]

    class ClippedNegativeReward(RewardWrapper):
        """Clip negative distance rewards for a stable public reward range."""

        def __init__(self, env, min_reward: float = -2.0, max_reward: float = 0.0):
            super().__init__(env)
            self.min_reward = min_reward
            self.max_reward = max_reward

        def reward(self, reward: SupportsFloat) -> float:
            return float(np.clip(float(reward), self.min_reward, self.max_reward))

    def build_custom_chain():
        env = DictSignalEnv(max_steps=3)
        env = TimeLimit(env, max_episode_steps=3)
        env = RelativePosition(env)
        env = DiscreteToMove(env)
        env = ClippedNegativeReward(env)
        env = FlattenObservation(env)
        env = RecordEpisodeStatistics(env, buffer_length=3)
        return env

    def build_transform_chain():
        env = gym.make("CartPole-v1")
        env = TransformObservation(
            env,
            lambda obs: obs.astype(np.float32),
            spaces.Box(
                low=env.observation_space.low.astype(np.float32),
                high=env.observation_space.high.astype(np.float32),
                shape=env.observation_space.shape,
                dtype=np.float32,
            ),
        )
        env = TransformAction(env, lambda action: int(action), env.action_space)
        env = TransformReward(env, lambda reward: float(reward))
        env = ClipReward(env, min_reward=0.0, max_reward=1.0)
        env = RecordEpisodeStatistics(env, buffer_length=3)
        return env

    def run_one_step(env):
        observation, info = env.reset(seed=seed)
        action = env.action_space.sample()
        next_observation, reward, terminated, truncated, step_info = env.step(action)
        obs_ok = env.observation_space.contains(observation)
        next_obs_ok = env.observation_space.contains(next_observation)
        return {
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "reset_info_keys": sorted(info.keys()),
            "step_info_keys": sorted(step_info.keys()),
            "obs_ok": obs_ok,
            "next_obs_ok": next_obs_ok,
        }

    env = build_custom_chain() if mode == "custom" else build_transform_chain()
    try:
        result = run_one_step(env)
        if not result["obs_ok"] or not result["next_obs_ok"]:
            raise AssertionError(f"Observation did not match wrapped space: {result}")
        print(f"WRAPPER_SMOKE_OK mode={mode}")
        print(f"chain={env}")
        print(f"observation_space={env.observation_space}")
        print(f"action_space={env.action_space}")
        print(
            "step="
            f"reward={result['reward']} "
            f"terminated={result['terminated']} "
            f"truncated={result['truncated']} "
            f"info_keys={result['step_info_keys']}"
        )
    finally:
        env.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a one-step Gymnasium wrapper smoke test."
    )
    parser.add_argument(
        "--mode",
        choices=("custom", "transform"),
        default="custom",
        help="Wrapper chain to run: custom subclasses or built-in transform wrappers.",
    )
    parser.add_argument("--seed", type=int, default=123, help="Reset seed.")
    args = parser.parse_args()
    return run_smoke(args.mode, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
