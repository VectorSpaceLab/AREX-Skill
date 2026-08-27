#!/usr/bin/env python3
"""Tiny NumPy ART preprocessing smoke.

This script uses synthetic arrays only. It verifies StandardisationMeanStd and
SpatialSmoothing behavior for channel-last data by default, with an optional
channel-first branch.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)

if (Path.cwd() / "art" / "__init__.py").exists():
    sys.path.insert(0, str(Path.cwd()))


def make_data(channels_first: bool) -> np.ndarray:
    base = np.array(
        [
            [0.00, 0.20, 0.40, 0.60],
            [0.10, 0.30, 0.50, 0.70],
            [0.20, 0.40, 0.60, 0.80],
            [0.30, 0.50, 0.70, 1.00],
        ],
        dtype=np.float32,
    )
    if channels_first:
        return base.reshape(1, 1, 4, 4)
    return base.reshape(1, 4, 4, 1)


def run_smoke(channels_first: bool) -> dict[str, float | str | bool]:
    from art.defences.preprocessor import SpatialSmoothing
    from art.preprocessing.standardisation_mean_std.numpy import StandardisationMeanStd

    x = make_data(channels_first)
    y = np.array([[1.0, 0.0]], dtype=np.float32)

    standard = StandardisationMeanStd(mean=np.array([0.5], dtype=np.float32), std=np.array([0.25], dtype=np.float32))
    x_standard, y_standard = standard(x, y)
    grad = np.ones_like(x, dtype=np.float32)
    grad_back = standard.estimate_gradient(x, grad)

    assert x_standard.shape == x.shape
    assert y_standard is y
    assert np.isfinite(x_standard).all()
    assert np.allclose(grad_back, np.full_like(x, 4.0), atol=1e-6)

    smoother = SpatialSmoothing(
        window_size=3,
        channels_first=channels_first,
        clip_values=(0.0, 1.0),
        apply_fit=False,
        apply_predict=True,
    )
    x_smooth, y_smooth = smoother(x, y)

    assert x_smooth.shape == x.shape
    assert y_smooth is y
    assert np.isfinite(x_smooth).all()
    assert float(x_smooth.min()) >= -1e-6
    assert float(x_smooth.max()) <= 1.0 + 1e-6

    changed = float(np.mean(np.abs(x_smooth - x)))
    assert changed >= 0.0

    return {
        "channels_first": channels_first,
        "input_shape": "x".join(map(str, x.shape)),
        "standard_min": float(x_standard.min()),
        "standard_max": float(x_standard.max()),
        "smooth_mean_abs_delta": changed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tiny ART NumPy preprocessing smokes on synthetic image data.")
    parser.add_argument(
        "--channels-first",
        action="store_true",
        help="Use NCHW data and SpatialSmoothing(channels_first=True); default uses NHWC.",
    )
    args = parser.parse_args()

    result = run_smoke(args.channels_first)
    print("ART NumPy preprocessor smoke passed")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
