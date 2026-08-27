#!/usr/bin/env python3
"""Smoke-test Squidpy plotting with generated in-memory data."""

from __future__ import annotations

import argparse
import contextlib
import io
import tempfile
import warnings
from pathlib import Path
from typing import Any


def build_adata() -> Any:
    import numpy as np
    import pandas as pd
    from anndata import AnnData
    coordinates = np.array(
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
    expression = np.array(
        [
            [1.0, 0.2],
            [0.8, 0.3],
            [0.1, 1.1],
            [0.2, 0.9],
            [1.2, 0.4],
            [0.3, 1.0],
        ],
        dtype=float,
    )
    obs = pd.DataFrame(
        {
            "cluster": pd.Categorical(["A", "A", "B", "B", "A", "B"]),
            "score": [0.1, 0.4, 0.8, 0.7, 0.3, 0.9],
        },
        index=[f"cell{i}" for i in range(coordinates.shape[0])],
    )
    adata = AnnData(expression, obs=obs, var=pd.DataFrame(index=["GeneA", "GeneB"]))
    adata.obsm["spatial"] = coordinates
    return adata


def compute_spatial_graph(sq: Any, adata: Any) -> None:
    if hasattr(sq.gr, "spatial_neighbors_knn"):
        sq.gr.spatial_neighbors_knn(adata, n_neighs=2, key_added="spatial")
    else:
        sq.gr.spatial_neighbors(adata, n_neighs=2, coord_type="generic", key_added="spatial")


def run_smoke(output_dir: Path, quiet: bool) -> list[Path]:
    if quiet:
        warnings.filterwarnings("ignore", category=SyntaxWarning)
        warnings.filterwarnings("ignore", message="No data for colormapping provided via 'c'.*")

    import matplotlib

    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import scanpy as sc
    import squidpy as sq

    if quiet:
        sc.settings.verbosity = 0

    output_dir.mkdir(parents=True, exist_ok=True)
    adata = build_adata()

    with contextlib.ExitStack() as stack:
        if quiet:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))

        scatter_ax = sq.pl.spatial_scatter(
            adata,
            shape=None,
            img=False,
            library_id="",
            color="cluster",
            size=80,
            title="Generated spatial scatter",
            return_ax=True,
        )
        scatter_path = output_dir / "spatial_scatter.png"
        scatter_ax.figure.savefig(scatter_path, dpi=120, bbox_inches="tight")
        plt.close(scatter_ax.figure)

        compute_spatial_graph(sq, adata)
        sq.gr.interaction_matrix(adata, cluster_key="cluster")
        fig, ax = plt.subplots(figsize=(3, 3), constrained_layout=True)
        sq.pl.interaction_matrix(adata, cluster_key="cluster", annotate=True, ax=ax)
        graph_path = output_dir / "interaction_matrix.png"
        fig.savefig(graph_path, dpi=120, bbox_inches="tight")
        plt.close(fig)

    outputs = [scatter_path, graph_path]
    if not quiet:
        for path in outputs:
            print(f"wrote {path}")
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a no-download Squidpy plotting smoke test using generated AnnData.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated PNG files. Defaults to a temporary directory.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress success messages.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir is None:
        with tempfile.TemporaryDirectory(prefix="squidpy-plotting-smoke-") as tmpdir:
            run_smoke(Path(tmpdir), quiet=args.quiet)
    else:
        run_smoke(args.output_dir, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
