#!/usr/bin/env python3
"""Tiny DeepXDE Poisson PINN smoke test.

This script is intentionally small and backend-safe for the verified PyTorch CPU
path. It checks that basic problem assembly, compilation, a couple of training
iterations, prediction, and residual prediction all work.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import warnings
from types import ModuleType

import numpy as np

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="The pynvml package is deprecated.*",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny 1D Poisson PINN smoke test with DeepXDE."
    )
    parser.add_argument(
        "--backend",
        choices=("pytorch",),
        default="pytorch",
        help="DeepXDE backend to use. This smoke is verified only for PyTorch.",
    )
    parser.add_argument("--seed", type=int, default=1234, help="Random seed.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=2,
        help="Training iterations to run (keep tiny for smoke testing).",
    )
    parser.add_argument(
        "--num-domain",
        type=int,
        default=16,
        help="Number of interior training points.",
    )
    parser.add_argument(
        "--num-boundary",
        type=int,
        default=2,
        help="Number of boundary training points.",
    )
    parser.add_argument(
        "--num-test",
        type=int,
        default=32,
        help="Number of test points for the smoke prediction.",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
        help="Learning rate for the tiny Adam run.",
    )
    return parser.parse_args()


def _ensure_skopt_stub() -> None:
    if importlib.util.find_spec("skopt") is not None:
        return

    class _BaseSampler:
        def __init__(self, *args, **kwargs):
            pass

        def generate(self, space, n_samples):
            dim = len(space)
            if dim == 1:
                values = (np.arange(n_samples, dtype=float) + 0.5) / max(n_samples, 1)
                return values[:, None]
            return np.random.random((n_samples, dim))

    sampler_mod = ModuleType("skopt.sampler")
    sampler_mod.Lhs = _BaseSampler
    sampler_mod.Halton = _BaseSampler
    sampler_mod.Hammersly = _BaseSampler
    sampler_mod.Sobol = _BaseSampler

    skopt_mod = ModuleType("skopt")
    skopt_mod.sampler = sampler_mod
    sys.modules.setdefault("skopt", skopt_mod)
    sys.modules.setdefault("skopt.sampler", sampler_mod)


def main() -> int:
    args = parse_args()
    os.environ["DDE_BACKEND"] = args.backend
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    _ensure_skopt_stub()

    import deepxde as dde
    from deepxde.backend import torch

    dde.config.set_random_seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    geom = dde.geometry.Interval(-1.0, 1.0)

    def boundary(_, on_boundary):
        return on_boundary

    def exact(x):
        return np.sin(np.pi * x)

    def pde(x, y):
        dy_xx = dde.grad.hessian(y, x)
        return -dy_xx - (np.pi**2) * torch.sin(np.pi * x)

    bc = dde.icbc.DirichletBC(geom, exact, boundary)
    data = dde.data.PDE(
        geom,
        pde,
        bc,
        num_domain=args.num_domain,
        num_boundary=args.num_boundary,
        train_distribution="Hammersley",
        solution=exact,
        num_test=args.num_test,
    )

    net = dde.nn.FNN([1, 16, 16, 1], "tanh", "Glorot uniform")
    model = dde.Model(data, net)
    model.compile("adam", lr=args.lr, verbose=0)
    model.train(iterations=args.iterations, display_every=max(1, args.iterations), verbose=0)

    x = np.linspace(-1.0, 1.0, 9)[:, None]
    y_pred = model.predict(x)
    residual = model.predict(x, operator=pde)

    if not np.all(np.isfinite(y_pred)):
        raise RuntimeError("Prediction contained non-finite values.")
    if not np.all(np.isfinite(residual)):
        raise RuntimeError("Residual prediction contained non-finite values.")

    summary = {
        "backend": dde.backend.backend_name,
        "iterations": args.iterations,
        "prediction_shape": list(np.shape(y_pred)),
        "residual_shape": list(np.shape(residual)),
        "max_abs_residual": float(np.max(np.abs(residual))),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
