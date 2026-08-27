#!/usr/bin/env python3
"""Tiny differentiable throw optimization smoke test for PhiFlow.

The helper runs a small gradient-descent loop on the classic throw example
across installed backends that support Jacobians.
"""

from __future__ import annotations

import argparse
import sys

import phi
from phi import math
from phiml.backend import Backend


def simulate_hit(pos, height, vel, angle, gravity=1.):
    vel_x, vel_y = math.cos(angle) * vel, math.sin(angle) * vel
    height = math.maximum(height, .5)
    hit_time = (vel_y + math.sqrt(vel_y**2 + 2 * gravity * height)) / gravity
    return pos + vel_x * hit_time, hit_time, height, vel_x, vel_y


def optimize_backend(backend, iterations: int, step_size: float) -> float:
    def loss_function(vel):
        return math.l2_loss(simulate_hit(10, 1, vel, 0)[0] - 0)

    gradient = math.functional_gradient(loss_function)
    vel = 1.0
    with backend:
        for step in range(iterations):
            loss, (grad,) = gradient(vel)
            vel = vel - step_size * grad
            print(f"backend={backend.name} step={step:02d} loss={float(loss):.6g} vel={float(vel):.6g}")
        math.assert_close(-7.022265, vel, abs_tolerance=1e-3)
    return float(vel)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny PhiFlow throw-gradient smoke test.")
    parser.add_argument("--iterations", type=int, default=10, help="Gradient-descent steps per backend (default: 10).")
    parser.add_argument("--step-size", type=float, default=0.2, help="Update step size (default: 0.2).")
    args = parser.parse_args(argv)

    if args.iterations <= 0:
        parser.error("--iterations must be positive")
    if args.step_size <= 0:
        parser.error("--step-size must be positive")

    backends = [backend for backend in phi.detect_backends() if backend.supports(Backend.jacobian)]
    if not backends:
        print("ERROR: no detected backend supports Jacobians", file=sys.stderr)
        return 2

    with math.precision(64):
        final_velocities = [optimize_backend(backend, args.iterations, args.step_size) for backend in backends]

    print("final velocities: " + ", ".join(f"{value:.6f}" for value in final_velocities))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
