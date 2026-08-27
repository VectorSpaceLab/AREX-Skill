#!/usr/bin/env python3
"""Tiny self-contained smoke checks for Tianshou Batch, ReplayBuffer, and Collector."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any


@dataclass
class SmokeResult:
    name: str
    detail: str


def check_batch() -> SmokeResult:
    import numpy as np

    from tianshou.data import Batch

    batch = Batch(
        obs={
            "state": np.arange(6, dtype=np.float32).reshape(3, 2),
            "label": np.array(["a", "b", "c"], dtype=object),
        },
        act=np.array([0, 1, 1], dtype=np.int64),
        rew=np.array([0.0, 1.0, 2.0], dtype=np.float32),
    )
    assert len(batch) == 3
    assert batch[1].obs.state.shape == (2,)
    stacked = Batch.stack([batch[0], batch[1]])
    assert len(stacked) == 2
    merged = Batch.cat([batch[:1], batch[1:]])
    assert np.array_equal(merged.act, batch.act)
    numeric_batch = Batch(obs={"state": batch.obs.state}, act=batch.act, rew=batch.rew)
    torch_batch = numeric_batch.to_torch(device="cpu")
    assert tuple(torch_batch.obs.state.shape) == (3, 2)
    assert batch.obs.label.dtype == object
    assert not batch.hasnull()
    return SmokeResult("batch", f"keys={list(batch.get_keys())}, len={len(batch)}")


def make_transition(index: int, done: bool = False):
    import numpy as np

    from tianshou.data import Batch

    return Batch(
        obs=np.array([float(index)], dtype=np.float32),
        act=np.array(index % 2, dtype=np.int64),
        rew=np.array(float(index), dtype=np.float32),
        terminated=np.array(done, dtype=bool),
        truncated=np.array(False, dtype=bool),
        obs_next=np.array([float(index + 1)], dtype=np.float32),
        info={"index": index},
    )


def check_replay_buffer() -> SmokeResult:
    import numpy as np

    from tianshou.data import ReplayBuffer

    buffer = ReplayBuffer(size=8, random_seed=0)
    for index in range(5):
        insertion_index, episode_return, episode_length, _ = buffer.add(
            make_transition(index, done=index == 2),
        )
        assert insertion_index.shape == (1,)
        if index == 2:
            assert episode_length[0] == 3
            assert float(episode_return[0]) == 3.0
    assert len(buffer) == 5
    all_batch, all_indices = buffer.sample(0)
    assert len(all_batch) == 5
    assert np.array_equal(all_indices, np.arange(5))
    sample_batch, sample_indices = buffer.sample(3)
    assert len(sample_batch) == 3
    assert sample_indices.shape == (3,)
    assert not buffer.hasnull()
    return SmokeResult("replay-buffer", f"len={len(buffer)}, all_indices={all_indices.tolist()}")


def check_collector(collector_steps: int, episodes: int, horizon: int) -> SmokeResult:
    import gymnasium as gym
    import numpy as np

    from tianshou.algorithm.algorithm_base import Policy
    from tianshou.data import Batch, CollectStats, Collector, VectorReplayBuffer
    from tianshou.env import DummyVectorEnv

    class CountingEnv(gym.Env):
        metadata = {"render_modes": []}

        def __init__(self, horizon: int = 3) -> None:
            super().__init__()
            self.horizon = horizon
            self.observation_space = gym.spaces.Box(
                low=0.0,
                high=100.0,
                shape=(1,),
                dtype=np.float32,
            )
            self.action_space = gym.spaces.Discrete(2)
            self.step_count = 0

        def reset(
            self,
            *,
            seed: int | None = None,
            options: dict[str, Any] | None = None,
        ):
            super().reset(seed=seed)
            self.step_count = 0
            return np.array([0.0], dtype=np.float32), {"reset": True}

        def step(self, action: int):
            self.step_count += 1
            obs = np.array([float(self.step_count)], dtype=np.float32)
            reward = float(action == 1)
            terminated = self.step_count >= self.horizon
            truncated = False
            info = {"step_count": self.step_count}
            return obs, reward, terminated, truncated, info

    class ConstantPolicy(Policy):
        def __init__(self, action_space: gym.spaces.Space) -> None:
            super().__init__(action_space=action_space)

        def forward(
            self,
            batch,
            state: dict | Batch | np.ndarray | None = None,
            **kwargs: Any,
        ) -> Batch:
            return Batch(act=np.ones(len(batch.obs), dtype=np.int64), state=state)

    env_num = 2
    envs = DummyVectorEnv([lambda: CountingEnv(horizon=horizon) for _ in range(env_num)])
    policy = ConstantPolicy(envs.action_space[0])
    buffer = VectorReplayBuffer(total_size=64, buffer_num=env_num)
    collector = Collector[CollectStats](
        policy,
        envs,
        buffer,
        raise_on_nan_in_buffer=True,
    )
    step_target = max(env_num, collector_steps)
    if step_target % env_num:
        step_target += env_num - (step_target % env_num)
    step_stats = collector.collect(n_step=step_target, reset_before_collect=True)
    assert step_stats.n_collected_steps >= step_target
    assert len(buffer) >= step_target
    episode_stats = collector.collect(n_episode=episodes, reset_before_collect=True)
    assert episode_stats.n_collected_episodes >= episodes
    assert episode_stats.returns.size >= episodes
    assert not buffer.hasnull()
    collector.close()
    return SmokeResult(
        "collector",
        (
            f"step_stats={step_stats.n_collected_steps} steps, "
            f"episode_returns={episode_stats.returns.tolist()}"
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny Tianshou data-layer smoke checks for Batch, ReplayBuffer, and Collector.",
    )
    parser.add_argument(
        "--skip-collector",
        action="store_true",
        help="Only check Batch and ReplayBuffer; skip Gymnasium collector interaction.",
    )
    parser.add_argument(
        "--collector-steps",
        type=int,
        default=4,
        help="Minimum number of transitions to collect in the collector smoke.",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=2,
        help="Number of complete episodes to collect in the collector smoke.",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=3,
        help="Episode length for the tiny counting environment.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.collector_steps <= 0:
        raise SystemExit("--collector-steps must be positive")
    if args.episodes <= 0:
        raise SystemExit("--episodes must be positive")
    if args.horizon <= 0:
        raise SystemExit("--horizon must be positive")

    results = [check_batch(), check_replay_buffer()]
    if not args.skip_collector:
        results.append(check_collector(args.collector_steps, args.episodes, args.horizon))

    for result in results:
        print(f"ok: {result.name}: {result.detail}")


if __name__ == "__main__":
    main()
