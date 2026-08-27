#!/usr/bin/env python3
"""Inspect a staged PyDESeq2 model-fitting pipeline on local synthetic data.

The script is intentionally self-contained: it creates a tiny count matrix in
memory, uses safe CPU defaults, and prints the AnnData keys produced by each
stage. It does not read source-repository examples, write outputs, download
files, or require a particular working directory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any


def load_runtime_dependencies():
    """Import scientific dependencies only after argparse handles --help."""
    try:
        import numpy as np
        import pandas as pd
        from pydeseq2.dds import DeseqDataSet
        from pydeseq2.default_inference import DefaultInference
    except ImportError as exc:  # pragma: no cover - helpful CLI failure path
        raise SystemExit(
            "PyDESeq2 and its scientific dependencies are not importable. Install "
            "them in the active environment with a generic command such as: "
            "python -m pip install pydeseq2"
        ) from exc

    return np, pd, DeseqDataSet, DefaultInference


@dataclass(frozen=True)
class Snapshot:
    stage: str
    obs: list[str]
    var: list[str]
    varm: list[str]
    layers: list[str]
    obsm: list[str]
    uns: list[str]


def make_synthetic_counts(
    n_samples: int = 12,
    n_genes: int = 8,
    seed: int = 13,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create deterministic samples-by-genes count and metadata tables."""
    if n_samples < 8:
        raise ValueError("Use at least 8 samples so staged dispersion fitting is stable.")
    if n_genes < 4:
        raise ValueError("Use at least 4 genes so trend fitting has enough points.")

    rng = np.random.default_rng(seed)
    conditions = np.array(["A"] * (n_samples // 2) + ["B"] * (n_samples - n_samples // 2))
    sample_names = [f"sample_{i + 1:02d}" for i in range(n_samples)]
    gene_names = [f"gene_{j + 1:02d}" for j in range(n_genes)]

    library_size = rng.uniform(0.85, 1.2, size=n_samples)[:, None]
    base_means = np.linspace(35, 260, n_genes)[None, :]
    condition_effect = np.ones((n_samples, n_genes))
    condition_effect[conditions == "B", 1::3] = 1.6
    condition_effect[conditions == "B", 2::3] = 0.65
    lam = library_size * base_means * condition_effect

    counts = rng.poisson(lam).astype(int) + 1
    counts_df = pd.DataFrame(counts, index=sample_names, columns=gene_names)
    metadata = pd.DataFrame({"condition": conditions}, index=sample_names)
    return counts_df, metadata


def snapshot(stage: str, dds: DeseqDataSet) -> Snapshot:
    """Collect sorted AnnData key names after one fitting stage."""
    return Snapshot(
        stage=stage,
        obs=sorted(map(str, dds.obs.keys())),
        var=sorted(map(str, dds.var.keys())),
        varm=sorted(map(str, dds.varm.keys())),
        layers=sorted(map(str, dds.layers.keys())),
        obsm=sorted(map(str, dds.obsm.keys())),
        uns=sorted(map(str, dds.uns.keys())),
    )


def print_snapshot(item: Snapshot) -> None:
    print(f"\n[{item.stage}]")
    print(f"  obs:    {', '.join(item.obs) or '-'}")
    print(f"  var:    {', '.join(item.var) or '-'}")
    print(f"  varm:   {', '.join(item.varm) or '-'}")
    print(f"  layers: {', '.join(item.layers) or '-'}")
    print(f"  obsm:   {', '.join(item.obsm) or '-'}")
    print(f"  uns:    {', '.join(item.uns) or '-'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run PyDESeq2 internals stage by stage on a generated synthetic "
            "count matrix and print expected AnnData storage keys."
        )
    )
    parser.add_argument("--n-cpus", type=int, default=1, help="CPUs for DefaultInference; default: 1.")
    parser.add_argument(
        "--fit-type",
        choices=["parametric", "mean"],
        default="parametric",
        help="Dispersion trend fit type for the DEA stages; default: parametric.",
    )
    parser.add_argument(
        "--size-factors-fit-type",
        choices=["ratio", "poscounts", "iterative"],
        default="ratio",
        help="Size-factor fitting mode; default: ratio.",
    )
    parser.add_argument(
        "--use-design-vst",
        action="store_true",
        help="Fit VST using the full design matrix instead of blind intercept-only VST.",
    )
    parser.add_argument(
        "--low-memory",
        action="store_true",
        help="Enable PyDESeq2 low_memory mode to show which intermediates may disappear.",
    )
    parser.add_argument("--seed", type=int, default=13, help="Synthetic data seed; default: 13.")
    parser.add_argument("--samples", type=int, default=12, help="Synthetic sample count; default: 12.")
    parser.add_argument("--genes", type=int, default=8, help="Synthetic gene count; default: 8.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the final stage snapshots as JSON instead of human-readable text.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    global np, pd, DeseqDataSet, DefaultInference
    np, pd, DeseqDataSet, DefaultInference = load_runtime_dependencies()
    counts_df, metadata = make_synthetic_counts(args.samples, args.genes, args.seed)

    inference = DefaultInference(n_cpus=args.n_cpus)
    dds = DeseqDataSet(
        counts=counts_df,
        metadata=metadata,
        design="~condition",
        fit_type=args.fit_type,
        size_factors_fit_type=args.size_factors_fit_type,
        inference=inference,
        quiet=True,
        low_memory=args.low_memory,
    )

    snapshots: list[Snapshot] = [snapshot("initialized", dds)]

    dds.fit_size_factors()
    snapshots.append(snapshot("fit_size_factors", dds))

    dds.fit_genewise_dispersions()
    snapshots.append(snapshot("fit_genewise_dispersions", dds))

    dds.fit_dispersion_trend()
    snapshots.append(snapshot("fit_dispersion_trend", dds))

    dds.fit_dispersion_prior()
    snapshots.append(snapshot("fit_dispersion_prior", dds))

    dds.fit_MAP_dispersions()
    snapshots.append(snapshot("fit_MAP_dispersions", dds))

    dds.fit_LFC()
    snapshots.append(snapshot("fit_LFC", dds))

    dds.calculate_cooks()
    snapshots.append(snapshot("calculate_cooks", dds))

    if dds.refit_cooks:
        dds.refit()
        snapshots.append(snapshot("refit", dds))

    dds.cooks_outlier()
    snapshots.append(snapshot("cooks_outlier", dds))

    dds.vst(use_design=args.use_design_vst, fit_type=args.fit_type)
    snapshots.append(snapshot("vst", dds))

    external_vst = dds.vst_transform(counts_df.to_numpy())

    expected_keys: dict[str, Any] = {
        "size_factors": "size_factors" in dds.obs,
        "normed_counts": "normed_counts" in dds.layers,
        "genewise_dispersions": "genewise_dispersions" in dds.var,
        "fitted_dispersions": "fitted_dispersions" in dds.var,
        "prior_disp_var": "prior_disp_var" in dds.uns,
        "dispersions": "dispersions" in dds.var,
        "LFC": "LFC" in dds.varm,
        "cooks": "cooks" in dds.layers,
        "pvalue_cooks_outlier": "_pvalue_cooks_outlier" in dds.var,
        "vst_counts": "vst_counts" in dds.layers,
        "external_vst_shape": list(external_vst.shape),
    }

    if args.json:
        payload = {
            "counts_shape": list(counts_df.shape),
            "design_columns": list(dds.obsm["design_matrix"].columns),
            "expected_keys": expected_keys,
            "snapshots": [item.__dict__ for item in snapshots],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("PyDESeq2 stepwise internals inspection")
    print(f"counts shape: {counts_df.shape[0]} samples x {counts_df.shape[1]} genes")
    print(f"design columns: {list(dds.obsm['design_matrix'].columns)}")
    print(f"DefaultInference n_cpus: {dds.inference.n_cpus}")
    print(f"fit_type: {dds.fit_type}; size_factors_fit_type: {dds.size_factors_fit_type}")
    print(f"use_design_vst: {args.use_design_vst}; low_memory: {args.low_memory}")

    for item in snapshots:
        print_snapshot(item)

    print("\nExpected key check:")
    for key, value in expected_keys.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
