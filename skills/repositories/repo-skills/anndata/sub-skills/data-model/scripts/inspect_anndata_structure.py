#!/usr/bin/env python3
"""Inspect the public structure of a tiny or existing AnnData object."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a deterministic AnnData data-model summary: shape, axis-name "
            "uniqueness, aligned slot keys and shapes, raw state, view state, and "
            "backed/filename state. If no input is provided, a tiny demo AnnData is used."
        )
    )
    parser.add_argument(
        "--h5ad",
        type=Path,
        action="append",
        default=[],
        metavar="PATH",
        help="Inspect an existing .h5ad file with anndata.read_h5ad(PATH). Can be repeated.",
    )
    parser.add_argument(
        "--zarr",
        type=Path,
        action="append",
        default=[],
        metavar="PATH",
        help="Inspect an existing Zarr store with anndata.read_zarr(PATH). Can be repeated.",
    )
    return parser.parse_args()


def require_imports() -> tuple[Any, Any, Any]:
    try:
        import anndata as ad
        import numpy as np
        import pandas as pd
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        raise SystemExit(f"FAIL missing dependency {missing!r}; install anndata and its base dependencies.") from exc
    return ad, np, pd


def make_demo(ad: Any, np: Any, pd: Any) -> Any:
    x = np.array(
        [
            [1.0, 0.0, 2.0],
            [0.0, 3.0, 4.0],
            [5.0, 0.0, 6.0],
        ],
        dtype=np.float32,
    )
    obs = pd.DataFrame(
        {
            "batch": pd.Categorical(["a", "a", "b"]),
            "quality": np.array([0.10, 0.20, 0.30], dtype=np.float32),
        },
        index=["cell-0", "cell-1", "cell-2"],
    )
    var = pd.DataFrame(
        {"symbol": ["g0", "g1", "g2"]},
        index=["gene-0", "gene-1", "gene-2"],
    )
    adata = ad.AnnData(X=x, obs=obs, var=var)
    adata.layers["counts"] = x.astype("int64")
    adata.obsm["X_pca"] = np.arange(6, dtype=np.float32).reshape(3, 2)
    adata.varm["PCs"] = np.arange(6, dtype=np.float32).reshape(3, 2)
    adata.obsp["distances"] = np.eye(adata.n_obs, dtype=np.float32)
    adata.varp["correlations"] = np.eye(adata.n_vars, dtype=np.float32)
    adata.uns["demo"] = {"created_by": "inspect_anndata_structure.py"}
    adata.raw = adata.copy()
    return adata


def safe_shape(value: Any) -> str:
    shape = getattr(value, "shape", None)
    if shape is None:
        return "shape=<unknown>"
    try:
        return "shape=" + repr(tuple(shape))
    except TypeError:
        return "shape=" + repr(shape)


def sorted_keys(mapping: Any, *, include_none: bool = True) -> list[Any]:
    try:
        keys = list(mapping.keys())
    except Exception:  # noqa: BLE001
        return []
    if not include_none:
        keys = [key for key in keys if key is not None]
    return sorted(keys, key=lambda key: str(key))


def display_keys(keys: list[Any]) -> list[str]:
    return [str(key) for key in keys]


def print_mapping_shapes(
    label: str,
    mapping: Any,
    expected: tuple[int, ...] | None,
    warnings: list[str],
    *,
    include_none: bool = True,
) -> None:
    keys = sorted_keys(mapping, include_none=include_none)
    print(f"{label}_keys={display_keys(keys)}")
    for key in keys:
        try:
            value = mapping[key]
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{label}[{key!r}] could not be read: {type(exc).__name__}: {exc}")
            continue
        shape = getattr(value, "shape", None)
        print(f"{label}[{key!r}] {safe_shape(value)} type={type(value).__name__}")
        if expected is not None and shape is not None:
            try:
                actual = tuple(shape)
            except TypeError:
                continue
            if actual != expected:
                warnings.append(f"{label}[{key!r}] has shape {actual}, expected {expected}")


def print_axis_mapping_shapes(
    label: str,
    mapping: Any,
    axis_name: str,
    expected_first_dim: int,
    expected_index: Any,
    warnings: list[str],
) -> None:
    keys = sorted_keys(mapping)
    print(f"{label}_keys={display_keys(keys)}")
    for key in keys:
        try:
            value = mapping[key]
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{label}[{key!r}] could not be read: {type(exc).__name__}: {exc}")
            continue
        shape = getattr(value, "shape", None)
        print(f"{label}[{key!r}] {safe_shape(value)} type={type(value).__name__}")
        if shape is not None:
            try:
                actual_first_dim = tuple(shape)[0]
            except (IndexError, TypeError):
                actual_first_dim = None
            if actual_first_dim != expected_first_dim:
                warnings.append(
                    f"{label}[{key!r}] first dimension {actual_first_dim!r}, expected {expected_first_dim} ({axis_name})"
                )
        index = getattr(value, "index", None)
        if index is not None:
            try:
                if not index.equals(expected_index):
                    warnings.append(f"{label}[{key!r}] DataFrame index does not equal {axis_name}_names")
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{label}[{key!r}] index comparison failed: {type(exc).__name__}: {exc}")


def inspect_adata(label: str, adata: Any) -> None:
    warnings: list[str] = []
    print(f"== {label} ==")
    print(f"type={type(adata).__name__}")
    print(f"shape={tuple(adata.shape)} n_obs={adata.n_obs} n_vars={adata.n_vars}")
    print(f"is_view={adata.is_view}")
    print(f"isbacked={getattr(adata, 'isbacked', None)}")
    print(f"filename={getattr(adata, 'filename', None)}")
    print(f"X {safe_shape(adata.X)} type={type(adata.X).__name__ if adata.X is not None else 'None'}")

    obs_names = adata.obs_names
    var_names = adata.var_names
    print(f"obs_shape={tuple(adata.obs.shape)} obs_names_unique={obs_names.is_unique}")
    print(f"var_shape={tuple(adata.var.shape)} var_names_unique={var_names.is_unique}")
    if len(obs_names) != adata.n_obs:
        warnings.append(f"obs_names length {len(obs_names)} != n_obs {adata.n_obs}")
    if len(var_names) != adata.n_vars:
        warnings.append(f"var_names length {len(var_names)} != n_vars {adata.n_vars}")
    if not obs_names.is_unique:
        warnings.append("obs_names are not unique; consider adata.obs_names_make_unique()")
    if not var_names.is_unique:
        warnings.append("var_names are not unique; consider adata.var_names_make_unique()")

    print_mapping_shapes("layers", adata.layers, tuple(adata.shape), warnings, include_none=False)
    print_axis_mapping_shapes("obsm", adata.obsm, "obs", adata.n_obs, obs_names, warnings)
    print_axis_mapping_shapes("varm", adata.varm, "var", adata.n_vars, var_names, warnings)
    print_mapping_shapes("obsp", adata.obsp, (adata.n_obs, adata.n_obs), warnings)
    print_mapping_shapes("varp", adata.varp, (adata.n_vars, adata.n_vars), warnings)
    print(f"uns_keys={display_keys(sorted_keys(adata.uns))}")

    raw = adata.raw
    if raw is None:
        print("raw=None")
    else:
        print(
            "raw="
            f"shape={tuple(raw.shape)} "
            f"n_obs={raw.n_obs} "
            f"n_vars={raw.n_vars} "
            f"var_names_unique={raw.var_names.is_unique} "
            f"X_{safe_shape(raw.X)}"
        )
        if raw.n_obs != adata.n_obs:
            warnings.append(f"raw.n_obs {raw.n_obs} != adata.n_obs {adata.n_obs}")

    if warnings:
        print("suspicious_mismatches:")
        for message in warnings:
            print(f"- {message}")
    else:
        print("suspicious_mismatches=[]")
    print()


def read_inputs(ad: Any, h5ad_paths: list[Path], zarr_paths: list[Path]) -> list[tuple[str, Any]]:
    loaded: list[tuple[str, Any]] = []
    for path in h5ad_paths:
        try:
            loaded.append((f"h5ad:{path}", ad.read_h5ad(path)))
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL h5ad:{path}: {type(exc).__name__}: {exc}", file=sys.stderr)
    for path in zarr_paths:
        try:
            loaded.append((f"zarr:{path}", ad.read_zarr(path)))
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL zarr:{path}: {type(exc).__name__}: {exc}", file=sys.stderr)
    return loaded


def main() -> int:
    args = parse_args()
    ad, np, pd = require_imports()
    adatas = read_inputs(ad, args.h5ad, args.zarr)
    if not args.h5ad and not args.zarr:
        adatas = [("demo", make_demo(ad, np, pd))]
    if not adatas:
        return 1
    for label, adata in adatas:
        inspect_adata(label, adata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
