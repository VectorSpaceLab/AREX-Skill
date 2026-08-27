#!/usr/bin/env python3
"""No-network smoke check for STUMPY motif matching and FLUSS segmentation.

The script builds a tiny deterministic series, computes a matrix profile, and
then runs either motif/query matching, FLUSS segmentation, or both. Imports of
NumPy/STUMPY are delayed until after argument parsing so that ``--help`` works
without a prepared runtime environment.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute a tiny synthetic STUMPY profile and run motif/match or "
            "FLUSS validation facts. No network or repository checkout data is used."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=("motif", "fluss", "both"),
        default="both",
        help="Which downstream analysis to run after computing the profile.",
    )
    parser.add_argument(
        "--m",
        type=int,
        default=4,
        help="Matrix-profile and query window size.",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=0.1,
        help="Distance threshold for motif and query-match outputs.",
    )
    parser.add_argument(
        "--max-matches",
        type=int,
        default=3,
        help="Maximum matches returned by motif and query-match calls.",
    )
    parser.add_argument(
        "--query-start",
        type=int,
        default=0,
        help="Start index of the synthetic query subsequence.",
    )
    parser.add_argument(
        "--L",
        type=int,
        default=4,
        help="FLUSS arc-curve subsequence/period length.",
    )
    parser.add_argument(
        "--n-regimes",
        type=int,
        default=2,
        help="FLUSS regime count; boundaries are n_regimes - 1.",
    )
    parser.add_argument(
        "--excl-factor",
        type=int,
        default=1,
        help="FLUSS regime exclusion factor.",
    )
    parser.add_argument(
        "--distance-mode",
        choices=("normalized", "non-normalized"),
        default="normalized",
        help="Use stumpy.stump for normalized distances or stumpy.aamp for absolute distances.",
    )
    parser.add_argument(
        "--p",
        type=float,
        default=2.0,
        help="Minkowski p-norm for non-normalized routing; ignored when normalized.",
    )
    return parser


def _synthetic_series(np):
    """Return one repeated motif followed by a different repeated motif."""
    motif_a = np.array([0.0, 1.0, 0.0, -1.0], dtype=np.float64)
    motif_b = np.array([0.0, -1.0, 0.0, 1.0], dtype=np.float64)
    return np.concatenate([motif_a, motif_a, motif_a, motif_b, motif_b, motif_b])


def _json_number_table(array, np):
    arr = np.asarray(array)
    if arr.size == 0:
        return []
    rows = []
    for row in arr:
        rows.append([float(row[0]), int(row[1])])
    return rows


def run(args: argparse.Namespace) -> int:
    try:
        import numpy as np
        import stumpy
    except Exception as exc:  # pragma: no cover - environment diagnostic only
        raise SystemExit(f"Unable to import numpy/stumpy for smoke execution: {exc}")

    if args.m < 3:
        raise SystemExit("--m must be at least 3 for this synthetic smoke series")
    if args.L < 1:
        raise SystemExit("--L must be positive")
    if args.n_regimes < 2:
        raise SystemExit("--n-regimes must be at least 2")
    if args.excl_factor < 0:
        raise SystemExit("--excl-factor must be non-negative")

    T = _synthetic_series(np)
    if args.query_start < 0 or args.query_start + args.m > T.shape[0]:
        raise SystemExit("--query-start must allow a full query window inside the synthetic series")

    normalize = args.distance_mode == "normalized"
    if normalize:
        mp = stumpy.stump(T, args.m)
        backend = "stump"
    else:
        mp = stumpy.aamp(T, args.m, p=args.p)
        backend = "aamp"

    P = mp[:, 0].astype(np.float64)
    I = mp[:, 1].astype(np.int64)
    min_idx = int(np.nanargmin(P))
    max_idx = int(np.nanargmax(P))

    print(f"mode={args.mode}")
    print(f"backend={backend}")
    print(f"distance_mode={args.distance_mode}")
    print(f"normalize={normalize}")
    print(f"p={args.p}")
    print(f"series_len={T.shape[0]}")
    print(f"window_m={args.m}")
    print(f"profile_len={P.shape[0]}")
    print(f"profile_min={float(P[min_idx]):.6f} at={min_idx}")
    print(f"profile_max={float(P[max_idx]):.6f} at={max_idx}")

    if args.mode in {"motif", "both"}:
        motif_distances, motif_indices = stumpy.motifs(
            T,
            P,
            min_neighbors=1,
            max_distance=args.max_distance,
            cutoff=np.inf,
            max_matches=args.max_matches,
            max_motifs=1,
            normalize=normalize,
            p=args.p,
        )
        query = T[args.query_start : args.query_start + args.m]
        query_matches = stumpy.match(
            query,
            T,
            max_distance=args.max_distance,
            max_matches=args.max_matches,
            query_idx=args.query_start,
            normalize=normalize,
            p=args.p,
        )
        print("motif_distances=" + json.dumps(np.round(motif_distances, 6).tolist()))
        print("motif_indices=" + json.dumps(motif_indices.tolist()))
        print("query_matches=" + json.dumps(_json_number_table(query_matches, np)))
        print(f"query_start={args.query_start}")

    if args.mode in {"fluss", "both"}:
        cac, regime_locations = stumpy.fluss(
            I,
            L=args.L,
            n_regimes=args.n_regimes,
            excl_factor=args.excl_factor,
        )
        cac_summary = {
            "len": int(cac.shape[0]),
            "min": round(float(np.nanmin(cac)), 6),
            "max": round(float(np.nanmax(cac)), 6),
        }
        print("fluss_cac=" + json.dumps(cac_summary, sort_keys=True))
        print("fluss_regime_locations=" + json.dumps(np.asarray(regime_locations, dtype=int).tolist()))

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
