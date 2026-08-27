#!/usr/bin/env python3
"""Tiny CPU-first training smoke for Jittor.

The script fits a one-layer regression model on synthetic data, checks that the
loss decreases, and exercises train/eval plus no_grad state handling.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny Jittor training smoke on synthetic data.")
    parser.add_argument("--steps", type=int, default=20, help="Number of optimizer steps to run.")
    parser.add_argument("--batch-size", type=int, default=16, help="Synthetic batch size.")
    parser.add_argument("--lr", type=float, default=0.1, help="Learning rate for SGD.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for deterministic values.")
    parser.add_argument("--assert-loss-drop", action="store_true", help="Fail if the final loss is not lower than the initial loss.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    return parser.parse_args()


def configure_environment() -> None:
    os.environ.setdefault("log_silent", "1")
    os.environ.setdefault("nvcc_path", "")


def build_batch(jt: Any, np: Any, batch_size: int):
    x_np = np.linspace(-1.0, 1.0, batch_size, dtype="float32").reshape(batch_size, 1)
    y_np = (2.0 * x_np + 1.0).astype("float32")
    return jt.float32(x_np), jt.float32(y_np)


def main() -> int:
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")
    if args.lr <= 0:
        raise SystemExit("--lr must be positive")

    configure_environment()

    try:
        import numpy as np
        import jittor as jt
        from jittor import nn
    except Exception as exc:  # pragma: no cover - CLI diagnostics path
        payload = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return 1

    np.random.seed(args.seed)
    jt.set_seed(args.seed)

    class TinyRegressor(jt.Module):
        def __init__(self) -> None:
            super().__init__()
            self.linear = nn.Linear(1, 1)

        def execute(self, x):
            return self.linear(x)

    model = TinyRegressor()
    opt = nn.SGD(model.parameters(), args.lr)
    model.train()

    x, y = build_batch(jt, np, args.batch_size)
    losses: List[float] = []
    initial_pred = model(x)
    initial_loss_var = ((initial_pred - y) ** 2).mean()
    initial_loss = float(initial_loss_var.data.reshape(-1)[0])
    losses.append(initial_loss)

    for _ in range(args.steps):
        pred = model(x)
        loss = ((pred - y) ** 2).mean()
        losses.append(float(loss.data.reshape(-1)[0]))
        opt.step(loss)

    model.eval()
    with jt.no_grad():
        eval_loss_var = ((model(x) - y) ** 2).mean()
        eval_loss = float(eval_loss_var.data.reshape(-1)[0])

    state = model.state_dict()
    cloned = TinyRegressor()
    cloned.load_state_dict(state)

    result: Dict[str, Any] = {
        "status": "passed",
        "initial_loss": initial_loss,
        "final_train_loss": losses[-1],
        "eval_loss": eval_loss,
        "state_keys": sorted(state.keys()),
        "cloned_state_keys": sorted(cloned.state_dict().keys()),
        "losses": losses,
    }

    if args.assert_loss_drop and result["final_train_loss"] >= result["initial_loss"]:
        result["status"] = "failed"
        result["error"] = "final loss did not decrease"
        if args.json:
            print(json.dumps(result, sort_keys=True))
        else:
            print("training smoke failed: final loss did not decrease", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("training smoke passed")
        print(f"initial_loss: {result['initial_loss']:.6f}")
        print(f"final_train_loss: {result['final_train_loss']:.6f}")
        print(f"eval_loss: {result['eval_loss']:.6f}")
        print(f"state_keys: {result['state_keys']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
