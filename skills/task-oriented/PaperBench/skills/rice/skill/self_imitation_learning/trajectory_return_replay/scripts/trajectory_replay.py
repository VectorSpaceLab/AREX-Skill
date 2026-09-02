#!/usr/bin/env python3
"""Build discounted-return replay records for Self-Imitation Learning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def discounted_returns(steps: list[dict[str, Any]], gamma: float) -> list[float]:
    if not 0.0 <= gamma <= 1.0:
        raise ValueError("gamma must be in [0, 1]")
    returns = [0.0 for _ in steps]
    running = 0.0
    for index in range(len(steps) - 1, -1, -1):
        step = steps[index]
        reward = float(step.get("reward", 0.0))
        if index < len(steps) - 1 and bool(steps[index].get("done", False)):
            running = 0.0
        running = reward + gamma * running
        returns[index] = running
    return returns


def build_replay_records(steps: list[dict[str, Any]], gamma: float = 0.99, capacity: int | None = None) -> list[dict[str, Any]]:
    returns = discounted_returns(steps, gamma)
    records = []
    for index, (step, ret) in enumerate(zip(steps, returns)):
        if "state" not in step or "action" not in step:
            raise ValueError("each step must contain state and action")
        records.append(
            {
                "index": index,
                "state": step["state"],
                "action": step["action"],
                "reward": float(step.get("reward", 0.0)),
                "return": ret,
                "done": bool(step.get("done", False)),
            }
        )
    if capacity is not None and capacity >= 0:
        records = records[-capacity:]
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_json")
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--capacity", type=int, default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    steps = json.loads(Path(args.episode_json).read_text(encoding="utf-8"))
    records = build_replay_records(steps, gamma=args.gamma, capacity=args.capacity)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
