#!/usr/bin/env python3
"""Tiny Dipy reslice smoke check with JSON output.

The script uses only a synthetic 3D image, performs no downloads, and writes
nothing. It is safe to run from any working directory when Dipy is importable.
"""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic tiny Dipy 3D reslice smoke check."
    )
    parser.add_argument(
        "--shape",
        type=int,
        nargs=3,
        default=(3, 4, 5),
        metavar=("I", "J", "K"),
        help="Input 3D shape for the synthetic volume.",
    )
    parser.add_argument(
        "--zooms",
        type=float,
        nargs=3,
        default=(2.0, 2.0, 3.0),
        metavar=("ZI", "ZJ", "ZK"),
        help="Input voxel sizes.",
    )
    parser.add_argument(
        "--new-zooms",
        type=float,
        nargs=3,
        default=(1.0, 1.0, 1.5),
        metavar=("NZI", "NZJ", "NZK"),
        help="Target voxel sizes.",
    )
    parser.add_argument(
        "--order",
        type=int,
        default=1,
        choices=range(0, 6),
        help="Spline interpolation order, 0 through 5.",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for the JSON summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if any(value <= 0 for value in args.shape):
        raise SystemExit("--shape values must be positive")
    if any(value <= 0 for value in args.zooms):
        raise SystemExit("--zooms values must be positive")
    if any(value <= 0 for value in args.new_zooms):
        raise SystemExit("--new-zooms values must be positive")

    import numpy as np

    from dipy.align.reslice import reslice

    shape = tuple(args.shape)
    zooms = np.asarray(args.zooms, dtype=float)
    new_zooms = np.asarray(args.new_zooms, dtype=float)

    data = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    affine = np.diag([zooms[0], zooms[1], zooms[2], 1.0])

    resliced, new_affine = reslice(
        data,
        affine,
        tuple(zooms),
        tuple(new_zooms),
        order=args.order,
        mode="constant",
        cval=0,
        num_processes=1,
    )

    expected_shape = tuple(
        int(value) for value in np.round(zooms / new_zooms * np.asarray(shape))
    )
    observed_new_zooms = np.abs(np.diag(new_affine)[:3])

    ok = (
        resliced.shape == expected_shape
        and resliced.ndim == 3
        and np.allclose(observed_new_zooms, new_zooms)
        and np.isfinite(resliced).all()
        and float(resliced.max()) <= float(data.max())
        and float(resliced.min()) >= 0.0
    )

    summary = {
        "ok": bool(ok),
        "input_shape": list(shape),
        "output_shape": [int(value) for value in resliced.shape],
        "expected_shape": [int(value) for value in expected_shape],
        "input_zooms": [float(value) for value in zooms],
        "target_zooms": [float(value) for value in new_zooms],
        "observed_affine_diagonal": [float(value) for value in np.diag(new_affine)[:3]],
        "input_min_max": [float(data.min()), float(data.max())],
        "output_min_max": [float(resliced.min()), float(resliced.max())],
        "order": args.order,
    }
    print(json.dumps(summary, indent=args.json_indent, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
