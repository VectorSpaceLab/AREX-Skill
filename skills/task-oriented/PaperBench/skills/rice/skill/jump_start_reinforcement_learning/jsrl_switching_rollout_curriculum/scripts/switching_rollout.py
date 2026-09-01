#!/usr/bin/env python3
"""Switching rollout and curriculum utilities for JSRL."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from typing import Callable


Policy = Callable[[int], int]


@dataclass
class ChainEnv:
    length: int = 7
    state: int = 0

    @property
    def goal(self) -> int:
        return self.length - 1

    def reset(self) -> int:
        self.state = 0
        return self.state

    def step(self, action: int) -> tuple[int, float, bool, dict]:
        if action not in {-1, 1}:
            raise ValueError(f"invalid action: {action}")
        old_state = self.state
        self.state = max(0, min(self.goal, self.state + action))
        done = self.state == self.goal
        reward = 1.0 if done else 0.0
        return self.state, reward, done, {"old_state": old_state}


def right_policy(state: int) -> int:
    return 1


def left_policy(state: int) -> int:
    return -1


def rollout_switching(env: ChainEnv, guide_policy: Policy, exploration_policy: Policy, horizon: int, guide_steps: int) -> dict:
    guide_steps = max(0, min(int(guide_steps), int(horizon)))
    state = env.reset()
    transitions: list[dict] = []
    total_reward = 0.0
    for t in range(horizon):
        controller = "guide" if t < guide_steps else "exploration"
        policy = guide_policy if controller == "guide" else exploration_policy
        action = int(policy(state))
        next_state, reward, done, info = env.step(action)
        transitions.append({
            "t": t,
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "controller": controller,
            "info": info,
        })
        total_reward += reward
        state = next_state
        if done:
            break
    guide_count = sum(1 for row in transitions if row["controller"] == "guide")
    exploration_count = sum(1 for row in transitions if row["controller"] == "exploration")
    return {
        "horizon": horizon,
        "guide_steps": guide_steps,
        "trajectory": transitions,
        "summary": {
            "guide_action_count": guide_count,
            "exploration_action_count": exploration_count,
            "total_reward": total_reward,
            "success": bool(transitions and transitions[-1]["done"]),
            "final_state": state,
        },
    }


def maybe_advance_curriculum(schedule: list[int], cursor: int, evaluation: float, beta: float) -> int:
    if evaluation >= beta:
        return min(cursor + 1, len(schedule) - 1)
    return cursor


def select_guide_steps(schedule: list[int], cursor: int = 0, strategy: str = "curriculum", seed: int = 0) -> int:
    if strategy == "curriculum":
        return int(schedule[max(0, min(cursor, len(schedule) - 1))])
    if strategy == "random":
        rng = random.Random(seed)
        return int(rng.choice(schedule))
    raise ValueError(f"unknown strategy: {strategy}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    report = rollout_switching(ChainEnv(), right_policy, left_policy, horizon=6, guide_steps=3)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
