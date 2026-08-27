#!/usr/bin/env python3
"""Run a tiny headless Scanpy plotting smoke test and print JSON."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny AnnData object, render Scanpy plots with Matplotlib's "
            "Agg backend, save PNG outputs, and print JSON."
        )
    )
    parser.add_argument(
        "--basis",
        default="umap",
        choices=["embedding", "umap", "pca"],
        help="Embedding-style API to exercise. 'embedding' calls sc.pl.embedding with basis='umap'.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for PNG outputs. If omitted, a temporary directory is used and removed.",
    )
    parser.add_argument(
        "--include-dotplot",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also render a class-backed dotplot with return_fig=True.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=120,
        help="DPI used when saving smoke-test figures.",
    )
    return parser.parse_args()


def build_adata():
    import numpy as np
    import pandas as pd
    from anndata import AnnData

    adata = AnnData(
        X=np.array(
            [
                [1.0, 0.0, 3.0],
                [0.0, 2.0, 1.0],
                [3.0, 1.0, 0.0],
                [0.5, 1.5, 2.5],
            ],
            dtype=float,
        ),
        obs=pd.DataFrame(
            {"cluster": pd.Categorical(["A", "B", "A", "B"], categories=["A", "B"])},
            index=["cell0", "cell1", "cell2", "cell3"],
        ),
        var=pd.DataFrame(
            {"symbol": ["GA", "GB", "GC"]},
            index=["GeneA", "GeneB", "GeneC"],
        ),
    )
    adata.layers["scaled"] = adata.X.copy() * 0.5
    adata.obsm["X_umap"] = np.array(
        [[0.0, 0.0], [1.0, 0.2], [0.2, 1.0], [1.2, 1.1]], dtype=float
    )
    adata.obsm["X_pca"] = np.array(
        [[-1.0, 0.0], [0.2, -0.5], [0.4, 0.6], [1.0, 0.2]], dtype=float
    )
    adata.uns["cluster_colors"] = ["#1f77b4", "#ff7f0e"]
    return adata


def save_figure(figure, output_path: Path, dpi: int) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
    return int(output_path.stat().st_size)


def main() -> int:
    args = parse_args()

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import scanpy as sc
    except ModuleNotFoundError as error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "missing_dependency",
                    "missing": error.name,
                    "basis": args.basis,
                },
                sort_keys=True,
            )
        )
        return 2

    adata = build_adata()
    sc.settings.autoshow = False
    sc.set_figure_params(dpi=args.dpi, dpi_save=args.dpi, format="png")

    temp_dir = None
    if args.output_dir is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="scanpy-plot-smoke-")
        output_dir = Path(temp_dir.name)
    else:
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, int] = {}
    try:
        if args.basis == "embedding":
            axes = sc.pl.embedding(adata, basis="umap", color="cluster", show=False)
            embedding_name = "embedding_umap.png"
        elif args.basis == "pca":
            axes = sc.pl.pca(adata, color="cluster", show=False)
            embedding_name = "pca.png"
        else:
            axes = sc.pl.umap(adata, color="cluster", show=False)
            embedding_name = "umap.png"

        figure = axes[0].figure if isinstance(axes, list) else axes.figure
        outputs[embedding_name] = save_figure(figure, output_dir / embedding_name, args.dpi)
        plt.close(figure)

        if args.include_dotplot:
            dotplot = sc.pl.dotplot(
                adata,
                ["GeneA", "GeneB"],
                groupby="cluster",
                layer="scaled",
                use_raw=False,
                return_fig=True,
            )
            dotplot.style(cmap="Reds").legend(colorbar_title="Mean expression")
            dotplot.make_figure()
            outputs["dotplot.png"] = save_figure(dotplot.fig, output_dir / "dotplot.png", args.dpi)
            plt.close(dotplot.fig)
    finally:
        plt.close("all")

    result = {
        "ok": bool(outputs) and all(size > 0 for size in outputs.values()),
        "basis": args.basis,
        "cells": int(adata.n_obs),
        "genes": int(adata.n_vars),
        "backend": matplotlib.get_backend(),
        "output_dir": str(output_dir) if args.output_dir is not None else None,
        "outputs": outputs,
    }

    if temp_dir is not None:
        temp_dir.cleanup()

    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
