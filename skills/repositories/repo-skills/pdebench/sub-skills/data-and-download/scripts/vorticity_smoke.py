#!/usr/bin/env python3
"""Run a deterministic tiny smoke for PDEBench NumPy/JAX vorticity APIs."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def make_case() -> tuple[np.ndarray, np.ndarray, tuple[float, float, float]]:
    """Create a periodic analytic velocity field and its exact curl."""
    nx, ny, nz, samples = 8, 10, 12, 2
    dx, dy, dz = 1.0 / nx, 1.0 / ny, 1.0 / nz
    x = np.arange(nx, dtype=np.float64) * dx
    y = np.arange(ny, dtype=np.float64) * dy
    z = np.arange(nz, dtype=np.float64) * dz
    xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")

    velocity_one = np.stack(
        [
            np.sin(2 * np.pi * yy) + np.cos(4 * np.pi * zz),
            np.sin(2 * np.pi * zz) + np.cos(4 * np.pi * xx),
            np.sin(2 * np.pi * xx) + np.cos(4 * np.pi * yy),
        ],
        axis=-1,
    )
    expected_one = np.stack(
        [
            -2 * np.pi * np.cos(2 * np.pi * zz)
            - 4 * np.pi * np.sin(4 * np.pi * yy),
            -4 * np.pi * np.sin(4 * np.pi * zz)
            - 2 * np.pi * np.cos(2 * np.pi * xx),
            -4 * np.pi * np.sin(4 * np.pi * xx)
            - 2 * np.pi * np.cos(2 * np.pi * yy),
        ],
        axis=-1,
    )
    velocity = np.broadcast_to(
        velocity_one[None, ...], (samples, nx, ny, nz, 3)
    ).copy()
    expected = np.broadcast_to(
        expected_one[None, ...], (samples, nx, ny, nz, 3)
    ).copy()
    return velocity, expected, (dx, dy, dz)


def _run_numpy(velocity: np.ndarray, expected: np.ndarray, spacing: tuple[float, float, float]) -> float:
    try:
        from pdebench.data_gen.src.vorticity import compute_spectral_vorticity_np
    except ImportError as exc:
        raise ImportError("pdebench NumPy vorticity API is not importable") from exc
    actual = compute_spectral_vorticity_np(velocity, *spacing)
    np.testing.assert_allclose(actual, expected, rtol=2e-5, atol=2e-5)
    return float(np.max(np.abs(actual - expected)))


def _run_jax(velocity: np.ndarray, expected: np.ndarray, spacing: tuple[float, float, float]) -> float:
    try:
        import jax.numpy as jnp
        from pdebench.data_gen.src.vorticity import compute_spectral_vorticity_jnp
    except ImportError as exc:
        raise ImportError("JAX or the public JAX vorticity API is not importable") from exc
    actual = np.asarray(
        compute_spectral_vorticity_jnp(jnp.asarray(velocity), *spacing)
    )
    np.testing.assert_allclose(actual, expected, rtol=4e-4, atol=4e-4)
    return float(np.max(np.abs(actual - expected)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check public PDEBench spectral-vorticity APIs on a deterministic "
            "periodic tiny field; no files or network are used."
        )
    )
    parser.add_argument(
        "--backend",
        choices=("numpy", "jax", "both"),
        default="both",
        help="API(s) to exercise (default: both)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    velocity, expected, spacing = make_case()
    try:
        if args.backend in ("numpy", "both"):
            error = _run_numpy(velocity, expected, spacing)
            print(f"PASS numpy max_abs_error={error:.6g}")
        if args.backend in ("jax", "both"):
            error = _run_jax(velocity, expected, spacing)
            print(f"PASS jax max_abs_error={error:.6g}")
    except (AssertionError, ImportError, ValueError) as exc:
        print(f"ERROR: vorticity smoke failed: {exc}", file=sys.stderr)
        return 2
    print("PASS deterministic periodic [2,8,10,12,3] vorticity case")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
