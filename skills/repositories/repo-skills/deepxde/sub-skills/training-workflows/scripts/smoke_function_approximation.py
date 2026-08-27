#!/usr/bin/env python3
"""Tiny DeepXDE function-approximation smoke for PyTorch CPU.

Adapted from DeepXDE's function approximation example, but intentionally tiny,
headless, deterministic, and safe for agent/CI use. The script sets
DDE_BACKEND=pytorch before importing DeepXDE unless the caller already selected
another backend.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Must happen before importing deepxde.
os.environ.setdefault("DDE_BACKEND", "pytorch")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny DeepXDE Function + FNN training smoke without plots."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of Adam training iterations to run (default: 3).",
    )
    parser.add_argument(
        "--num-train",
        type=int,
        default=8,
        help="Number of function training points (default: 8).",
    )
    parser.add_argument(
        "--num-test",
        type=int,
        default=16,
        help="Number of function test points (default: 16).",
    )
    parser.add_argument(
        "--hidden-width",
        type=int,
        default=8,
        help="Width of two tanh hidden layers (default: 8).",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
        help="Adam learning rate (default: 1e-3).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Random seed passed to DeepXDE when supported (default: 1234).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for a JSON summary; no files are written by default.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.iterations < 1:
        raise ValueError("--iterations must be >= 1")
    if args.num_train < 2:
        raise ValueError("--num-train must be >= 2")
    if args.num_test < 2:
        raise ValueError("--num-test must be >= 2")
    if args.hidden_width < 1:
        raise ValueError("--hidden-width must be >= 1")
    if args.lr <= 0:
        raise ValueError("--lr must be positive")


def main() -> int:
    args = parse_args()
    validate_args(args)

    # Import after setting DDE_BACKEND.
    import numpy as np
    import deepxde as dde

    try:
        dde.config.set_random_seed(args.seed)
    except Exception:
        # Some backend combinations can fail to enforce determinism; the smoke should
        # still report train-loop health rather than fail before model construction.
        pass

    def func(x: np.ndarray) -> np.ndarray:
        """Target f(x) = x sin(5x), with x shaped (N, 1)."""
        return x * np.sin(5 * x)

    geom = dde.geometry.Interval(-1, 1)
    data = dde.data.Function(
        geom,
        func,
        num_train=args.num_train,
        num_test=args.num_test,
    )
    net = dde.nn.FNN(
        [1, args.hidden_width, args.hidden_width, 1],
        "tanh",
        "Glorot uniform",
    )
    model = dde.Model(data, net)
    model.compile("adam", lr=args.lr, metrics=["l2 relative error"], verbose=0)
    losshistory, train_state = model.train(
        iterations=args.iterations,
        display_every=max(1, args.iterations),
        verbose=0,
    )

    x_eval = np.linspace(-1.0, 1.0, 5, dtype=np.float32)[:, None]
    y_pred = model.predict(x_eval)
    final_train_loss = np.asarray(losshistory.loss_train[-1], dtype=float)
    final_test_loss = np.asarray(losshistory.loss_test[-1], dtype=float)
    metrics_test = np.asarray(losshistory.metrics_test[-1], dtype=float)

    if not np.all(np.isfinite(y_pred)):
        raise RuntimeError("prediction contains non-finite values")
    if not np.all(np.isfinite(final_train_loss)):
        raise RuntimeError("final train loss contains non-finite values")
    if not np.all(np.isfinite(final_test_loss)):
        raise RuntimeError("final test loss contains non-finite values")

    summary = {
        "backend": os.environ.get("DDE_BACKEND"),
        "iterations": args.iterations,
        "num_train": args.num_train,
        "num_test": args.num_test,
        "hidden_width": args.hidden_width,
        "prediction_shape": list(y_pred.shape),
        "final_train_loss": final_train_loss.tolist(),
        "final_test_loss": final_test_loss.tolist(),
        "final_metrics_test": metrics_test.tolist(),
        "best_step": int(train_state.best_step),
        "ok": True,
    }

    print(json.dumps(summary, indent=2, sort_keys=True))

    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = args.output_dir / "smoke_function_approximation_summary.json"
        output_file.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - produce concise CLI diagnostics.
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
