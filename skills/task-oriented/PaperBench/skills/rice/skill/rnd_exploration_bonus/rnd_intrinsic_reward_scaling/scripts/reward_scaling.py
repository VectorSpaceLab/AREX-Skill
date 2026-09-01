#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math


def discounted_returns(rewards: list[float], gamma: float, initial: float = 0.0) -> list[float]:
    running = initial
    output = []
    for reward in reversed(rewards):
        running = float(reward) + gamma * running
        output.append(running)
    return list(reversed(output))


def stats(values: list[float]) -> dict:
    mean = sum(values) / len(values)
    var = sum((value - mean) ** 2 for value in values) / len(values)
    return {"mean": mean, "var": var, "count": len(values), "std": math.sqrt(var)}


def scale_intrinsic_rewards(errors: list[float], gamma: float = 0.99, eps: float = 1e-8) -> dict:
    returns = discounted_returns(errors, gamma)
    scale_stats = stats(returns)
    denom = math.sqrt(scale_stats["var"] + eps)
    return {"raw_errors": errors, "discounted_returns": returns, "stats": scale_stats, "scaled_rewards": [error / denom for error in errors]}


def _self_test() -> None:
    result = scale_intrinsic_rewards([1.0, 0.5, 0.25], gamma=0.9)
    assert result["discounted_returns"][0] > result["discounted_returns"][-1]
    assert all(math.isfinite(value) for value in result["scaled_rewards"])
    assert result["scaled_rewards"][0] > result["scaled_rewards"][-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    payload = json.load(__import__("sys").stdin)
    print(json.dumps(scale_intrinsic_rewards(payload["errors"], payload.get("gamma", 0.99)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
