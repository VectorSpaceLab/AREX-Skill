#!/usr/bin/env python3
"""Tiny CPU-only PhySO SR smoke adapted from the canonical SR quick start."""

from __future__ import annotations

import argparse
import copy
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

import physo
import physo.learn.monitoring as monitoring

OP_NAMES = [
    "mul", "add", "sub", "div", "inv", "n2", "sqrt", "neg",
    "exp", "log", "sin", "cos",
]


def identity_wrapper(func, X):
    """Picklable identity wrapper showing the candidate_wrapper signature."""
    return func(X)


def build_dataset():
    """Return a small dimensionless weighted single-dataset SR fixture."""
    n_samples = 24
    x0 = np.linspace(-1.0, 1.0, n_samples, dtype=float)
    x1 = np.linspace(0.2, 1.2, n_samples, dtype=float)
    X = np.stack((x0, x1), axis=0)
    y = 0.75 * x0 + 0.25 * x1**2
    y_weights = np.ones_like(y)
    y_weights[n_samples // 2 :] = 4.0
    return X, y, y_weights


def make_smoke_config(preset):
    """Use a light preset with a smaller batch for a quick package check."""
    preset_module = getattr(physo.config, preset)
    run_config = copy.deepcopy(getattr(preset_module, preset))
    run_config["learning_config"]["batch_size"] = 256
    return run_config


def run_smoke(preset) -> None:
    if preset not in {"config0", "config0b"}:
        raise ValueError("preset must be config0 or config0b")

    np.random.seed(0)
    torch.manual_seed(0)

    X, y, y_weights = build_dataset()
    assert X.shape == (2, y.shape[0])
    assert y_weights.shape == y.shape

    run_logger = lambda: monitoring.RunLogger(save_path=None, do_save=False)
    run_visualiser = lambda: None

    expression, logs = physo.SR(
        X,
        y,
        y_weights=y_weights,
        X_names=["x0", "x1"],
        X_units=[[0, 0, 0], [0, 0, 0]],
        y_name="y",
        y_units=[0, 0, 0],
        fixed_consts=[1.0],
        fixed_consts_units=[[0, 0, 0]],
        free_consts_names=["a", "b"],
        free_consts_units=[[0, 0, 0], [0, 0, 0]],
        op_names=OP_NAMES,
        candidate_wrapper=identity_wrapper,
        run_config=make_smoke_config(preset),
        get_run_logger=run_logger,
        get_run_visualiser=run_visualiser,
        parallel_mode=False,
        n_cpus=1,
        device="cpu",
        epochs=4,
    )

    complexities, programs, rewards, rmse = logs.get_pareto_front()
    if len(programs) == 0:
        raise RuntimeError("empty Pareto front after SR smoke")

    with tempfile.TemporaryDirectory(prefix="physo_sr_smoke_") as tmp_dir:
        pareto_path = Path(tmp_dir) / "pareto.pkl"
        monitoring.save_pareto_pkl([prog.detach() for prog in programs], pareto_path)
        reloaded = physo.read_pareto_pkl(pareto_path)
        if len(reloaded) != len(programs):
            raise RuntimeError("reloaded Pareto pkl length mismatch")

    print("PhySO SR smoke: PASS")
    print(
        f"preset={preset} pareto_size={len(programs)} "
        f"best_reward={float(rewards[-1]):.6f} best_rmse={float(rmse[-1]):.6g}"
    )
    print("best_expression:")
    print(expression.get_infix_pretty())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=("config0", "config0b"), default="config0")
    args = parser.parse_args(argv)
    try:
        run_smoke(args.preset)
    except Exception as exc:
        print("PhySO SR smoke: FAIL", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
