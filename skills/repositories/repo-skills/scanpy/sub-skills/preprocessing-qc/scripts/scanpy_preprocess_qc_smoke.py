#!/usr/bin/env python
"""Run a tiny self-contained Scanpy preprocessing/QC smoke check and print JSON."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from typing import Any


def build_fixture() -> Any:
    import numpy as np
    import pandas as pd
    from anndata import AnnData

    counts = np.array(
        [
            [4, 0, 1, 0, 3, 0],
            [0, 2, 0, 5, 1, 0],
            [3, 1, 0, 0, 2, 1],
            [0, 0, 6, 1, 0, 2],
            [2, 1, 0, 2, 3, 0],
            [0, 3, 2, 0, 1, 4],
        ],
        dtype=np.float32,
    )
    adata = AnnData(counts)
    adata.obs_names = [f"cell{i}" for i in range(adata.n_obs)]
    adata.var_names = ["MT-gene0", "gene1", "gene2", "gene3", "gene4", "gene5"]
    adata.obs["batch"] = pd.Categorical(["a", "a", "a", "b", "b", "b"])
    adata.var["mito"] = adata.var_names.str.startswith("MT-")
    adata.layers["counts"] = adata.X.copy()
    return adata


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_filter_smoke(args: argparse.Namespace) -> dict[str, Any]:
    import scanpy as sc

    adata = build_fixture()
    sc.pp.calculate_qc_metrics(
        adata,
        qc_vars=["mito"],
        percent_top=(1, 2),
        layer="counts",
        inplace=True,
    )
    cell_mask, cell_counts = sc.pp.filter_cells(adata, min_counts=1, inplace=False)
    gene_mask, gene_cells = sc.pp.filter_genes(adata, min_cells=1, inplace=False)
    assert_true(bool(cell_mask.all()), "all fixture cells should pass min_counts=1")
    assert_true(bool(gene_mask.all()), "all fixture genes should pass min_cells=1")

    sc.pp.filter_cells(adata, min_counts=1)
    sc.pp.filter_genes(adata, min_cells=1)
    sc.pp.sample(adata, n=min(args.sample_n, adata.n_obs), rng=args.rng)

    return {
        "mode": "filter-sample",
        "filtered_shape": list(adata.shape),
        "mask_cells_passed": int(cell_mask.sum()),
        "mask_genes_passed": int(gene_mask.sum()),
        "min_cell_counts_preview": float(cell_counts.min()),
        "min_gene_cells_preview": float(gene_cells.min()),
    }


def run_preprocess_smoke(args: argparse.Namespace) -> dict[str, Any]:
    import numpy as np
    import scanpy as sc

    adata = build_fixture()
    original_counts = build_fixture().X

    sc.pp.calculate_qc_metrics(
        adata,
        qc_vars=["mito"],
        percent_top=(1, 2),
        layer="counts",
        inplace=True,
    )
    assert_true("total_counts" in adata.obs, "QC total_counts missing")
    assert_true("pct_counts_mito" in adata.obs, "QC mito percentage missing")

    sc.pp.normalize_total(adata, target_sum=args.target_sum, key_added="size_factor")
    normalized_totals = np.asarray(adata.X.sum(axis=1)).ravel()
    assert_true(np.allclose(normalized_totals, args.target_sum), "normalization totals differ")
    assert_true(np.allclose(adata.layers["counts"], original_counts), "counts layer changed")

    sc.pp.log1p(adata)
    hvg = sc.pp.highly_variable_genes(
        adata,
        flavor="seurat",
        n_top_genes=min(args.n_top_genes, adata.n_vars),
        inplace=False,
    )
    assert_true(hvg is not None, "HVG inplace=False returned None")
    assert_true("highly_variable" in hvg, "HVG result missing highly_variable column")

    adata.var["highly_variable"] = hvg["highly_variable"].to_numpy()
    sc.pp.scale(adata, max_value=10)
    n_comps = min(args.n_comps, adata.n_obs - 1, adata.n_vars - 1)
    assert_true(n_comps >= 1, "fixture too small for PCA")
    sc.pp.pca(adata, n_comps=n_comps, mask_var=None, rng=args.rng)
    assert_true("X_pca" in adata.obsm, "PCA coordinates missing")
    assert_true(adata.obsm["X_pca"].shape == (adata.n_obs, n_comps), "PCA shape mismatch")

    return {
        "mode": "normalize-log-hvg-pca",
        "normalized_total_min": float(normalized_totals.min()),
        "normalized_total_max": float(normalized_totals.max()),
        "counts_layer_preserved": bool(np.allclose(adata.layers["counts"], original_counts)),
        "log1p_recorded": "log1p" in adata.uns,
        "hvg_rows": int(hvg.shape[0]),
        "hvg_selected": int(hvg["highly_variable"].sum()),
        "pca_shape": list(adata.obsm["X_pca"].shape),
        "scale_columns_present": sorted(set(["mean", "std"]) & set(adata.var.columns)),
        "size_factor_positive": bool((adata.obs["size_factor"] > 0).all()),
    }


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    adata = build_fixture()
    output: dict[str, Any] = {
        "scanpy_version": version("scanpy"),
        "initial_shape": list(adata.shape),
    }
    if args.mode == "filter-sample":
        output.update(run_filter_smoke(args))
    else:
        output.update(run_preprocess_smoke(args))
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny self-contained Scanpy preprocessing/QC smoke check and print JSON."
    )
    parser.add_argument(
        "--mode",
        choices=("normalize-log-hvg-pca", "filter-sample"),
        default="normalize-log-hvg-pca",
        help="Which preprocessing path to smoke-test.",
    )
    parser.add_argument(
        "--target-sum",
        type=float,
        default=1.0,
        help="Target per-cell total for normalize_total in normalize-log-hvg-pca mode.",
    )
    parser.add_argument(
        "--n-top-genes",
        type=int,
        default=3,
        help="Requested HVG count, capped by fixture genes.",
    )
    parser.add_argument(
        "--n-comps",
        type=int,
        default=2,
        help="Requested PCA components, capped to fit the tiny fixture.",
    )
    parser.add_argument(
        "--sample-n",
        type=int,
        default=3,
        help="Number of cells to keep in filter-sample mode.",
    )
    parser.add_argument("--rng", type=int, default=0, help="Random seed for stochastic steps.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run_smoke(args), sort_keys=True))


if __name__ == "__main__":
    main()
