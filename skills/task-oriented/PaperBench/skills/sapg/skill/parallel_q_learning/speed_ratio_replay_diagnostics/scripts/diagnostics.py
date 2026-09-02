#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def compute_diagnostics(num_envs: int, rollout_steps: int, replay_capacity: int, actor_rate: float, policy_rate: float, value_rate: float) -> dict:
    for name, value in {
        "num_envs": num_envs,
        "rollout_steps": rollout_steps,
        "replay_capacity": replay_capacity,
        "actor_rate": actor_rate,
        "policy_rate": policy_rate,
        "value_rate": value_rate,
    }.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive")
    transitions_per_tick = num_envs * rollout_steps
    replay_refresh_ticks = replay_capacity / transitions_per_tick
    actor_to_value_ratio = actor_rate / value_rate
    policy_to_value_ratio = policy_rate / value_rate
    warnings = []
    if replay_refresh_ticks <= 100:
        warnings.append("high_replay_overwrite_pressure")
    if actor_to_value_ratio > 50:
        warnings.append("actor_throughput_may_outpace_value_learning")
    if policy_to_value_ratio > 2:
        warnings.append("policy_updates_may_outpace_value_targets")
    if policy_to_value_ratio < 0.05:
        warnings.append("policy_learning_may_lag_value_learning")
    return {
        "transitions_per_tick": transitions_per_tick,
        "replay_refresh_ticks": replay_refresh_ticks,
        "actor_to_value_ratio": actor_to_value_ratio,
        "policy_to_value_ratio": policy_to_value_ratio,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-envs", type=int, required=True)
    parser.add_argument("--rollout-steps", type=int, default=1)
    parser.add_argument("--replay-capacity", type=int, required=True)
    parser.add_argument("--actor-rate", type=float, required=True)
    parser.add_argument("--policy-rate", type=float, required=True)
    parser.add_argument("--value-rate", type=float, required=True)
    args = parser.parse_args()
    result = compute_diagnostics(args.num_envs, args.rollout_steps, args.replay_capacity, args.actor_rate, args.policy_rate, args.value_rate)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
