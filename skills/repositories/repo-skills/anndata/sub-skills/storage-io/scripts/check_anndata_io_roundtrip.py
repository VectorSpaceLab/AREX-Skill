#!/usr/bin/env python3
"""Create and validate tiny AnnData H5AD and Zarr round-trips."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate deterministic tiny AnnData H5AD and/or Zarr round-trips. "
            "The checker uses local temporary fixtures and never accesses the network."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for generated fixtures; created if needed.",
    )
    parser.add_argument(
        "--skip-h5ad",
        action="store_true",
        help="Skip the H5AD write/read check.",
    )
    parser.add_argument(
        "--skip-zarr",
        action="store_true",
        help="Skip the Zarr write/read check.",
    )
    parser.add_argument(
        "--backed-lazy",
        action="store_true",
        help="Also check H5AD backed='r' and Zarr experimental.read_lazy when available.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep generated fixtures instead of deleting the temporary directory.",
    )
    return parser.parse_args()


def require_imports() -> tuple[Any, Any, Any, Any]:
    try:
        import anndata as ad
        import numpy as np
        import pandas as pd
        from scipy import sparse
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        raise SystemExit(
            f"FAIL missing dependency {missing!r}; install AnnData with the "
            "dependencies needed for H5AD/Zarr round-trips."
        ) from exc
    return ad, np, pd, sparse


def make_fixture(ad: Any, np: Any, pd: Any, sparse: Any) -> Any:
    matrix = sparse.csr_matrix(
        np.array(
            [
                [1.0, 0.0, 2.0, 0.0],
                [0.0, 3.0, 0.0, 4.0],
                [5.0, 0.0, 6.0, 0.0],
            ],
            dtype=np.float32,
        )
    )
    obs = pd.DataFrame(
        {
            "batch": pd.Categorical(["a", "a", "b"]),
            "quality": np.array([0.1, 0.2, 0.3], dtype=np.float32),
        },
        index=["cell-0", "cell-1", "cell-2"],
    )
    var = pd.DataFrame(
        {"gene_symbol": ["g0", "g1", "g2", "g3"]},
        index=["gene-0", "gene-1", "gene-2", "gene-3"],
    )
    adata = ad.AnnData(X=matrix, obs=obs, var=var)
    adata.layers["dense"] = matrix.toarray()
    adata.obsm["pca"] = np.arange(6, dtype=np.float32).reshape(3, 2)
    adata.uns["fixture"] = {"purpose": "storage-io-roundtrip", "version": 1}
    return adata


def assert_basic_equal(original: Any, loaded: Any) -> None:
    if loaded.shape != original.shape:
        raise AssertionError(f"shape mismatch: {loaded.shape!r} != {original.shape!r}")
    if list(loaded.obs_names) != list(original.obs_names):
        raise AssertionError("obs_names mismatch")
    if list(loaded.var_names) != list(original.var_names):
        raise AssertionError("var_names mismatch")
    if set(loaded.layers.keys()) != set(original.layers.keys()):
        raise AssertionError("layer keys mismatch")
    if set(loaded.obsm.keys()) != set(original.obsm.keys()):
        raise AssertionError("obsm keys mismatch")
    if "fixture" not in loaded.uns:
        raise AssertionError("missing uns['fixture'] after round-trip")


def replace_existing(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def validate_h5ad(ad: Any, original: Any, path: Path, check_backed: bool) -> None:
    replace_existing(path)
    original.write_h5ad(path, compression="lzf")
    loaded = ad.read_h5ad(path)
    assert_basic_equal(original, loaded)
    print(f"PASS h5ad eager shape={loaded.shape} path={path}")

    if check_backed:
        backed = ad.read_h5ad(path, backed="r")
        try:
            if not backed.isbacked:
                raise AssertionError("read_h5ad(..., backed='r') did not return backed object")
            if backed.shape != original.shape:
                raise AssertionError("backed shape mismatch")
            _ = backed.X[:2, :2]
            print(f"PASS h5ad backed shape={backed.shape} path={path}")
        finally:
            backed.file.close()


def validate_zarr(ad: Any, original: Any, path: Path, check_lazy: bool) -> None:
    replace_existing(path)
    original.write_zarr(path, chunks=(2, original.n_vars))
    loaded = ad.read_zarr(path)
    assert_basic_equal(original, loaded)
    print(f"PASS zarr eager shape={loaded.shape} path={path}")

    if check_lazy:
        try:
            lazy = ad.experimental.read_lazy(path)
        except (ImportError, ModuleNotFoundError) as exc:
            missing = getattr(exc, "name", None) or str(exc)
            print(f"SKIP zarr lazy missing_dependency={missing!r} path={path}")
            return
        if lazy.shape != original.shape:
            raise AssertionError("lazy zarr shape mismatch")
        print(f"PASS zarr lazy shape={lazy.shape} path={path}")


def main() -> int:
    args = parse_args()
    if args.skip_h5ad and args.skip_zarr:
        raise SystemExit("FAIL both --skip-h5ad and --skip-zarr were provided")

    ad, np, pd, sparse = require_imports()

    if args.output_dir is None:
        workdir = Path(tempfile.mkdtemp(prefix="anndata-io-roundtrip-"))
        owns_workdir = True
    else:
        workdir = args.output_dir.expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        owns_workdir = False

    try:
        fixture = make_fixture(ad, np, pd, sparse)
        if not args.skip_h5ad:
            validate_h5ad(ad, fixture, workdir / "fixture.h5ad", args.backed_lazy)
        if not args.skip_zarr:
            validate_zarr(ad, fixture, workdir / "fixture.zarr", args.backed_lazy)
        print(f"OK shape={fixture.shape} output_dir={workdir}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if owns_workdir and not args.keep:
            shutil.rmtree(workdir, ignore_errors=True)
        elif args.keep:
            print(f"KEPT output_dir={workdir}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
