#!/usr/bin/env python3
"""Segment offline trajectories into fixed-horizon OPAL primitive windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _as_list(value, name):
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def segment_trajectories(trajectories, horizon):
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    segments = []
    dropped_tails = 0
    for trajectory_index, trajectory in enumerate(_as_list(trajectories, "trajectories")):
        states = _as_list(trajectory.get("states"), "states")
        actions = _as_list(trajectory.get("actions"), "actions")
        rewards = trajectory.get("rewards", [])
        if rewards is None:
            rewards = []
        if len(states) < len(actions):
            raise ValueError("states must contain at least as many entries as actions")
        usable = len(actions) - (len(actions) % horizon)
        dropped_tails += len(actions) - usable
        for start in range(0, usable, horizon):
            action_window = actions[start:start + horizon]
            state_window = states[start:start + horizon]
            reward_window = rewards[start:start + horizon] if isinstance(rewards, list) else []
            segments.append({
                "trajectory_id": trajectory.get("id", trajectory_index),
                "start": start,
                "horizon": horizon,
                "states": state_window,
                "actions": action_window,
                "initial_state": state_window[0],
                "reward_sum": sum(reward_window) if reward_window else 0.0,
                "metadata": trajectory.get("metadata", {}),
            })
    return {"segments": segments, "summary": {"segment_count": len(segments), "dropped_tails": dropped_tails, "horizon": horizon}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json")
    parser.add_argument("--horizon", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    trajectories = data.get("trajectories", data)
    result = segment_trajectories(trajectories, args.horizon)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
