#!/usr/bin/env python3
"""Solve the swing-foot polynomial coefficients from the original helper.

This is a safe, non-plotting replacement for `humanoid/utils/calculate_gait.py`.
It solves the same 6x6 linear system and prints the coefficients.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class GaitInputs:
    h0: float
    hswing: float
    v0: float
    vswing: float
    hmax: float
    swing_time: float


def build_system(inputs: GaitInputs) -> Tuple[np.ndarray, np.ndarray]:
    t = float(inputs.swing_time)
    half_t = 0.5 * t
    a = np.array(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            [t**5, t**4, t**3, t**2, t, 1.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [5 * t**4, 4 * t**3, 3 * t**2, 2 * t, 1.0, 0.0],
            [half_t**5, half_t**4, half_t**3, half_t**2, half_t, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        ],
        dtype=float,
    )
    b = np.array([inputs.h0, inputs.hswing, inputs.v0, inputs.vswing, inputs.hmax, 0.0], dtype=float)
    return a, b


def solve_coefficients(inputs: GaitInputs) -> np.ndarray:
    if inputs.swing_time <= 0:
        raise ValueError("swing_time must be positive")
    a, b = build_system(inputs)
    return np.linalg.solve(a, b)


def format_text(inputs: GaitInputs, coeffs: np.ndarray, residuals: np.ndarray) -> str:
    lines = ["Inputs:"]
    for key, value in asdict(inputs).items():
        lines.append(f"  {key} = {value}")
    lines.append("")
    lines.append("Coefficients (a5, a4, a3, a2, a1, a0):")
    for idx, value in enumerate(coeffs):
        lines.append(f"  a{5 - idx} = {value:.15f}")
    lines.append("")
    lines.append("Residuals:")
    lines.append(f"  max_abs = {float(np.max(np.abs(residuals))):.3e}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Solve the gait polynomial coefficients without plotting.")
    parser.add_argument("--h0", type=float, default=0.0, help="Height at t=0")
    parser.add_argument("--hswing", type=float, default=0.0, help="Height at t=swing_time")
    parser.add_argument("--v0", type=float, default=0.0, help="Velocity at t=0")
    parser.add_argument("--vswing", type=float, default=-0.1, help="Velocity at t=swing_time")
    parser.add_argument("--hmax", type=float, default=0.04, help="Height at t=swing_time/2")
    parser.add_argument("--swing-time", type=float, default=0.26, help="Swing duration in seconds")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    args = parser.parse_args(argv)

    inputs = GaitInputs(
        h0=args.h0,
        hswing=args.hswing,
        v0=args.v0,
        vswing=args.vswing,
        hmax=args.hmax,
        swing_time=args.swing_time,
    )
    coeffs = solve_coefficients(inputs)
    a, b = build_system(inputs)
    residuals = a @ coeffs - b

    if args.json:
        print(
            json.dumps(
                {
                    "inputs": asdict(inputs),
                    "coefficients": {
                        "a5": coeffs[0],
                        "a4": coeffs[1],
                        "a3": coeffs[2],
                        "a2": coeffs[3],
                        "a1": coeffs[4],
                        "a0": coeffs[5],
                    },
                    "residual_max_abs": float(np.max(np.abs(residuals))),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(format_text(inputs, coeffs, residuals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
