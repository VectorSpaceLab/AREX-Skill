#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import Any

NumberTree = Any


def _map2(a: NumberTree, b: NumberTree, fn):
    if isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            raise ValueError("shape mismatch")
        return [_map2(x, y, fn) for x, y in zip(a, b)]
    if isinstance(b, list):
        raise ValueError("shape mismatch")
    return fn(float(a), float(b))


def _shape(x: NumberTree):
    shape = []
    while isinstance(x, list):
        shape.append(len(x))
        x = x[0] if x else []
    return shape


def diffuse(clean: NumberTree, noise: NumberTree, alpha_bar_t: float) -> NumberTree:
    if not (0.0 < alpha_bar_t <= 1.0):
        raise ValueError("alpha_bar_t must be in (0, 1]")
    sqrt_alpha = math.sqrt(alpha_bar_t)
    sqrt_one_minus = math.sqrt(1.0 - alpha_bar_t)
    return _map2(clean, noise, lambda x0, eps: sqrt_alpha * x0 + sqrt_one_minus * eps)


def reconstruct_x0(x_t: NumberTree, predicted_epsilon: NumberTree, alpha_bar_t: float) -> NumberTree:
    if not (0.0 < alpha_bar_t <= 1.0):
        raise ValueError("alpha_bar_t must be in (0, 1]")
    sqrt_alpha = math.sqrt(alpha_bar_t)
    sqrt_one_minus = math.sqrt(1.0 - alpha_bar_t)
    return _map2(x_t, predicted_epsilon, lambda xt, eps: (xt - sqrt_one_minus * eps) / sqrt_alpha)


def build_protocol(clean: NumberTree, noise: NumberTree, source_epsilon: NumberTree, adapted_epsilon: NumberTree, alpha_bar_t: float) -> dict:
    x_t = diffuse(clean, noise, alpha_bar_t)
    source_x0_hat = reconstruct_x0(x_t, source_epsilon, alpha_bar_t)
    adapted_x0_hat = reconstruct_x0(x_t, adapted_epsilon, alpha_bar_t)
    return {
        "x_t": x_t,
        "source_x0_hat": source_x0_hat,
        "adapted_x0_hat": adapted_x0_hat,
        "metadata": {"alpha_bar_t": alpha_bar_t, "shape": _shape(clean)},
    }


def _smoke() -> dict:
    clean = [[[[1.0, -1.0], [0.5, 0.0]]], [[[0.0, 0.25], [-0.5, 1.0]]]]
    noise = [[[[0.2, -0.1], [0.0, 0.3]]], [[[0.1, 0.1], [-0.2, 0.4]]]]
    out = build_protocol(clean, noise, noise, noise, 0.81)
    return {"ok": out["source_x0_hat"] == out["adapted_x0_hat"], "metadata": out["metadata"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        print(json.dumps(_smoke(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
