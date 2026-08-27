#!/usr/bin/env python3
"""Tiny Scanpy IO roundtrip validator.

Creates a small AnnData object, writes it to a temporary .h5ad file, reads it
back through Scanpy, and prints validation details as JSON. The script is safe
to run from any working directory and does not depend on the Scanpy source tree.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exercise-obs-df",
        action="store_true",
        help="Also validate sc.get.obs_df extraction from obs and var keys.",
    )
    parser.add_argument(
        "--exercise-backed",
        action="store_true",
        help="Also validate a read-only backed read and a small expression extraction.",
    )
    parser.add_argument(
        "--keep-file",
        type=Path,
        default=None,
        help="Optional destination path for the generated .h5ad file.",
    )
    return parser


def package_version(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def close_backed(adata) -> None:
    backing_file = getattr(adata, "file", None)
    if backing_file is not None:
        close = getattr(backing_file, "close", None)
        if close is not None:
            close()


def main() -> int:
    args = build_parser().parse_args()

    try:
        import numpy as np
        import pandas as pd
        from anndata import AnnData
        import scanpy as sc
    except ModuleNotFoundError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "missing_dependency",
                    "module": exc.name,
                    "hint": "Install Scanpy and dependencies in the active Python environment.",
                },
                sort_keys=True,
            )
        )
        return 2

    counts = np.array([[1, 0, 2], [0, 3, 1]], dtype=np.int64)
    adata = AnnData(
        X=counts.astype(float),
        obs=pd.DataFrame(
            {"cell_type": ["B cell", "T cell"], "passes_qc": [True, True]},
            index=["cell_a", "cell_b"],
        ),
        var=pd.DataFrame(
            {"gene_symbols": ["MS4A1", "CD3D", "LYZ"]},
            index=["gene_0", "gene_1", "gene_2"],
        ),
        layers={"counts": counts.copy()},
        uns={"fixture": {"source": "scanpy_io_roundtrip"}},
    )
    adata.raw = adata

    obs_df_columns: list[str] = []
    backed_shape: list[int] | None = None
    output_file: str | None = None

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = args.keep_file or Path(tmpdir) / "scanpy_io_roundtrip.h5ad"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sc.write(output_path, adata)
        loaded = sc.read_h5ad(output_path)

        if args.exercise_obs_df:
            obs_df = sc.get.obs_df(
                loaded,
                keys=["cell_type", "MS4A1"],
                layer="counts",
                gene_symbols="gene_symbols",
            )
            obs_df_columns = list(obs_df.columns)
            if obs_df.loc["cell_a", "MS4A1"] != 1:
                raise AssertionError("Unexpected obs_df value for MS4A1/cell_a")

        if args.exercise_backed:
            backed = sc.read_h5ad(output_path, backed="r")
            try:
                backed_shape = list(backed.shape)
                backed_df = sc.get.obs_df(
                    backed,
                    keys=["MS4A1"],
                    gene_symbols="gene_symbols",
                )
                if backed_df.loc["cell_a", "MS4A1"] != 1.0:
                    raise AssertionError("Unexpected backed obs_df value for MS4A1/cell_a")
            finally:
                close_backed(backed)

        layers = sorted(loaded.layers.keys())
        ok = bool(
            loaded.shape == adata.shape
            and loaded.obs_names.tolist() == adata.obs_names.tolist()
            and loaded.var_names.tolist() == adata.var_names.tolist()
            and "counts" in layers
            and "fixture" in loaded.uns
            and loaded.raw is not None
        )
        output_file = str(output_path) if args.keep_file else None

    result = {
        "ok": ok,
        "shape": list(loaded.shape),
        "obs_names": loaded.obs_names.tolist(),
        "var_names": loaded.var_names.tolist(),
        "layers": layers,
        "has_raw": loaded.raw is not None,
        "obs_df_columns": obs_df_columns,
        "backed_shape": backed_shape,
        "file": output_file,
        "scanpy_version": package_version("scanpy"),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
