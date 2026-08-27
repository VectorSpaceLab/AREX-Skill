#!/usr/bin/env python3
"""Run a deterministic, CPU-only smoke test for selected pure-Python SLiM maps.

The script only constructs small tensors, checks map dimensions, and runs one
backward pass. It never downloads data, trains a model, compiles extensions,
or writes files. Run ``python maps_smoke.py --help`` for usage and
``python maps_smoke.py --run`` for the check.
"""

from __future__ import annotations

import argparse
import math
import sys


# These cases deliberately avoid the optional native butterfly backend.
CASES = (
    ("linear", 3, 5, False, {}),
    ("identity", 3, 5, False, {}),
    ("nneg", 3, 5, False, {}),
    ("psd", 4, 4, False, {}),
    # OrthogonalLinear in this release adds self.bias unconditionally.
    ("orthogonal", 4, 4, True, {}),
    ("spectral", 3, 5, False, {"sigma_min": 0.1, "sigma_max": 1.0}),
    ("rstochastic", 3, 5, False, {}),
    ("softSVD", 3, 5, False, {}),
    ("split", 3, 5, False, {}),
    ("trivial_nullspace", 3, 5, False, {}),
)


def run() -> int:
    """Construct the selected maps and verify shape and autograd contracts."""
    try:
        import torch
        import neuromancer.slim as slim
    except Exception as exc:  # pragma: no cover - depends on the target env
        print(f"cannot import the CPU NeuroMANCER runtime: {exc}", file=sys.stderr)
        return 2

    torch.manual_seed(0)
    for key, insize, outsize, bias, kwargs in CASES:
        if key not in slim.maps:
            print(f"missing expected registry key: {key}", file=sys.stderr)
            return 1
        map_cls = slim.maps[key]
        layer = map_cls(insize, outsize, bias=bias, **kwargs)
        x = torch.randn(4, insize, requires_grad=True)
        y = layer(x)
        effective = layer.effective_W()
        if tuple(y.shape) != (4, outsize):
            raise AssertionError(f"{key}: output shape {tuple(y.shape)}")
        if tuple(effective.shape) != (insize, outsize):
            raise AssertionError(f"{key}: effective_W shape {tuple(effective.shape)}")
        regularizer = layer.reg_error()
        if not torch.isfinite(y).all() or not torch.isfinite(effective).all():
            raise AssertionError(f"{key}: non-finite forward result")
        if not torch.isfinite(regularizer).all():
            raise AssertionError(f"{key}: non-finite regularization result")
        objective = y.square().mean() + regularizer
        objective.backward()
        if x.grad is None or not torch.isfinite(x.grad).all():
            raise AssertionError(f"{key}: missing or non-finite input gradient")
        print(f"ok {key:18s} input=({4}, {insize}) output=({4}, {outsize})")

    print(f"passed {len(CASES)} pure-Python map checks")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and optionally execute the smoke test."""
    parser = argparse.ArgumentParser(
        description=(
            "CPU-only shape/autograd smoke for selected NeuroMANCER SLiM maps; "
            "no network, training, downloads, or native compilation."
        )
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="construct the selected maps and run the checks",
    )
    args = parser.parse_args(argv)
    if not args.run:
        parser.print_help()
        return 0
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
