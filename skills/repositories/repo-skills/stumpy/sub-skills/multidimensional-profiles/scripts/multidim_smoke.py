#!/usr/bin/env python3
"""Deterministic smoke runner for multidimensional STUMPY workflows.

The default path uses ``mstump`` on a tiny synthetic 2-D float64 array and prints
shape and dimension-selection facts. Optional flags let you exercise the non-normalized
``maamp`` route, the ``subspace`` routing wrapper, and one-window distance profiles.
"""

from __future__ import annotations

import argparse
from typing import Optional
import warnings

import numpy as np

warnings.filterwarnings(
    "ignore",
    message=r".*where.*without.*out.*",
    category=UserWarning,
)

import stumpy
from stumpy.maamp import maamp_multi_distance_profile
from stumpy.mstump import multi_distance_profile


def build_t() -> np.ndarray:
    """Return a tiny deterministic 2-D float64 array."""

    return np.array(
        [
            [0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 4.0, 5.0, 6.0, 4.0, 5.0, 6.0],
            [6.0, 5.0, 4.0, 6.0, 5.0, 4.0, 1.0, 0.0, -1.0, 1.0, 0.0, -1.0],
        ],
        dtype=np.float64,
    )


def parse_include(values: Optional[list[int]]) -> Optional[np.ndarray]:
    if not values:
        return None
    return np.asarray(values, dtype=np.int64)


def summarize(
    label: str,
    T: np.ndarray,
    m: int,
    include: Optional[np.ndarray],
    discords: bool,
    p: float,
    normalized: bool,
    show_subspace: bool,
    query_idx: int,
) -> None:
    if normalized:
        P, I = stumpy.mstump(T, m, include=include, discords=discords)
        D = multi_distance_profile(query_idx, T, m, include=include, discords=discords)
        mdl_kwargs = {"normalize": True}
        subspace_kwargs = {"normalize": True}
    else:
        P, I = stumpy.maamp(T, m, include=include, discords=discords, p=p)
        D = maamp_multi_distance_profile(
            query_idx, T, m, include=include, discords=discords, p=p
        )
        mdl_kwargs = {"normalize": False, "p": p}
        subspace_kwargs = {"normalize": False, "p": p}

    print(f"[{label}] T.shape={T.shape} dtype={T.dtype} m={m}")
    print(f"[{label}] include={None if include is None else include.tolist()} discords={discords}")
    print(f"[{label}] D.shape={D.shape} query_idx={query_idx}")
    print(f"[{label}] P.shape={P.shape} I.shape={I.shape}")

    row_selector = np.argmax if discords else np.argmin
    motif_idx = row_selector(P, axis=1)
    nn_idx = I[np.arange(P.shape[0]), motif_idx]

    for k in range(P.shape[0]):
        print(
            f"[{label}] row={k} subseq_idx={int(motif_idx[k])} "
            f"nn_idx={int(nn_idx[k])} profile={float(P[k, motif_idx[k]])}"
        )

    mdls, subspaces = stumpy.mdl(
        T,
        m,
        motif_idx,
        nn_idx,
        include=include,
        discords=discords,
        **mdl_kwargs,
    )
    best_k = int(np.argmin(mdls))
    print(f"[{label}] mdls={mdls.tolist()}")
    print(f"[{label}] best_k={best_k} subspace={subspaces[best_k].tolist()}")

    if show_subspace:
        S = stumpy.subspace(
            T,
            m,
            int(motif_idx[best_k]),
            int(nn_idx[best_k]),
            best_k,
            include=include,
            discords=discords,
            **subspace_kwargs,
        )
        print(f"[{label}] direct_subspace={S.tolist()}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny multidimensional STUMPY smoke test.",
    )
    parser.add_argument(
        "--mode",
        choices=("mstump", "maamp", "both"),
        default="mstump",
        help="Which profile family to exercise.",
    )
    parser.add_argument(
        "--m",
        type=int,
        default=3,
        help="Sliding window size (must be at least 3).",
    )
    parser.add_argument(
        "--include",
        type=int,
        nargs="*",
        default=None,
        metavar="IDX",
        help="Optional zero-based dimension indices to force into the search.",
    )
    parser.add_argument(
        "--discords",
        action="store_true",
        help="Reverse the ranking so the most unusual subsequences are selected.",
    )
    parser.add_argument(
        "--subspace",
        action="store_true",
        help="Also print the direct subspace selected by the routing wrapper.",
    )
    parser.add_argument(
        "--p",
        type=float,
        default=2.0,
        help="Minkowski p value for the non-normalized route.",
    )
    parser.add_argument(
        "--query-idx",
        type=int,
        default=0,
        help="Query subsequence index for the one-window distance-profile helper.",
    )
    args = parser.parse_args()

    T = build_t()
    include = parse_include(args.include)

    if args.mode in ("mstump", "both"):
        summarize(
            "mstump",
            T,
            args.m,
            include,
            args.discords,
            args.p,
            True,
            args.subspace,
            args.query_idx,
        )

    if args.mode in ("maamp", "both"):
        summarize(
            "maamp",
            T,
            args.m,
            include,
            args.discords,
            args.p,
            False,
            args.subspace,
            args.query_idx,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
