#!/usr/bin/env python3
"""Deterministic, CPU-only ICP smoke check using synthetic non-degenerate data.

See the nearest ``../SKILL.md`` for the operating contract."""
from __future__ import annotations

import argparse

import torch
import pypose as pp


def run(steps: int) -> None:
    torch.manual_seed(11)
    dtype = torch.float64
    # Asymmetric 3-D cloud avoids the ambiguous planar/collinear case.
    source = torch.tensor(
        [
            [-0.7, -0.4, 0.2],
            [0.2, -0.6, 1.1],
            [1.0, 0.1, -0.3],
            [-0.1, 0.9, 0.7],
            [0.8, 0.7, 1.4],
            [-1.1, 0.5, -0.8],
            [0.4, -1.0, -0.2],
            [1.2, -0.2, 0.5],
        ],
        dtype=dtype,
    ).unsqueeze(0)
    truth = pp.SE3(torch.tensor([0.35, -0.2, 0.12, 0.0, 0.0, 0.0, 1.0], dtype=dtype))
    target = truth.unsqueeze(-2) @ source
    stepper = pp.utils.ReduceToBason(steps=steps, patience=2, tol=1e-12)
    estimate = pp.module.ICP(stepper=stepper)(source, target)
    registered = estimate.unsqueeze(-2) @ source
    residual = (registered - target).norm(dim=-1).mean()

    assert pp.is_SE3(estimate), "ICP did not return an SE3 LieTensor"
    assert torch.isfinite(estimate.tensor()).all(), "ICP pose is not finite"
    assert torch.isfinite(residual), "ICP residual is not finite"
    assert residual < 1e-5, f"ICP synthetic residual too large: {residual.item()}"
    print(f"icp smoke ok: residual={residual.item():.8f}, steps={stepper.steps}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=20, help="maximum ICP iterations")
    args = parser.parse_args()
    if args.steps < 2:
        parser.error("--steps must be at least 2")
    run(args.steps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
