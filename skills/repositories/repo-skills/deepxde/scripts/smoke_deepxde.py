#!/usr/bin/env python3
"""Safe DeepXDE import and tiny PDE smoke.

The default path verifies the PyTorch CPU baseline used by this generated skill.
It selects DDE_BACKEND before importing DeepXDE, imports package metadata, and
optionally runs a one-dimensional Poisson PINN for a few iterations. The script
is deterministic, does not download data, and writes no files.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check DeepXDE import/backend and optionally run a tiny PyTorch CPU PDE smoke."
    )
    parser.add_argument(
        "--backend",
        default=os.environ.get("DDE_BACKEND", "pytorch"),
        choices=("tensorflow.compat.v1", "tensorflow", "pytorch", "jax", "paddle"),
        help="Backend to select before importing DeepXDE (default: DDE_BACKEND or pytorch).",
    )
    parser.add_argument(
        "--train-steps",
        type=int,
        default=0,
        help="Run a tiny Poisson PINN for this many Adam iterations. Use 0 for import-only.",
    )
    parser.add_argument(
        "--allow-gpu",
        action="store_true",
        help="Do not hide CUDA devices for the PyTorch smoke. Omit for CPU-safe diagnostics.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument("--seed", type=int, default=1234, help="Random seed for the optional smoke.")
    return parser.parse_args(argv)


def distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_tiny_pde(dde: Any, steps: int, seed: int) -> dict[str, Any]:
    import numpy as np

    if dde.backend.backend_name != "pytorch":
        raise RuntimeError(
            "The bundled training smoke is verified only for the PyTorch backend. "
            "Run import-only diagnostics for other backends or use their own verified smoke."
        )
    from deepxde.backend import torch

    dde.config.set_random_seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    geom = dde.geometry.Interval(-1.0, 1.0)

    def exact(x: Any) -> Any:
        return np.sin(np.pi * x)

    def boundary(_x: Any, on_boundary: bool) -> bool:
        return on_boundary

    def pde(x: Any, y: Any) -> Any:
        return -dde.grad.hessian(y, x) - (np.pi**2) * torch.sin(np.pi * x)

    data = dde.data.PDE(
        geom,
        pde,
        dde.icbc.DirichletBC(geom, exact, boundary),
        num_domain=8,
        num_boundary=2,
        train_distribution="Hammersley",
        solution=exact,
        num_test=16,
    )
    net = dde.nn.FNN([1, 8, 8, 1], "tanh", "Glorot uniform")
    model = dde.Model(data, net)
    model.compile("adam", lr=1e-3, verbose=0)
    losshistory, train_state = model.train(
        iterations=steps,
        display_every=max(1, steps),
        verbose=0,
    )
    x_eval = np.linspace(-1.0, 1.0, 5)[:, None]
    y_pred = model.predict(x_eval)
    residual = model.predict(x_eval, operator=pde)

    if not np.all(np.isfinite(y_pred)):
        raise RuntimeError("Prediction contains non-finite values.")
    if not np.all(np.isfinite(residual)):
        raise RuntimeError("Residual contains non-finite values.")

    return {
        "train_steps": steps,
        "loss_steps": len(losshistory.steps),
        "best_step": int(train_state.best_step),
        "prediction_shape": list(y_pred.shape),
        "residual_shape": list(residual.shape),
        "max_abs_residual": float(np.max(np.abs(residual))),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.train_steps < 0:
        print("ERROR: --train-steps must be >= 0", file=sys.stderr)
        return 2

    os.environ["DDE_BACKEND"] = args.backend
    if args.backend == "pytorch" and not args.allow_gpu:
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

    result: dict[str, Any] = {
        "ok": False,
        "requested_backend": args.backend,
        "deepxde_distribution_version": distribution_version("DeepXDE"),
        "backend": None,
        "deepxde_version": None,
        "smoke": None,
        "messages": [],
    }

    try:
        import deepxde as dde

        result["backend"] = dde.backend.backend_name
        result["deepxde_version"] = getattr(dde, "__version__", None)
        if result["backend"] != args.backend:
            result["messages"].append(
                f"DeepXDE reported backend {result['backend']!r}; expected {args.backend!r}. "
                "Set DDE_BACKEND before every import and check persistent config."
            )
        if args.train_steps:
            result["smoke"] = run_tiny_pde(dde, args.train_steps, args.seed)
        else:
            result["messages"].append("Import-only check passed; use --train-steps 1 for a tiny PDE smoke.")
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001 - CLI diagnostic.
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["messages"].append(
            "Install DeepXDE and the selected backend package stack, set DDE_BACKEND before import, "
            "or retry the verified CPU path with --backend pytorch."
        )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("DeepXDE smoke diagnostic")
        print(f"  requested backend: {result['requested_backend']}")
        print(f"  distribution version: {result['deepxde_distribution_version']}")
        print(f"  imported version: {result['deepxde_version']}")
        print(f"  backend: {result['backend']}")
        if result.get("smoke"):
            print("  tiny PDE smoke: ok")
            for key, value in result["smoke"].items():
                print(f"    {key}: {value}")
        if result.get("error"):
            print(f"  error: {result['error']}")
        for message in result["messages"]:
            print(f"  - {message}")
        print(f"Status: {'ok' if result['ok'] else 'failed'}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
