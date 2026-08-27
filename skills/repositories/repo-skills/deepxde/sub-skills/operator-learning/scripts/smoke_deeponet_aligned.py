#!/usr/bin/env python3
"""Tiny aligned DeepONet smoke test for DeepXDE.

The script creates a synthetic antiderivative-operator dataset in the
TripleCartesianProd layout, compiles a DeepONetCartesianProd, trains for a small
number of iterations, and verifies finite prediction shapes. It is deterministic
and writes no files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny synthetic aligned DeepONet smoke test with "
            "dde.data.TripleCartesianProd and dde.nn.DeepONetCartesianProd."
        )
    )
    parser.add_argument(
        "--backend",
        default=os.environ.get("DDE_BACKEND", "pytorch"),
        help="DeepXDE backend to select before import (default: DDE_BACKEND or pytorch).",
    )
    parser.add_argument(
        "--allow-gpu",
        action="store_true",
        help="Do not hide CUDA devices before importing PyTorch-backed DeepXDE.",
    )
    parser.add_argument("--functions", type=int, default=6, help="Number of training functions.")
    parser.add_argument("--test-functions", type=int, default=3, help="Number of test functions.")
    parser.add_argument("--sensors", type=int, default=8, help="Number of branch sensor points.")
    parser.add_argument("--points", type=int, default=8, help="Number of trunk/output points.")
    parser.add_argument("--hidden", type=int, default=16, help="Hidden width for branch and trunk nets.")
    parser.add_argument("--iterations", type=int, default=1, help="Adam iterations to run.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Adam learning rate.")
    parser.add_argument("--seed", type=int, default=1234, help="Random seed for NumPy and DeepXDE.")
    parser.add_argument("--verbose", action="store_true", help="Show DeepXDE compile/train output.")
    return parser.parse_args()


@dataclass(frozen=True)
class SyntheticAlignedData:
    branch: object
    trunk: object
    labels: object


def _check_positive(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}.")


def make_antiderivative_data(n_functions: int, n_sensors: int, n_points: int, seed: int):
    import numpy as np

    rng = np.random.default_rng(seed)
    sensors = np.linspace(0.0, 1.0, n_sensors, dtype=np.float32)[:, None]
    trunk = np.linspace(0.0, 1.0, n_points, dtype=np.float32)[:, None]
    coeffs = rng.normal(loc=0.0, scale=0.5, size=(n_functions, 3)).astype(np.float32)

    def forcing(x):
        x_row = x[:, 0][None, :]
        return (
            coeffs[:, 0:1]
            + coeffs[:, 1:2] * x_row
            + coeffs[:, 2:3] * np.sin(np.pi * x_row)
        ).astype(np.float32)

    def antiderivative(x):
        x_row = x[:, 0][None, :]
        return (
            coeffs[:, 0:1] * x_row
            + 0.5 * coeffs[:, 1:2] * x_row**2
            + coeffs[:, 2:3] * (1.0 - np.cos(np.pi * x_row)) / np.pi
        ).astype(np.float32)

    return SyntheticAlignedData(branch=forcing(sensors), trunk=trunk, labels=antiderivative(trunk))


def run() -> dict:
    args = parse_args()
    for name in ["functions", "test_functions", "sensors", "points", "hidden", "iterations"]:
        _check_positive(name, int(getattr(args, name)))

    os.environ["DDE_BACKEND"] = args.backend
    if args.backend == "pytorch" and not args.allow_gpu:
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

    try:
        import numpy as np
        import deepxde as dde
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(
            "Failed to import DeepXDE after setting DDE_BACKEND. Install DeepXDE "
            "and the selected backend, or choose --backend pytorch in a PyTorch CPU environment."
        ) from exc

    dde.config.set_random_seed(args.seed)

    train = make_antiderivative_data(args.functions, args.sensors, args.points, args.seed)
    test = make_antiderivative_data(args.test_functions, args.sensors, args.points, args.seed + 1)

    if train.labels.shape != (args.functions, args.points):
        raise AssertionError(f"Unexpected train label shape {train.labels.shape}.")
    if train.branch.shape != (args.functions, args.sensors):
        raise AssertionError(f"Unexpected branch shape {train.branch.shape}.")
    if train.trunk.shape != (args.points, 1):
        raise AssertionError(f"Unexpected trunk shape {train.trunk.shape}.")

    data = dde.data.TripleCartesianProd(
        X_train=(train.branch, train.trunk),
        y_train=train.labels,
        X_test=(test.branch, test.trunk),
        y_test=test.labels,
    )
    net = dde.nn.DeepONetCartesianProd(
        [args.sensors, args.hidden, args.hidden],
        [1, args.hidden, args.hidden],
        "tanh",
        "Glorot normal",
    )
    model = dde.Model(data, net)
    model.compile("adam", lr=args.lr, verbose=1 if args.verbose else 0)
    model.train(iterations=args.iterations, display_every=args.iterations, verbose=1 if args.verbose else 0)

    pred = model.predict((test.branch[:1], test.trunk))
    pred_array = np.asarray(pred)
    expected_shape = (1, args.points)
    if pred_array.shape != expected_shape:
        raise AssertionError(f"Expected prediction shape {expected_shape}, got {pred_array.shape}.")
    if not np.all(np.isfinite(pred_array)):
        raise AssertionError("Prediction contains non-finite values.")

    return {
        "status": "ok",
        "backend": dde.backend.backend_name,
        "train_branch_shape": list(train.branch.shape),
        "train_trunk_shape": list(train.trunk.shape),
        "train_y_shape": list(train.labels.shape),
        "prediction_shape": list(pred_array.shape),
        "iterations": args.iterations,
    }


def main() -> int:
    try:
        print(json.dumps(run(), sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"smoke_deeponet_aligned failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
