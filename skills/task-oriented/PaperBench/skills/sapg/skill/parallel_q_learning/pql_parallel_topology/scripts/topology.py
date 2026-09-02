#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

REQUIRED_ROLES = ["actors", "replay", "value_learner", "policy_learner"]
REQUIRED_EDGES = [
    ["actors", "replay", "transition_batch"],
    ["replay", "value_learner", "sampled_transitions"],
    ["value_learner", "policy_learner", "q_estimates"],
    ["policy_learner", "actors", "policy_sync"],
]


def build_topology(num_envs: int, replay_capacity: int, actor_steps_per_tick: int, policy_updates_per_tick: int, value_updates_per_tick: int, sync_interval: int) -> dict:
    if num_envs <= 0:
        raise ValueError("num_envs must be positive")
    if replay_capacity <= 0:
        raise ValueError("replay_capacity must be positive")
    if actor_steps_per_tick <= 0:
        raise ValueError("actor_steps_per_tick must be positive")
    if policy_updates_per_tick < 0 or value_updates_per_tick < 0:
        raise ValueError("update counts must be non-negative")
    if sync_interval <= 0:
        raise ValueError("sync_interval must be positive")
    transitions_per_tick = num_envs * actor_steps_per_tick
    warnings = []
    if replay_capacity < transitions_per_tick:
        warnings.append("replay_capacity_smaller_than_one_actor_tick")
    return {
        "roles": REQUIRED_ROLES[:],
        "edges": REQUIRED_EDGES[:],
        "parameters": {
            "num_envs": num_envs,
            "replay_capacity": replay_capacity,
            "actor_steps_per_tick": actor_steps_per_tick,
            "policy_updates_per_tick": policy_updates_per_tick,
            "value_updates_per_tick": value_updates_per_tick,
            "sync_interval": sync_interval,
            "transitions_per_tick": transitions_per_tick,
        },
        "invariants": [
            "actors write off-policy transitions before learner consumption",
            "value learner samples replay independently of latest actor policy",
            "policy learner consumes value estimates and periodically synchronizes actors",
        ],
        "warnings": warnings,
    }


def validate_topology(topology: dict) -> list[str]:
    errors = []
    roles = topology.get("roles", [])
    edges = topology.get("edges", [])
    for role in REQUIRED_ROLES:
        if role not in roles:
            errors.append(f"missing role: {role}")
    for edge in REQUIRED_EDGES:
        if edge not in edges:
            errors.append(f"missing edge: {edge}")
    if topology.get("parameters", {}).get("transitions_per_tick", 0) <= 0:
        errors.append("transitions_per_tick must be positive")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-envs", type=int, required=True)
    parser.add_argument("--replay-capacity", type=int, required=True)
    parser.add_argument("--actor-steps-per-tick", type=int, default=1)
    parser.add_argument("--policy-updates-per-tick", type=int, default=1)
    parser.add_argument("--value-updates-per-tick", type=int, default=1)
    parser.add_argument("--sync-interval", type=int, default=4)
    args = parser.parse_args()
    topology = build_topology(args.num_envs, args.replay_capacity, args.actor_steps_per_tick, args.policy_updates_per_tick, args.value_updates_per_tick, args.sync_interval)
    errors = validate_topology(topology)
    print(json.dumps({"ok": not errors, "topology": topology, "errors": errors}, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
