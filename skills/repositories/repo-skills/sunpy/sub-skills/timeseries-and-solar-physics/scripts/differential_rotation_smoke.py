#!/usr/bin/env python3
"""Run a deterministic SunPy differential-rotation calculation."""
from __future__ import annotations

import argparse
import json

import astropy.units as u
from sunpy.sun.models import differential_rotation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute a unit-bearing solar differential-rotation longitude change."
    )
    parser.add_argument(
        "--duration-days",
        type=float,
        default=2.0,
        help="rotation interval in days (default: 2)",
    )
    parser.add_argument(
        "--latitude",
        type=float,
        default=30.0,
        help="heliographic latitude in degrees (default: 30)",
    )
    parser.add_argument(
        "--model",
        choices=("howard", "snodgrass", "allen", "rigid"),
        default="howard",
        help="published rotation model (default: howard)",
    )
    parser.add_argument(
        "--frame-time",
        choices=("sidereal", "synodic"),
        default="sidereal",
        help="frame convention (default: sidereal)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.duration_days < 0:
        raise SystemExit("--duration-days must be non-negative")
    result = differential_rotation(
        args.duration_days * u.day,
        args.latitude * u.deg,
        model=args.model,
        frame_time=args.frame_time,
    )
    if not result.unit.is_equivalent(u.deg):
        raise AssertionError(f"unexpected result unit: {result.unit}")
    print(
        json.dumps(
            {
                "status": "ok",
                "model": args.model,
                "frame_time": args.frame_time,
                "duration_days": args.duration_days,
                "latitude_deg": args.latitude,
                "longitude_change": result.to_value(u.deg),
                "unit": str(result.unit),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
