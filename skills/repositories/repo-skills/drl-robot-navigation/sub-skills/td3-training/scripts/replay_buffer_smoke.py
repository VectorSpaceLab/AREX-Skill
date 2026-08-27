#!/usr/bin/env python3
"""Deterministic, dependency-light smoke for the source ReplayBuffer contract."""

from __future__ import annotations

import argparse
import random
import sys
from collections import deque
from typing import Any, Tuple

import numpy as np


class ReplayBuffer:
    """Self-contained distillation of TD3/replay_buffer.py."""

    def __init__(self, buffer_size: int, random_seed: int = 123) -> None:
        self.buffer_size = buffer_size
        self.count = 0
        self.buffer = deque()
        random.seed(random_seed)

    def add(self, state: Any, action: Any, reward: float, done: int, next_state: Any) -> None:
        experience = (state, action, reward, done, next_state)
        if self.count < self.buffer_size:
            self.buffer.append(experience)
            self.count += 1
        else:
            self.buffer.popleft()
            self.buffer.append(experience)

    def size(self) -> int:
        return self.count

    def sample_batch(self, batch_size: int) -> Tuple[np.ndarray, ...]:
        if self.count < batch_size:
            batch = random.sample(self.buffer, self.count)
        else:
            batch = random.sample(self.buffer, batch_size)
        states = np.array([item[0] for item in batch])
        actions = np.array([item[1] for item in batch])
        rewards = np.array([item[2] for item in batch]).reshape(-1, 1)
        dones = np.array([item[3] for item in batch]).reshape(-1, 1)
        next_states = np.array([item[4] for item in batch])
        return states, actions, rewards, dones, next_states

    def clear(self) -> None:
        self.buffer.clear()
        self.count = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check deterministic ReplayBuffer eviction and underfill behavior."
    )
    parser.add_argument("--capacity", type=int, default=3)
    parser.add_argument("--requested-batch", type=int, default=5)
    parser.add_argument("--seed", type=int, default=123)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.capacity < 1 or args.requested_batch < 1:
        raise SystemExit("capacity and requested batch must be positive")

    buffer = ReplayBuffer(args.capacity, args.seed)
    # The identifier is in state[0], making the eviction assertion independent
    # of random sampling order.
    for identifier in range(args.capacity + 1):
        state = np.array([identifier, identifier + 0.5], dtype=np.float32)
        action = np.array([-1.0 + identifier * 0.1, 1.0 - identifier * 0.1], dtype=np.float32)
        buffer.add(state, action, float(identifier), identifier % 2, state + 1)

    assert buffer.size() == args.capacity
    identifiers = {int(item[0][0]) for item in buffer.buffer}
    expected = set(range(1, args.capacity + 1))
    assert identifiers == expected, (identifiers, expected)

    states, actions, rewards, dones, next_states = buffer.sample_batch(args.requested_batch)
    sample_count = min(args.capacity, args.requested_batch)
    assert states.shape == (sample_count, 2), states.shape
    assert actions.shape == (sample_count, 2), actions.shape
    assert rewards.shape == (sample_count, 1), rewards.shape
    assert dones.shape == (sample_count, 1), dones.shape
    assert next_states.shape == (sample_count, 2), next_states.shape
    assert len(set(states[:, 0].astype(int))) == sample_count
    assert set(states[:, 0].astype(int)) <= expected

    buffer.clear()
    assert buffer.size() == 0
    assert len(buffer.buffer) == 0
    print(
        f"PASS capacity={args.capacity} sample_count={sample_count} "
        f"state_shape={states.shape} reward_shape={rewards.shape} cleared=True"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
