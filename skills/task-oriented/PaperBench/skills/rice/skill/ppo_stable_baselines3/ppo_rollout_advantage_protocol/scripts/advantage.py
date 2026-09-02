from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def compute_gae(steps: Iterable[dict], last_value: float, gamma: float = 0.99, gae_lambda: float = 0.95) -> dict:
    rollout = list(steps)
    if not rollout:
        raise ValueError("rollout must contain at least one step")
    if not (0.0 <= gamma <= 1.0 and 0.0 <= gae_lambda <= 1.0):
        raise ValueError("gamma and gae_lambda must be in [0, 1]")
    advantages = [0.0 for _ in rollout]
    deltas = [0.0 for _ in rollout]
    gae = 0.0
    terminal_resets = 0
    for index in range(len(rollout) - 1, -1, -1):
        step = rollout[index]
        reward = float(step["reward"])
        value = float(step["value"])
        done = bool(step.get("done", False))
        if index == len(rollout) - 1:
            next_value = float(last_value)
        else:
            next_value = float(rollout[index + 1]["value"])
        next_nonterminal = 0.0 if done else 1.0
        if done:
            terminal_resets += 1
        delta = reward + gamma * next_value * next_nonterminal - value
        gae = delta + gamma * gae_lambda * next_nonterminal * gae
        deltas[index] = delta
        advantages[index] = gae
    returns = [advantage + float(step["value"]) for advantage, step in zip(advantages, rollout)]
    return {
        "advantages": advantages,
        "returns": returns,
        "deltas": deltas,
        "diagnostics": {"step_count": len(rollout), "terminal_resets": terminal_resets},
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = compute_gae(data["steps"], data.get("last_value", 0.0), args.gamma, args.gae_lambda)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
