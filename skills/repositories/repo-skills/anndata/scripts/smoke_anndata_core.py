#!/usr/bin/env python3
"""Safe AnnData smoke test for import, object construction, concat, and I/O.

Example:
    python smoke_anndata_core.py
    python smoke_anndata_core.py --skip-zarr
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe tiny AnnData smoke checks.")
    parser.add_argument("--skip-h5ad", action="store_true", help="Skip H5AD round-trip.")
    parser.add_argument("--skip-zarr", action="store_true", help="Skip Zarr round-trip.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import anndata as ad
    import numpy as np
    import pandas as pd

    a = ad.AnnData(
        np.array([[1.0, 0.0], [0.0, 2.0]]),
        obs=pd.DataFrame({"batch": ["a", "a"]}, index=["c1", "c2"]),
        var=pd.DataFrame(index=["g1", "g2"]),
        layers={"counts": np.array([[1, 0], [0, 2]])},
        obsm={"embedding": np.array([[0.0, 1.0], [1.0, 0.0]])},
    )
    b = a.copy()
    b.obs_names = ["c3", "c4"]
    combined = ad.concat({"a": a, "b": b}, label="dataset", index_unique="-")
    print("import", ad.__name__)
    print("object", a.shape, [key for key in a.layers.keys() if key is not None], list(a.obsm))
    print("concat", combined.shape, list(combined.obs["dataset"].cat.categories))

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        if not args.skip_h5ad:
            h5ad_path = tmpdir / "tiny.h5ad"
            a.write_h5ad(h5ad_path)
            print("h5ad", ad.read_h5ad(h5ad_path).shape)
        if not args.skip_zarr:
            zarr_path = tmpdir / "tiny.zarr"
            a.write_zarr(zarr_path)
            print("zarr", ad.read_zarr(zarr_path).shape)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
