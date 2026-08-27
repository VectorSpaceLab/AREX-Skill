#!/usr/bin/env python3
"""Deterministic dense PyPose LM smoke.

The script intentionally imports the installed ``pypose`` package and does not
read the PyPose source checkout. See the nearest ../SKILL.md.
"""
from __future__ import annotations

import argparse
import sys

import torch
from torch import nn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny deterministic dense PyPose LM convergence smoke."
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Execution device (default: cpu).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=8,
        help="Maximum LM iterations (default: 8).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Torch seed for the deterministic fixture (default: 7).",
    )
    return parser.parse_args()


class LineResidual(nn.Module):
    """One scalar residual block per sample: a*x + b - target."""

    def __init__(self) -> None:
        super().__init__()
        self.slope = nn.Parameter(torch.tensor(0.0, dtype=torch.float64))
        self.intercept = nn.Parameter(torch.tensor(0.0, dtype=torch.float64))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Keep the final dimension visible so each sample is its own block.
        return (self.slope * x + self.intercept).unsqueeze(-1)


def main() -> int:
    args = parse_args()
    if args.steps < 1:
        print("error: --steps must be positive", file=sys.stderr)
        return 2
    if args.device == "cuda" and not torch.cuda.is_available():
        print("error: --device cuda requested but CUDA is unavailable", file=sys.stderr)
        return 2

    torch.manual_seed(args.seed)
    device = torch.device(args.device)
    x = torch.linspace(-1.0, 1.0, 17, dtype=torch.float64, device=device)
    target = (2.5 * x - 0.7).unsqueeze(-1)

    try:
        import pypose as pp
        from pypose.optim.corrector import FastTriggs
        from pypose.optim.kernel import Huber
        from pypose.optim.solver import Cholesky
        from pypose.optim.strategy import Constant

        model = LineResidual().to(device)
        kernel = Huber(delta=1.0)
        optimizer = pp.optim.LM(
            model,
            solver=Cholesky(),
            strategy=Constant(damping=1e-4),
            kernel=kernel,
            corrector=FastTriggs(kernel),
            vectorize=True,
        )
        jacobian = pp.optim.functional.modjac(
            model, input=x, vectorize=True, flatten=True
        )
        if jacobian.shape != (x.numel(), 2):
            raise AssertionError(f"unexpected Jacobian shape: {jacobian.shape}")

        with torch.no_grad():
            initial = optimizer.model.loss(x, target).item()
        if not torch.isfinite(torch.tensor(initial)):
            raise AssertionError(f"initial loss is not finite: {initial}")

        losses = []
        for _ in range(args.steps):
            loss = optimizer.step(x, target)
            value = float(loss)
            if not torch.isfinite(loss):
                raise AssertionError(f"LM returned a non-finite loss: {value}")
            losses.append(value)
            if value < 1e-18:
                break

        final = losses[-1]
        if not final < initial:
            raise AssertionError(f"loss did not decrease: {initial} -> {final}")
        with torch.no_grad():
            slope = float(model.slope)
            intercept = float(model.intercept)
        if abs(slope - 2.5) > 1e-6 or abs(intercept + 0.7) > 1e-6:
            raise AssertionError(
                f"unexpected fitted parameters: slope={slope:.8f}, "
                f"intercept={intercept:.8f}"
            )
        print(
            f"dense LM smoke passed: pypose={pp.__version__}, device={device}, "
            f"loss={initial:.3e}->{final:.3e}, steps={len(losses)}, "
            f"params=({slope:.6f}, {intercept:.6f})"
        )
        return 0
    except Exception as exc:  # give a concise actionable failure to shell users
        print(f"dense LM smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
