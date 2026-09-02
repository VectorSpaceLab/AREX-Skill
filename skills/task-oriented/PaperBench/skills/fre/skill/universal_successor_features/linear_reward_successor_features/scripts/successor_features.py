#!/usr/bin/env python3
"""Deterministic helpers for linear rewards and successor-feature TD targets."""

from __future__ import annotations

import argparse
import json
from typing import Iterable, List, Sequence


def _as_float_list(values: Iterable[float], name: str) -> List[float]:
    result = [float(value) for value in values]
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _check_same_dimension(*vectors: Sequence[float]) -> None:
    dimensions = {len(vector) for vector in vectors}
    if len(dimensions) != 1:
        raise ValueError(f"dimension mismatch: {sorted(dimensions)}")


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    _check_same_dimension(left, right)
    return sum(a * b for a, b in zip(left, right))


def linear_reward(phi: Sequence[float], weights: Sequence[float]) -> float:
    return dot(phi, weights)


def q_value(psi: Sequence[float], weights: Sequence[float]) -> float:
    return dot(psi, weights)


def sf_target(phi: Sequence[float], next_psi: Sequence[float], gamma: float, terminal: bool = False) -> List[float]:
    _check_same_dimension(phi, next_psi)
    if terminal:
        return [float(value) for value in phi]
    return [float(feature) + float(gamma) * float(next_value) for feature, next_value in zip(phi, next_psi)]


def td_error(psi: Sequence[float], target: Sequence[float]) -> List[float]:
    _check_same_dimension(psi, target)
    return [float(target_value) - float(value) for value, target_value in zip(psi, target)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phi", nargs="+", type=float, required=True)
    parser.add_argument("--w", nargs="+", type=float, required=True)
    parser.add_argument("--psi", nargs="+", type=float, required=True)
    parser.add_argument("--next-psi", nargs="+", type=float, required=True)
    parser.add_argument("--gamma", type=float, default=1.0)
    parser.add_argument("--terminal", action="store_true")
    args = parser.parse_args()
    phi = _as_float_list(args.phi, "phi")
    weights = _as_float_list(args.w, "w")
    psi = _as_float_list(args.psi, "psi")
    next_psi = _as_float_list(args.next_psi, "next_psi")
    target = sf_target(phi, next_psi, args.gamma, args.terminal)
    output = {
        "reward": linear_reward(phi, weights),
        "q_value": q_value(psi, weights),
        "target": target,
        "td_error": td_error(psi, target),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
