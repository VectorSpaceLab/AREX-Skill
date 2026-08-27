#!/usr/bin/env python3
"""Tiny, deterministic STUMPY smoke workflows for approximate/streaming/pan APIs.

No network or file I/O is performed. Imports of numpy/stumpy happen after
argument parsing so that --help remains usable even before STUMPY is installed.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


def percentage(text: str) -> float:
    value = float(text)
    if not 0.0 < value <= 1.0:
        raise argparse.ArgumentTypeError("must satisfy 0.0 < percentage <= 1.0")
    return value


def import_runtime() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        import stumpy
        from stumpy import rng
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise SystemExit(f"Unable to import numpy/stumpy runtime: {exc}") from exc
    return np, stumpy, rng


def fmt(np: Any, value: Any) -> str:
    return np.array2string(np.asarray(value), precision=3, suppress_small=True)


def tiny_series(np: Any) -> Any:
    return np.array([0.0, 1.0, 2.0, 1.0, 0.0, 1.0, 2.0, 1.0, 0.0, 1.0], dtype=np.float64)


def run_scrump(args: argparse.Namespace) -> int:
    np, stumpy, rng = import_runtime()
    T = tiny_series(np)
    with rng.fix_state():
        if args.non_normalized:
            approx = stumpy.scraamp(
                T,
                args.m,
                percentage=args.percentage,
                pre_scraamp=args.pre,
                p=2.0,
            )
            label = "scraamp"
        else:
            approx = stumpy.scrump(
                T,
                args.m,
                percentage=args.percentage,
                pre_scrump=args.pre,
            )
            label = "scrump"
        for _ in range(args.updates):
            approx.update()

    print(f"workflow={label} updates={args.updates} percentage_per_update={args.percentage} pre={args.pre}")
    print(f"T_length={T.shape[0]} m={args.m}")
    print(f"P_={fmt(np, approx.P_)}")
    print(f"I_={fmt(np, approx.I_)}")
    print(f"left_I_={fmt(np, approx.left_I_)}")
    print(f"right_I_={fmt(np, approx.right_I_)}")
    print(f"finite_P_count={int(np.isfinite(approx.P_).sum())}")
    return 0


def run_stumpi(args: argparse.Namespace) -> int:
    np, stumpy, _rng = import_runtime()
    T = tiny_series(np)[:8]
    incoming = np.array([2.0, 1.0, 0.0, 1.0], dtype=np.float64)
    egress = not args.no_egress
    if args.non_normalized:
        stream = stumpy.aampi(T, args.m, egress=egress, p=2.0)
        label = "aampi"
    else:
        stream = stumpy.stumpi(T, args.m, egress=egress)
        label = "stumpi"
    for t in incoming[: args.updates]:
        stream.update(float(t))

    print(f"workflow={label} updates={min(args.updates, incoming.shape[0])} egress={egress}")
    print(f"T_length={stream.T_.shape[0]} m={args.m}")
    print(f"T_={fmt(np, stream.T_)}")
    print(f"P_={fmt(np, stream.P_)}")
    print(f"I_={fmt(np, stream.I_)}")
    print(f"left_I_={fmt(np, stream.left_I_)}")
    return 0


def run_stimp(args: argparse.Namespace) -> int:
    np, stumpy, rng = import_runtime()
    T = tiny_series(np)
    with rng.fix_state():
        if args.non_normalized:
            pan = stumpy.aamp_stimp(
                T,
                min_m=args.min_m,
                max_m=args.max_m,
                step=args.step,
                percentage=args.percentage,
                pre_scraamp=args.pre,
                p=2.0,
            )
            label = "aamp_stimp"
        else:
            pan = stumpy.stimp(
                T,
                min_m=args.min_m,
                max_m=args.max_m,
                step=args.step,
                percentage=args.percentage,
                pre_scrump=args.pre,
            )
            label = "stimp"
        for _ in range(min(args.updates, len(pan.M_))):
            pan.update()

    raw_profiles = [np.asarray(p) for p in pan.P_]
    processed = sum(bool(np.isfinite(p).any()) for p in raw_profiles)
    transformed = np.asarray(pan.PAN_)
    print(f"workflow={label} updates={min(args.updates, len(pan.M_))} percentage_per_row={args.percentage} pre={args.pre}")
    print(f"M_={pan.M_.tolist()} min_m={args.min_m} max_m={args.max_m} step={args.step}")
    print(f"raw_profile_lengths={[int(p.shape[0]) for p in raw_profiles]}")
    print(f"processed_rows_with_finite_values={processed}")
    print(f"PAN_shape={list(transformed.shape)}")
    print(f"PAN_first_row={fmt(np, transformed[0])}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny no-network STUMPY approximate, streaming, or pan smoke workflows."
    )
    parser.add_argument("--workflow", choices=("scrump", "stumpi", "stimp"), default="scrump")
    parser.add_argument("--updates", type=positive_int, default=2, help="number of update calls to run")
    parser.add_argument("--m", type=positive_int, default=3, help="matrix-profile window size for scrump/stumpi")
    parser.add_argument("--percentage", type=percentage, default=0.5, help="anytime work fraction per update/row")
    parser.add_argument("--pre", action="store_true", help="enable pre_scrump/pre_scraamp seeding")
    parser.add_argument("--non-normalized", action="store_true", help="use scraamp/aampi/aamp_stimp counterparts")
    parser.add_argument("--no-egress", action="store_true", help="for stumpi/aampi, grow history instead of sliding")
    parser.add_argument("--min-m", type=positive_int, default=3, help="minimum pan window size")
    parser.add_argument("--max-m", type=positive_int, default=5, help="maximum pan window size")
    parser.add_argument("--step", type=positive_int, default=1, help="pan window-size step")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.workflow == "scrump":
            return run_scrump(args)
        if args.workflow == "stumpi":
            return run_stumpi(args)
        if args.workflow == "stimp":
            return run_stimp(args)
    except Exception as exc:
        print(f"workflow failed: {exc}", file=sys.stderr)
        return 2
    parser.error(f"unknown workflow: {args.workflow}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
