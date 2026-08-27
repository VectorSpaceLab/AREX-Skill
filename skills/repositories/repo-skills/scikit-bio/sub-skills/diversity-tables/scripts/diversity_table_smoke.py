#!/usr/bin/env python3
"""Deterministic smoke checks for scikit-bio diversity/table APIs."""

from __future__ import annotations

import argparse
import json
from typing import Any


def _round_nested(value: Any, digits: int) -> Any:
    """Round floats inside nested JSON-compatible containers."""
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, list):
        return [_round_nested(item, digits) for item in value]
    if isinstance(value, dict):
        return {key: _round_nested(item, digits) for key, item in value.items()}
    return value


def run_smoke(digits: int = 6) -> dict[str, Any]:
    """Run small deterministic diversity and table checks."""
    import numpy as np
    from skbio import TreeNode
    from skbio.diversity import alpha_diversity, beta_diversity
    from skbio.table import Table, example_table

    counts = np.array(
        [
            [1, 5],
            [2, 3],
            [0, 1],
        ],
        dtype=int,
    )
    sample_ids = ["A", "B", "C"]
    taxa = ["O1", "O2"]
    tree = TreeNode.read(["((O1:0.25,O2:0.50):0.25,O3:0.75)root;"])

    alpha = alpha_diversity("sobs", counts, ids=sample_ids)
    bray = beta_diversity("braycurtis", counts, ids=sample_ids)
    faith = alpha_diversity("faith_pd", counts, ids=sample_ids, taxa=taxa, tree=tree)
    unifrac = beta_diversity(
        "unweighted_unifrac",
        counts,
        ids=sample_ids,
        taxa=taxa,
        tree=tree,
    )

    table = Table(counts.T, observation_ids=taxa, sample_ids=sample_ids)
    table_counts = table.matrix_data.T.toarray()
    table_alpha = alpha_diversity("sobs", table)

    payload = {
        "alpha_sobs": dict(zip(map(str, alpha.index), alpha.astype(int).tolist())),
        "beta_braycurtis_ids": list(bray.ids),
        "beta_braycurtis": bray.data.tolist(),
        "faith_pd": dict(zip(map(str, faith.index), faith.astype(float).tolist())),
        "unweighted_unifrac": unifrac.data.tolist(),
        "table": {
            "sample_ids": list(table.ids()),
            "taxa": list(table.ids(axis="observation")),
            "dense_shape": list(table_counts.shape),
            "dense_counts": table_counts.astype(int).tolist(),
            "alpha_sobs": dict(
                zip(map(str, table_alpha.index), table_alpha.astype(int).tolist())
            ),
        },
        "example_table": {
            "sample_ids": list(example_table.ids()),
            "observation_ids": list(example_table.ids(axis="observation")),
        },
    }
    return _round_nested(payload, digits)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic scikit-bio diversity/table smoke checks and print JSON."
        )
    )
    parser.add_argument(
        "--digits",
        type=int,
        default=6,
        help="decimal places for floating-point values in the JSON output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when required runtime imports or smoke checks fail",
    )
    args = parser.parse_args()
    try:
        payload = {"ok": True, "result": run_smoke(args.digits)}
    except Exception as error:  # noqa: BLE001 - smoke script reports failures as JSON.
        payload = {
            "ok": False,
            "error_type": error.__class__.__name__,
            "error": str(error),
        }
        print(json.dumps(payload, sort_keys=True))
        if args.strict:
            raise SystemExit(1) from error
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
