#!/usr/bin/env python3
"""Synthetic smoke for 1-D STUMPY matrix profiles and distance profiles."""

from __future__ import annotations

import argparse
from importlib import metadata

import numpy as np
import stumpy

DEFAULT_WINDOW = 3
DEFAULT_T = np.array([0.0, 2.0, -1.0, 3.0, 1.0, 5.0, -2.0, 4.0], dtype=np.float64)
DEFAULT_T_B = np.array([1.0, -1.0, 2.0, 0.5, 3.5, -0.5, 4.5, 1.5], dtype=np.float64)


def _package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def _print_header(args: argparse.Namespace) -> None:
    print(f"stumpy_distribution={_package_version('stumpy')}")
    print(f"numpy={np.__version__}")
    normalize_display = "ignored" if args.mode == "aamp" else args.normalize
    print(
        "mode={mode} window={window} normalize={normalize} p={p} k={k}".format(
            mode=args.mode,
            window=args.window,
            normalize=normalize_display,
            p=args.p,
            k=args.k,
        )
    )


def _summarize_mparray(label: str, mp) -> None:
    profile = np.asarray(mp.P_, dtype=np.float64)
    indices = np.asarray(mp.I_)
    left_i = np.asarray(mp.left_I_)
    right_i = np.asarray(mp.right_I_)

    print(f"{label}.type={type(mp).__name__}")
    print(f"{label}.shape={mp.shape} dtype={mp.dtype}")
    print(f"{label}.P_.shape={profile.shape} finite={bool(np.isfinite(profile).all())}")
    print(
        f"{label}.I_.shape={indices.shape} left_I_.shape={left_i.shape} right_I_.shape={right_i.shape}"
    )
    print(
        f"{label}.left_neg_count={int(np.count_nonzero(left_i < 0))} "
        f"right_neg_count={int(np.count_nonzero(right_i < 0))}"
    )
    print(f"{label}.first_row={np.asarray(mp[0]).tolist()}")


def _summarize_distance_profile(label: str, profile) -> None:
    distances = np.asarray(profile, dtype=np.float64)
    print(f"{label}.shape={distances.shape} dtype={distances.dtype}")
    print(f"{label}.finite={bool(np.isfinite(distances).all())}")
    print(f"{label}={distances.tolist()}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny STUMPY 1-D matrix-profile or distance-profile smoke."
    )
    parser.add_argument(
        "--mode",
        choices=("exact", "aamp", "ab-join", "mass"),
        default="exact",
        help="Smoke mode to run. Default: exact.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW,
        help=f"Subsequence window size. Default: {DEFAULT_WINDOW}.",
    )
    parser.add_argument(
        "--p",
        type=float,
        default=2.0,
        help="Minkowski p-norm for raw-distance modes. Default: 2.0.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=1,
        help="Top-k profile width for stump/aamp. Default: 1.",
    )
    normalize_group = parser.add_mutually_exclusive_group()
    normalize_group.add_argument(
        "--normalize",
        dest="normalize",
        action="store_true",
        help="Use the normalized path where supported.",
    )
    normalize_group.add_argument(
        "--no-normalize",
        dest="normalize",
        action="store_false",
        help="Use the raw-distance path where supported.",
    )
    parser.set_defaults(normalize=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _print_header(args)

    if args.window < DEFAULT_WINDOW:
        raise SystemExit(f"window must be at least {DEFAULT_WINDOW}")
    if args.window >= DEFAULT_T.shape[0]:
        raise SystemExit(f"window must be smaller than {DEFAULT_T.shape[0]}")

    T = DEFAULT_T.copy()
    T_B = DEFAULT_T_B.copy()

    if args.mode == "exact":
        mp = stumpy.stump(T, m=args.window, normalize=args.normalize, k=args.k)
        _summarize_mparray("stump", mp)
    elif args.mode == "aamp":
        mp = stumpy.aamp(T, m=args.window, p=args.p, k=args.k)
        _summarize_mparray("aamp", mp)
    elif args.mode == "ab-join":
        mp = stumpy.stump(
            T,
            m=args.window,
            T_B=T_B,
            ignore_trivial=False,
            normalize=args.normalize,
            k=args.k,
        )
        _summarize_mparray("ab_join", mp)
    elif args.mode == "mass":
        Q = T[: args.window].copy()
        profile = stumpy.mass(Q, T, normalize=args.normalize, p=args.p, query_idx=0)
        _summarize_distance_profile("mass", profile)
    else:  # pragma: no cover
        raise SystemExit(f"unknown mode: {args.mode}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
