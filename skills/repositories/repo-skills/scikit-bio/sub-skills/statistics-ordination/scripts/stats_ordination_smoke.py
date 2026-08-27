#!/usr/bin/env python3
"""Deterministic smoke checks for scikit-bio statistics/ordination APIs."""

from __future__ import annotations

import argparse
import json
from typing import Any


def _json_ready(value: Any, digits: int) -> Any:
    """Convert common scientific Python values to compact JSON-safe objects."""
    try:
        import numpy as np
    except ImportError:  # pragma: no cover - handled by main smoke failure path.
        np = None

    if np is not None:
        if isinstance(value, np.generic):
            return _json_ready(value.item(), digits)
        if isinstance(value, np.ndarray):
            return _json_ready(value.tolist(), digits)

    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, dict):
        return {str(key): _json_ready(item, digits) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item, digits) for item in value]
    return value


def _series_to_dict(series: Any, digits: int) -> dict[str, Any]:
    """Convert a pandas Series-like result to a JSON-safe dictionary."""
    return {str(key): _json_ready(value, digits) for key, value in series.items()}


def run_smoke(permutations: int = 9, seed: int = 42, digits: int = 6) -> dict[str, Any]:
    """Run deterministic statistics, ordination, composition, and embedding checks."""
    import numpy as np
    from skbio import DistanceMatrix
    from skbio.embedding import (
        ProteinVector,
        embed_vec_to_dataframe,
        embed_vec_to_distances,
        embed_vec_to_ordination,
    )
    from skbio.stats.composition import closure, clr, multi_replace
    from skbio.stats.distance import permanova
    from skbio.stats.ordination import pcoa

    dm = DistanceMatrix(
        np.array(
            [
                [0.0, 0.25, 0.80, 0.75],
                [0.25, 0.0, 0.76, 0.70],
                [0.80, 0.76, 0.0, 0.18],
                [0.75, 0.70, 0.18, 0.0],
            ],
            dtype=float,
        ),
        ids=["s1", "s2", "s3", "s4"],
    )
    grouping = ["control", "control", "treated", "treated"]
    permanova_result = permanova(
        dm,
        grouping,
        permutations=permutations,
        seed=seed,
    )
    ordination = pcoa(dm, dimensions=2, warn_neg_eigval=False)

    counts = np.array(
        [
            [10.0, 0.0, 5.0],
            [4.0, 2.0, 0.0],
            [0.0, 3.0, 9.0],
        ]
    )
    composition = closure(counts)
    positive = multi_replace(composition)
    clr_coordinates = clr(positive)

    vectors = [
        ProteinVector(np.array([0.10, 0.20, 0.30]), "ACDE"),
        ProteinVector(np.array([0.20, 0.10, 0.40]), "ACDF"),
        ProteinVector(np.array([0.85, 0.75, 0.65]), "WYVR"),
    ]
    embedding_frame = embed_vec_to_dataframe(vectors)
    embedding_dm = embed_vec_to_distances(vectors)
    embedding_ord = embed_vec_to_ordination(vectors)

    payload = {
        "distance_matrix": {
            "ids": list(dm.ids),
            "shape": list(dm.shape),
            "condensed": dm.condensed_form().tolist(),
        },
        "permanova": _series_to_dict(permanova_result, digits),
        "pcoa": {
            "method": ordination.short_method_name,
            "sample_ids": list(ordination.samples.index.astype(str)),
            "samples": ordination.samples.to_numpy().tolist(),
            "proportion_explained": ordination.proportion_explained.tolist(),
        },
        "composition": {
            "closed_row_sums": composition.sum(axis=1).tolist(),
            "zero_count_before_replace": int((composition == 0).sum()),
            "min_after_replace": float(positive.min()),
            "clr": clr_coordinates.tolist(),
        },
        "embedding": {
            "frame_index": list(embedding_frame.index.astype(str)),
            "frame_shape": list(embedding_frame.shape),
            "distance_ids": list(embedding_dm.ids),
            "distance_matrix": embedding_dm.data.tolist(),
            "ordination_method": embedding_ord.short_method_name,
            "ordination_sample_ids": list(embedding_ord.samples.index.astype(str)),
        },
    }
    return _json_ready(payload, digits)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic scikit-bio statistics/ordination smoke checks and "
            "print compact JSON."
        )
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=9,
        help="number of permutations for the PERMANOVA smoke check",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed used for permutation-based smoke checks",
    )
    parser.add_argument(
        "--digits",
        type=int,
        default=6,
        help="decimal places for floating-point values in JSON output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when imports or smoke checks fail",
    )
    args = parser.parse_args()

    try:
        payload = {
            "ok": True,
            "result": run_smoke(args.permutations, args.seed, args.digits),
        }
    except (ImportError, ValueError, TypeError) as error:
        payload = {
            "ok": False,
            "error_type": error.__class__.__name__,
            "error": str(error),
        }
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        if args.strict:
            raise SystemExit(1) from error
    except Exception as error:  # noqa: BLE001 - smoke script reports failures as JSON.
        payload = {
            "ok": False,
            "error_type": error.__class__.__name__,
            "error": str(error),
        }
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
        if args.strict:
            raise SystemExit(1) from error
    else:
        print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
