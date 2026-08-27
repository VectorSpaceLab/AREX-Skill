#!/usr/bin/env python3
"""Create tiny AnnData or MuData fixtures for scvi-tools setup smoke tests."""

from __future__ import annotations

import argparse
from pathlib import Path


def _counts(rows: int, cols: int, seed: int):
    import numpy as np
    from scipy import sparse

    rng = np.random.default_rng(seed)
    return sparse.csr_matrix(rng.poisson(lam=2.0, size=(rows, cols)).astype(np.int64))


def make_anndata(cells: int, genes: int, proteins: int, regions: int, seed: int):
    import numpy as np
    import pandas as pd
    from anndata import AnnData

    adata = AnnData(X=_counts(cells, genes, seed))
    adata.var_names = [f"gene_{i}" for i in range(genes)]
    adata.obs_names = [f"cell_{i}" for i in range(cells)]
    adata.obs["batch"] = pd.Categorical([f"batch_{i % 2}" for i in range(cells)])
    adata.obs["labels"] = pd.Categorical(["Unknown" if i % 5 == 0 else f"label_{i % 3}" for i in range(cells)])
    adata.obs["donor"] = pd.Categorical([f"donor_{i % 3}" for i in range(cells)])
    adata.obs["percent_mito"] = np.linspace(0.01, 0.2, cells)
    adata.layers["counts"] = adata.X.copy()
    if proteins:
        adata.obsm["protein_expression"] = _counts(cells, proteins, seed + 1)
        adata.uns["protein_names"] = np.array([f"protein_{i}" for i in range(proteins)])
    if regions:
        adata.obsm["accessibility"] = _counts(cells, regions, seed + 2)
    return adata


def make_mudata(cells: int, genes: int, proteins: int, regions: int, seed: int):
    from anndata import AnnData

    try:
        from mudata import MuData
    except ImportError as exc:  # pragma: no cover - depends on optional runtime installs
        raise SystemExit("mudata is required for --format mudata") from exc

    rna = make_anndata(cells, genes, proteins=0, regions=0, seed=seed)
    modalities = {"rna": rna}
    if regions:
        atac = AnnData(X=_counts(cells, regions, seed + 10), obs=rna.obs.copy())
        atac.obs_names = rna.obs_names.copy()
        atac.var_names = [f"region_{i}" for i in range(regions)]
        modalities["accessibility"] = atac
    if proteins:
        protein = AnnData(X=_counts(cells, proteins, seed + 20), obs=rna.obs.copy())
        protein.obs_names = rna.obs_names.copy()
        protein.var_names = [f"protein_{i}" for i in range(proteins)]
        modalities["protein_expression"] = protein
    return MuData(modalities)


def smoke_setup(data, data_format: str, skip_setup: bool) -> None:
    if skip_setup:
        return
    import scvi

    if data_format == "anndata":
        scvi.model.SCVI.setup_anndata(
            data,
            layer="counts",
            batch_key="batch",
            labels_key="labels",
            categorical_covariate_keys=["donor"],
            continuous_covariate_keys=["percent_mito"],
        )
        if "protein_expression" in data.obsm:
            scvi.model.TOTALVI.setup_anndata(
                data,
                protein_expression_obsm_key="protein_expression",
                protein_names_uns_key="protein_names",
                batch_key="batch",
                layer="counts",
            )
    else:
        modalities = {"rna_layer": "rna", "batch_key": "rna"}
        if "accessibility" in data.mod:
            modalities["atac_layer"] = "accessibility"
        if "protein_expression" in data.mod:
            modalities["protein_layer"] = "protein_expression"
        scvi.model.MULTIVI.setup_mudata(data, batch_key="batch", modalities=modalities)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("tiny_scvi_fixture.h5ad"), help="Output .h5ad or .h5mu path.")
    parser.add_argument("--format", choices=["anndata", "mudata"], default="anndata", help="Fixture container type.")
    parser.add_argument("--cells", type=int, default=24, help="Number of observations/cells.")
    parser.add_argument("--genes", type=int, default=12, help="Number of RNA genes.")
    parser.add_argument("--proteins", type=int, default=4, help="Number of protein features.")
    parser.add_argument("--regions", type=int, default=6, help="Number of accessibility regions.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for deterministic counts.")
    parser.add_argument("--skip-setup", action="store_true", help="Write the fixture without running scvi-tools setup smoke checks.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cells < 1 or args.genes < 1:
        raise SystemExit("--cells and --genes must be positive")
    if args.proteins < 0 or args.regions < 0:
        raise SystemExit("--proteins and --regions must be non-negative")

    if args.format == "anndata":
        data = make_anndata(args.cells, args.genes, args.proteins, args.regions, args.seed)
        smoke_setup(data, args.format, args.skip_setup)
        data.write_h5ad(args.output)
    else:
        data = make_mudata(args.cells, args.genes, args.proteins, args.regions, args.seed)
        smoke_setup(data, args.format, args.skip_setup)
        data.write_h5mu(args.output)

    print(f"wrote {args.format} fixture to {args.output}")


if __name__ == "__main__":
    main()
