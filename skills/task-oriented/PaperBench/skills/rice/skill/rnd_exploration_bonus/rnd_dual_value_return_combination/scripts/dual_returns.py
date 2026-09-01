#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def compute_returns(rewards: list[float], dones: list[bool], gamma: float, episodic: bool) -> list[float]:
    running = 0.0
    output = [0.0] * len(rewards)
    for index in range(len(rewards) - 1, -1, -1):
        if episodic and dones[index]:
            running = 0.0
        running = float(rewards[index]) + gamma * running
        output[index] = running
    return output


def combine_returns(extrinsic: list[float], intrinsic: list[float], dones: list[bool], gamma_e: float = 0.999, gamma_i: float = 0.99, intrinsic_non_episodic: bool = True) -> dict:
    if not (len(extrinsic) == len(intrinsic) == len(dones)):
        raise ValueError("reward and done sequences must have equal length")
    extrinsic_returns = compute_returns(extrinsic, dones, gamma_e, episodic=True)
    intrinsic_returns = compute_returns(intrinsic, dones, gamma_i, episodic=not intrinsic_non_episodic)
    combined = [e + i for e, i in zip(extrinsic_returns, intrinsic_returns)]
    return {"extrinsic_returns": extrinsic_returns, "intrinsic_returns": intrinsic_returns, "combined_returns": combined}


def _self_test() -> None:
    result = combine_returns([1.0, 0.0, 2.0], [0.5, 0.5, 0.5], [False, True, False], gamma_e=1.0, gamma_i=1.0, intrinsic_non_episodic=True)
    assert result["extrinsic_returns"] == [1.0, 0.0, 2.0]
    assert result["intrinsic_returns"] == [1.5, 1.0, 0.5]
    assert result["combined_returns"][0] == 2.5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    payload = json.load(__import__("sys").stdin)
    print(json.dumps(combine_returns(payload["extrinsic"], payload["intrinsic"], payload["dones"], payload.get("gamma_e", 0.999), payload.get("gamma_i", 0.99), payload.get("intrinsic_non_episodic", True)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
