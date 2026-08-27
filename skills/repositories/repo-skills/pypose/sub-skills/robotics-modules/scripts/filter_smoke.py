#!/usr/bin/env python3
"""Deterministic, CPU-only smoke check for PyPose EKF/UKF/PF.

This intentionally uses only a synthetic model and no plotting, downloads, or
output files. It can be launched from any working directory. See the nearest
``../SKILL.md`` for the operating contract."""
from __future__ import annotations

import argparse

import torch
import pypose as pp


class ConstantVelocity(pp.module.NLS):
    """Small smooth model with state [position, velocity] and one input."""

    def state_transition(self, state: torch.Tensor, input: torch.Tensor, t=None):
        dt = state.new_tensor(0.1)
        force = input[..., 0]
        position = state[..., 0] + dt * state[..., 1]
        velocity = 0.99 * state[..., 1] + 0.05 * force
        return torch.stack((position, velocity), dim=-1)

    def observation(self, state: torch.Tensor, input: torch.Tensor, t=None):
        # Observe both state coordinates so the three filters share one R.
        return state


def run(particles: int) -> None:
    torch.manual_seed(7)
    dtype = torch.float64
    n = 2
    q = torch.diag(torch.tensor([2e-3, 2e-3], dtype=dtype))
    r = torch.diag(torch.tensor([3e-2, 3e-2], dtype=dtype))
    initial_p = torch.eye(n, dtype=dtype) * 0.25
    control = torch.tensor([0.2], dtype=dtype)

    results = {}
    for name, factory in (
        ("EKF", lambda model: pp.module.EKF(model, q, r)),
        ("UKF", lambda model: pp.module.UKF(model, q, r)),
        ("PF", lambda model: pp.module.PF(model, q, r, particles=particles)),
    ):
        model = ConstantVelocity().to(dtype=dtype)
        estimator = factory(model).to(dtype=dtype)
        x = torch.tensor([1.0, -0.4], dtype=dtype)
        truth = x.clone()
        covariance = initial_p.clone()
        initial_error = None
        final_error = None
        for _ in range(5):
            truth, measurement = model(truth, control)
            # Keep the fixture deterministic while exercising measurement noise.
            measurement = measurement + torch.tensor([0.01, -0.01], dtype=dtype)
            x, covariance = estimator(x, measurement, control, covariance)
            error = (x - truth).norm()
            initial_error = error if initial_error is None else initial_error
            final_error = error
            assert torch.isfinite(x).all(), f"{name} state is not finite"
            assert torch.isfinite(covariance).all(), f"{name} covariance is not finite"
            assert covariance.shape == (n, n), f"{name} covariance shape {covariance.shape}"
            assert torch.allclose(covariance, covariance.mT, atol=2e-8, rtol=2e-6), (
                f"{name} covariance is not symmetric: {covariance}"
            )
        # The fixture is informative rather than a strict monotonic convergence test.
        assert final_error < 0.5, f"{name} did not remain bounded: {final_error}"
        results[name] = float(final_error)

    print("filter smoke ok:", ", ".join(f"{k}={v:.6f}" for k, v in results.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--particles", type=int, default=128, help="PF particle count for the smoke check"
    )
    args = parser.parse_args()
    if args.particles < 8:
        parser.error("--particles must be at least 8")
    run(args.particles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
