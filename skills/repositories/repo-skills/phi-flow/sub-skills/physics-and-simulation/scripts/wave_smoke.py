#!/usr/bin/env python3
"""Small deterministic wave-equation smoke test for phi.physics.wave.

This helper intentionally uses a much smaller grid and fewer steps than the
source demo. It verifies that grid construction, wave stepping, field math, and
basic finite-value reductions work in the installed package.
"""

from __future__ import annotations

import argparse
import sys

from phi.flow import *  # noqa: F403,F401 - PhiFlow examples use the standard flow import
from phi.physics import wave


def build_initial_field(resolution: int):
    """Create a deterministic Gaussian displacement on a unit square."""
    return CenteredGrid(  # noqa: F405
        lambda x: math.exp(-100 * math.squared_norm(x - 0.5)),  # noqa: F405
        extrapolation.ZERO_GRADIENT,  # noqa: F405
        x=resolution,
        y=resolution,
        bounds=Box(x=1, y=1),  # noqa: F405
    )


def run_wave(resolution: int, steps: int, dt: float, speed: float, scheme: str):
    u = build_initial_field(resolution)
    if scheme == "leapfrog":
        u_prev = u  # start from rest
        for _ in range(steps):
            u, u_prev = wave.step(u, u_prev, c=speed, dt=dt)
        return u
    if scheme == "euler":
        v = CenteredGrid(0, extrapolation.ZERO_GRADIENT, x=resolution, y=resolution, bounds=Box(x=1, y=1))  # noqa: F405
        for _ in range(steps):
            u, v = wave.euler_step(u, v, c=speed, dt=dt)
        return u
    raise ValueError(f"unknown scheme {scheme!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a small phi.physics.wave smoke test.")
    parser.add_argument("--resolution", type=int, default=32, help="Square grid resolution per axis (default: 32).")
    parser.add_argument("--steps", type=int, default=24, help="Number of wave steps (default: 24).")
    parser.add_argument("--dt", type=float, default=0.002, help="Time step size (default: 0.002).")
    parser.add_argument("--speed", type=float, default=1.0, help="Wave speed c (default: 1.0).")
    parser.add_argument("--scheme", choices=("leapfrog", "euler"), default="leapfrog", help="Integrator to smoke-test.")
    args = parser.parse_args(argv)

    if args.resolution <= 1:
        parser.error("--resolution must be greater than 1")
    if args.steps < 0:
        parser.error("--steps must be non-negative")
    if args.dt <= 0:
        parser.error("--dt must be positive")

    u = run_wave(args.resolution, args.steps, args.dt, args.speed, args.scheme)
    finite = bool(math.all(math.is_finite(u.values)))  # noqa: F405
    min_value = float(math.min(u.values))  # noqa: F405
    max_value = float(math.max(u.values))  # noqa: F405
    mean_value = float(math.mean(u.values))  # noqa: F405
    max_abs = float(math.max(math.abs(u.values)))  # noqa: F405
    cfl = abs(args.speed) * args.dt * args.resolution

    print(
        "wave smoke completed: "
        f"scheme={args.scheme}, steps={args.steps}, grid={args.resolution}x{args.resolution}, "
        f"dt={args.dt:g}, c={args.speed:g}, CFL={cfl:.3f}"
    )
    print(f"final field: min={min_value:.6g}, max={max_value:.6g}, mean={mean_value:.6g}, max_abs={max_abs:.6g}")

    if not finite:
        print("ERROR: final wave field contains non-finite values", file=sys.stderr)
        return 2
    if max_abs > 10:
        print("ERROR: final wave field grew beyond the smoke-test safety threshold", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
