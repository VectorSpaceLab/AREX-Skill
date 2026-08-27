#!/usr/bin/env python
"""Deterministic Scanpy graph/embedding/marker smoke check.

The fixture is synthetic and does not depend on any source checkout files. By
default the script avoids optional Leiden/Louvain dependencies; pass
``--try-leiden`` to test clustering and receive a clear skip reason if the
required graph packages are unavailable.
"""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def make_adata():
    import numpy as np
    import pandas as pd
    from anndata import AnnData

    rng = np.random.default_rng(7)
    group_a = rng.normal(loc=2.0, scale=0.15, size=(10, 3))
    group_b = rng.normal(loc=0.2, scale=0.10, size=(10, 3))
    group_c = rng.normal(loc=1.0, scale=0.12, size=(10, 3))
    signal = np.vstack([group_a, group_b, group_c])
    background = rng.normal(loc=0.5, scale=0.05, size=(30, 5))
    matrix = np.clip(np.hstack([signal, background]), 0, None).astype(np.float32)

    adata = AnnData(matrix)
    adata.var_names = [f"gene_{idx}" for idx in range(adata.n_vars)]
    adata.obs["truth"] = pd.Categorical(["a"] * 10 + ["b"] * 10 + ["c"] * 10)
    adata.obs["coarse"] = pd.Categorical(["left"] * 10 + ["right"] * 20)
    adata.layers["log1p"] = np.log1p(adata.X)
    return adata


def call_with_seed(func, *args, **kwargs):
    """Call a Scanpy function across rng/random_state naming differences."""

    try:
        return func(*args, rng=0, **kwargs)
    except TypeError as error:
        if "rng" not in str(error):
            raise
        return func(*args, random_state=0, **kwargs)


def run_smoke(include_umap: bool, try_leiden: bool) -> dict[str, Any]:
    import numpy as np
    import scanpy as sc

    adata = make_adata()
    sc.pp.pca(adata, n_comps=5, random_state=0)
    call_with_seed(sc.pp.neighbors, adata, n_neighbors=6, n_pcs=5)
    call_with_seed(
        sc.pp.neighbors,
        adata,
        n_neighbors=8,
        use_rep="X_pca",
        metric="cosine",
        key_added="neighbors_cosine",
    )

    result: dict[str, Any] = {
        "scanpy_version": package_version("scanpy"),
        "shape": list(adata.shape),
        "default_graph": {
            "uns_key": "neighbors",
            "connectivities_key": adata.uns["neighbors"]["connectivities_key"],
            "connectivities_shape": list(adata.obsp["connectivities"].shape),
        },
        "alternate_graph": {
            "uns_key": "neighbors_cosine",
            "connectivities_key": adata.uns["neighbors_cosine"]["connectivities_key"],
            "connectivities_shape": list(adata.obsp["neighbors_cosine_connectivities"].shape),
        },
    }

    if include_umap:
        try:
            call_with_seed(
                sc.tl.umap,
                adata,
                neighbors_key="neighbors_cosine",
                key_added="X_umap_cosine",
                maxiter=20,
            )
            result["umap"] = {
                "status": "ok",
                "obsm_key": "X_umap_cosine",
                "shape": list(adata.obsm["X_umap_cosine"].shape),
            }
        except Exception as error:  # noqa: BLE001 - smoke output should report environment gaps.
            result["umap"] = {"status": "skipped", "reason": f"{type(error).__name__}: {error}"}
    else:
        result["umap"] = {"status": "skipped", "reason": "--skip-umap"}

    if try_leiden:
        try:
            call_with_seed(
                sc.tl.leiden,
                adata,
                resolution=0.5,
                key_added="leiden_r05",
                neighbors_key="neighbors",
            )
            result["leiden"] = {
                "status": "ok",
                "obs_key": "leiden_r05",
                "n_categories": int(adata.obs["leiden_r05"].nunique()),
            }
        except Exception as error:  # noqa: BLE001 - optional dependency failures are expected.
            result["leiden"] = {"status": "skipped", "reason": f"{type(error).__name__}: {error}"}
    else:
        result["leiden"] = {"status": "skipped", "reason": "pass --try-leiden to test optional clustering"}

    sc.tl.rank_genes_groups(
        adata,
        groupby="truth",
        method="t-test",
        layer="log1p",
        use_raw=False,
        n_genes=3,
        pts=True,
        key_added="rank_truth",
    )
    sc.tl.filter_rank_genes_groups(
        adata,
        key="rank_truth",
        key_added="rank_truth_filtered",
        min_in_group_fraction=0.1,
        max_out_group_fraction=1.0,
        min_fold_change=0.0,
    )
    call_with_seed(
        sc.tl.score_genes,
        adata,
        gene_list=["gene_0", "gene_1"],
        score_name="signal_score",
        ctrl_size=2,
        n_bins=3,
        use_raw=False,
    )

    moran = sc.metrics.morans_i(
        adata,
        vals=adata.obs["signal_score"].to_numpy(),
        neighbors_key="neighbors_cosine",
    )
    geary = sc.metrics.gearys_c(
        adata,
        vals=adata.obs["signal_score"].to_numpy(),
        neighbors_key="neighbors_cosine",
    )
    confusion = sc.metrics.confusion_matrix("truth", "coarse", data=adata.obs, normalize=True)

    result.update(
        {
            "rank_genes_groups": {
                "key": "rank_truth",
                "groups": list(adata.uns["rank_truth"]["names"].dtype.names),
                "filtered_key_present": "rank_truth_filtered" in adata.uns,
            },
            "score_genes": {
                "obs_key": "signal_score",
                "mean": float(np.mean(adata.obs["signal_score"])),
            },
            "metrics": {
                "morans_i": float(moran),
                "gearys_c": float(geary),
                "confusion_shape": list(confusion.shape),
            },
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-umap",
        action="store_true",
        help="Skip UMAP if the environment lacks a working umap-learn stack.",
    )
    parser.add_argument(
        "--try-leiden",
        action="store_true",
        help="Attempt optional Leiden clustering and report a clear skip reason on failure.",
    )
    args = parser.parse_args()
    print(json.dumps(run_smoke(include_umap=not args.skip_umap, try_leiden=args.try_leiden), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
