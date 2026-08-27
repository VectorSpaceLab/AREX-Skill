#!/usr/bin/env python3
"""Validate AnnData slots needed by OmicVerse single-cell workflows.

The script is read-only for real AnnData files. Use --synthetic to generate a
small in-memory AnnData object for parser and environment checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check AnnData slots expected by OmicVerse single-cell workflows.",
    )
    parser.add_argument(
        "h5ad",
        nargs="?",
        help="Path to an .h5ad file. Omit when using --synthetic.",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Create a tiny synthetic AnnData object instead of reading a file.",
    )
    parser.add_argument(
        "--cluster-key",
        default="leiden",
        help="obs column expected to contain cluster or cell-type labels.",
    )
    parser.add_argument(
        "--batch-key",
        default=None,
        help="Optional obs column expected to contain batch/sample labels.",
    )
    parser.add_argument(
        "--sample-key",
        default=None,
        help="Optional obs column expected to contain donor/sample labels for pseudobulk.",
    )
    parser.add_argument(
        "--pseudotime-key",
        default=None,
        help="Optional obs column expected to contain pseudotime values.",
    )
    parser.add_argument(
        "--embedding",
        action="append",
        default=[],
        help="Required obsm key. Repeat for multiple embeddings, e.g. --embedding X_umap.",
    )
    parser.add_argument(
        "--layer",
        action="append",
        default=[],
        help="Required layer key. Repeat for counts/scaled layers.",
    )
    parser.add_argument(
        "--require-rank-genes",
        action="store_true",
        help="Require uns['rank_genes_groups'] for marker-based annotation.",
    )
    parser.add_argument(
        "--require-neighbors",
        action="store_true",
        help="Require obsp['connectivities'] for trajectory/fate/Milo workflows.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    return parser


def _load_anndata(path: str | None, synthetic: bool):
    try:
        import numpy as np
        import pandas as pd
        import scipy.sparse as sp
        from anndata import AnnData, read_h5ad
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit(f"ERROR: anndata, numpy, pandas, and scipy are required: {exc}") from exc

    if synthetic:
        rng = np.random.default_rng(7)
        matrix = rng.poisson(2.0, size=(24, 12)).astype("float32")
        obs = pd.DataFrame(
            {
                "leiden": pd.Categorical([str(i % 3) for i in range(24)]),
                "batch": pd.Categorical([f"b{i % 2}" for i in range(24)]),
                "donor": pd.Categorical([f"d{i % 4}" for i in range(24)]),
                "pseudotime": np.linspace(0.0, 1.0, 24),
            },
            index=[f"cell_{i}" for i in range(24)],
        )
        var = pd.DataFrame(index=[f"Gene{i}" for i in range(12)])
        adata = AnnData(X=matrix, obs=obs, var=var)
        adata.layers["counts"] = matrix.copy()
        adata.layers["scaled"] = (matrix - matrix.mean(axis=0)).astype("float32")
        adata.obsm["X_pca"] = rng.normal(size=(24, 5)).astype("float32")
        adata.obsm["X_umap"] = rng.normal(size=(24, 2)).astype("float32")
        connectivity = sp.eye(24, format="csr")
        adata.obsp["connectivities"] = connectivity
        adata.uns["rank_genes_groups"] = {"names": {"0": ["Gene0", "Gene1"]}}
        return adata, "synthetic"

    if not path:
        raise SystemExit("ERROR: provide an .h5ad path or pass --synthetic.")
    h5ad_path = Path(path).expanduser()
    if not h5ad_path.exists():
        raise SystemExit(f"ERROR: file does not exist: {h5ad_path}")
    if not h5ad_path.is_file():
        raise SystemExit(f"ERROR: not a file: {h5ad_path}")
    return read_h5ad(h5ad_path, backed=None), str(h5ad_path)


def _matrix_summary(matrix: Any) -> dict[str, Any]:
    try:
        import numpy as np
        import scipy.sparse as sp
    except Exception as exc:  # pragma: no cover - import checked earlier
        return {"ok": False, "detail": f"matrix summary imports failed: {exc}"}

    shape = tuple(int(x) for x in getattr(matrix, "shape", ()))
    sparse = bool(sp.issparse(matrix))
    if sparse:
        nnz = int(matrix.nnz)
        finite = bool(np.isfinite(matrix.data).all()) if nnz else True
        min_value = float(matrix.data.min()) if nnz else 0.0
        max_value = float(matrix.data.max()) if nnz else 0.0
    else:
        arr = np.asarray(matrix)
        finite = bool(np.isfinite(arr).all()) if arr.size else True
        min_value = float(np.nanmin(arr)) if arr.size else 0.0
        max_value = float(np.nanmax(arr)) if arr.size else 0.0
        nnz = int(np.count_nonzero(arr)) if arr.size else 0
    return {
        "shape": shape,
        "sparse": sparse,
        "nnz": nnz,
        "finite": finite,
        "min": min_value,
        "max": max_value,
    }


def _check_key(container: Any, key: str | None, label: str, required: bool, results: list[dict[str, Any]]) -> None:
    if not key:
        return
    exists = key in container
    results.append(
        {
            "name": f"{label}:{key}",
            "ok": bool(exists),
            "required": required,
            "detail": "present" if exists else f"missing {label} key {key!r}",
        }
    )


def _validate(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    adata, source = _load_anndata(args.h5ad, args.synthetic)
    results: list[dict[str, Any]] = []

    x_summary = _matrix_summary(adata.X)
    results.append(
        {
            "name": "X",
            "ok": bool(x_summary.get("finite", False)) and len(x_summary.get("shape", ())) == 2,
            "required": True,
            "detail": x_summary,
        }
    )

    _check_key(adata.obs, args.cluster_key, "obs", True, results)
    _check_key(adata.obs, args.batch_key, "obs", False, results)
    _check_key(adata.obs, args.sample_key, "obs", False, results)
    _check_key(adata.obs, args.pseudotime_key, "obs", False, results)

    for key in args.embedding:
        _check_key(adata.obsm, key, "obsm", True, results)
        if key in adata.obsm:
            shape = tuple(int(x) for x in getattr(adata.obsm[key], "shape", ()))
            results.append(
                {
                    "name": f"obsm_shape:{key}",
                    "ok": len(shape) == 2 and shape[0] == adata.n_obs,
                    "required": True,
                    "detail": {"shape": shape, "expected_rows": int(adata.n_obs)},
                }
            )

    for key in args.layer:
        _check_key(adata.layers, key, "layers", True, results)
        if key in adata.layers:
            summary = _matrix_summary(adata.layers[key])
            results.append(
                {
                    "name": f"layer_shape:{key}",
                    "ok": tuple(summary.get("shape", ())) == (adata.n_obs, adata.n_vars)
                    and bool(summary.get("finite", False)),
                    "required": True,
                    "detail": summary,
                }
            )

    if args.require_rank_genes:
        _check_key(adata.uns, "rank_genes_groups", "uns", True, results)
    else:
        _check_key(adata.uns, "rank_genes_groups", "uns", False, results)

    if args.require_neighbors:
        _check_key(adata.obsp, "connectivities", "obsp", True, results)
    else:
        _check_key(adata.obsp, "connectivities", "obsp", False, results)

    if args.cluster_key in adata.obs:
        series = adata.obs[args.cluster_key]
        n_missing = int(series.isna().sum())
        n_unique = int(series.nunique(dropna=True))
        results.append(
            {
                "name": f"obs_values:{args.cluster_key}",
                "ok": n_missing == 0 and n_unique > 0,
                "required": True,
                "detail": {"unique_values": n_unique, "missing_values": n_missing},
            }
        )

    if args.batch_key and args.batch_key in adata.obs:
        n_batches = int(adata.obs[args.batch_key].nunique(dropna=True))
        results.append(
            {
                "name": f"batch_categories:{args.batch_key}",
                "ok": n_batches >= 2,
                "required": False,
                "detail": {
                    "unique_values": n_batches,
                    "message": "CCA/scVI-family integration expects at least two batches.",
                },
            }
        )

    if args.pseudotime_key and args.pseudotime_key in adata.obs:
        try:
            import numpy as np

            values = np.asarray(adata.obs[args.pseudotime_key], dtype=float)
            finite = bool(np.isfinite(values).all())
        except Exception:
            finite = False
        results.append(
            {
                "name": f"pseudotime_values:{args.pseudotime_key}",
                "ok": finite,
                "required": False,
                "detail": "finite numeric pseudotime" if finite else "pseudotime is not fully finite numeric",
            }
        )

    failed_required = [item for item in results if item["required"] and not item["ok"]]
    report = {
        "ok": not failed_required,
        "source": source,
        "shape": {"n_obs": int(adata.n_obs), "n_vars": int(adata.n_vars)},
        "obs_columns": list(map(str, adata.obs.columns[:50])),
        "obsm_keys": list(map(str, adata.obsm.keys())),
        "layer_keys": list(map(str, adata.layers.keys())),
        "obsp_keys": list(map(str, adata.obsp.keys())),
        "uns_keys_sample": list(map(str, list(adata.uns.keys())[:50])),
        "checks": results,
        "failed_required": [item["name"] for item in failed_required],
    }
    return report, 0 if report["ok"] else 2


def _print_text(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"single-cell input check: {status}")
    print(f"source: {report['source']}")
    print(f"shape: {report['shape']['n_obs']} cells x {report['shape']['n_vars']} features")
    print(f"obs columns sample: {', '.join(report['obs_columns']) or '(none)'}")
    print(f"obsm keys: {', '.join(report['obsm_keys']) or '(none)'}")
    print(f"layer keys: {', '.join(report['layer_keys']) or '(none)'}")
    print(f"obsp keys: {', '.join(report['obsp_keys']) or '(none)'}")
    for item in report["checks"]:
        marker = "PASS" if item["ok"] else ("FAIL" if item["required"] else "WARN")
        print(f"[{marker}] {item['name']}: {item['detail']}")
    if report["failed_required"]:
        print("failed required checks: " + ", ".join(report["failed_required"]))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.synthetic and args.h5ad:
        parser.error("do not pass an h5ad path together with --synthetic")
    report, exit_code = _validate(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
