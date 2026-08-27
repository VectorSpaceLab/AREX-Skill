#!/usr/bin/env python3
"""Tiny CPU smoke for Jittor core Var, autograd, Module, and state transfer.

Safe defaults:
- no downloads
- no training data
- CPU only unless the user intentionally changes the environment
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny Jittor core API smoke check.")
    parser.add_argument("--steps", type=int, default=3, help="Number of tiny gradient steps to take.")
    parser.add_argument("--lr", type=float, default=0.1, help="Learning rate for the tiny update loop.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument("--seed", type=int, default=0, help="Seed for deterministic values.")
    return parser.parse_args()


def configure_environment() -> None:
    os.environ.setdefault("log_silent", "1")
    os.environ.setdefault("nvcc_path", "")


class TinyModule:
    pass


@dataclass
class SmokeResult:
    initial_loss: float
    final_loss: float
    grad_norm: float
    state_keys: List[str]
    cloned_state_keys: List[str]


def run_smoke(steps: int, lr: float, seed: int) -> SmokeResult:
    import numpy as np
    import jittor as jt

    np.random.seed(seed)
    jt.set_seed(seed)

    class LinearCore(jt.Module):
        def __init__(self) -> None:
            super().__init__()
            self.w = jt.random((3,))
            self.b = jt.random((3,))

        def execute(self, x):
            return (x * self.w).sum()

    model = LinearCore()
    params = model.parameters()
    if len(params) != 2:
        raise AssertionError(f"expected 2 parameters, got {len(params)}")

    x = jt.float32([0.1, 0.2, 0.3])
    target = jt.float32([1.0])

    def loss_value() -> Any:
        pred = model(x)
        return ((pred - target) ** 2).mean()

    initial = loss_value()
    initial_loss = float(initial.data.reshape(-1)[0])

    last_grads = None
    for _ in range(steps):
        loss = loss_value()
        grads = jt.grad(loss, params)
        last_grads = grads
        for p, g in zip(params, grads):
            p -= lr * g
    final = loss_value()
    final_loss = float(final.data.reshape(-1)[0])

    assert last_grads is not None
    grad_norm = float(sum(float((g * g).sum().data.reshape(-1)[0]) for g in last_grads)) ** 0.5

    state = model.state_dict()
    state_keys = sorted(state.keys())
    clone = LinearCore()
    clone.load_state_dict(state)
    cloned_state_keys = sorted(clone.state_dict().keys())

    return SmokeResult(
        initial_loss=initial_loss,
        final_loss=final_loss,
        grad_norm=grad_norm,
        state_keys=state_keys,
        cloned_state_keys=cloned_state_keys,
    )


def main() -> int:
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")
    if args.lr <= 0:
        raise SystemExit("--lr must be positive")

    configure_environment()

    try:
        result = run_smoke(args.steps, args.lr, args.seed)
    except Exception as exc:  # pragma: no cover - CLI diagnostics path
        payload = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return 1

    payload: Dict[str, Any] = {
        "status": "passed",
        "initial_loss": result.initial_loss,
        "final_loss": result.final_loss,
        "grad_norm": result.grad_norm,
        "state_keys": result.state_keys,
        "cloned_state_keys": result.cloned_state_keys,
    }
    if payload["final_loss"] > payload["initial_loss"]:
        payload["status"] = "failed"
        payload["error"] = "final loss did not decrease"
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print("core API smoke failed: final loss did not decrease", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("core API smoke passed")
        print(f"initial_loss: {payload['initial_loss']:.6f}")
        print(f"final_loss: {payload['final_loss']:.6f}")
        print(f"grad_norm: {payload['grad_norm']:.6f}")
        print(f"state_keys: {payload['state_keys']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
