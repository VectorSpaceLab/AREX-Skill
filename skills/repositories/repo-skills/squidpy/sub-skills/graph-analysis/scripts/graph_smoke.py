#!/usr/bin/env python3
"""Tiny deterministic Squidpy graph/statistics smoke test.

Creates a small AnnData object in memory, builds a spatial neighbor graph, runs
lightweight graph statistics, and prints the keys produced. No downloads or
local source files are required.
"""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-perms", type=int, default=5, help="Permutations for neighborhood enrichment.")
    parser.add_argument("--neighbors", type=int, default=3, help="KNN neighbors for the tiny graph.")
    parser.add_argument("--quiet", action="store_true", help="Only print JSON summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    import anndata as ad
    import numpy as np
    import pandas as pd
    import squidpy as sq

    counts = np.array(
        [
            [1.0, 0.0, 3.0],
            [2.0, 1.0, 0.0],
            [0.0, 3.0, 1.0],
            [4.0, 0.0, 2.0],
            [0.0, 2.0, 4.0],
            [3.0, 1.0, 1.0],
        ],
        dtype=float,
    )
    obs = pd.DataFrame(
        {"cell_type": pd.Categorical(["A", "A", "B", "B", "C", "C"])},
        index=[f"cell{i}" for i in range(6)],
    )
    var = pd.DataFrame(index=["GeneA", "GeneB", "GeneC"])
    adata = ad.AnnData(X=counts, obs=obs, var=var)
    adata.obsm["spatial"] = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [2.0, 0.0],
            [2.0, 1.0],
        ],
        dtype=float,
    )

    sq.gr.spatial_neighbors_knn(adata, n_neighs=args.neighbors, n_jobs=1)
    sq.gr.nhood_enrichment(
        adata,
        cluster_key="cell_type",
        n_perms=args.n_perms,
        seed=0,
        n_jobs=1,
        show_progress_bar=False,
    )
    sq.gr.interaction_matrix(adata, cluster_key="cell_type", normalized=False)
    moran = sq.gr.spatial_autocorr(
        adata,
        genes=["GeneA"],
        mode="moran",
        n_perms=None,
        copy=True,
        n_jobs=1,
        show_progress_bar=False,
    )

    required = [
        "spatial_connectivities",
        "spatial_distances",
    ]
    missing = [key for key in required if key not in adata.obsp]
    if missing:
        raise RuntimeError(f"Missing graph outputs: {missing}")
    if "cell_type_nhood_enrichment" not in adata.uns:
        raise RuntimeError("Missing neighborhood enrichment output")
    if "cell_type_interactions" not in adata.uns:
        raise RuntimeError("Missing interaction matrix output")

    summary = {
        "n_obs": int(adata.n_obs),
        "connectivities_nnz": int(adata.obsp["spatial_connectivities"].nnz),
        "distances_nnz": int(adata.obsp["spatial_distances"].nnz),
        "uns_keys": sorted(str(key) for key in adata.uns.keys()),
        "moran_index": list(map(str, moran.index)),
        "ok": True,
    }

    if not args.quiet:
        print("Squidpy graph smoke completed.")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
