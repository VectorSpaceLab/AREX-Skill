#!/usr/bin/env python3
"""Demonstrate anndata accessors and extension namespaces on a tiny AnnData object."""

import argparse
import json
from collections.abc import Iterable

import numpy as np
import pandas as pd

import anndata as ad
from anndata import AnnData
from anndata.acc import A, AdRef


def make_adata() -> AnnData:
    obs = pd.DataFrame(
        {"batch": ["a", "a", "b"], "quality": [0.95, 0.80, 0.60]},
        index=pd.Index(["cell-a", "cell-b", "cell-c"], name="cell"),
    )
    var = pd.DataFrame(
        {"symbol": ["GNA", "GNB", "GNC"]},
        index=pd.Index(["gene-a", "gene-b", "gene-c"], name="gene"),
    )
    x = np.arange(9, dtype=float).reshape(3, 3)
    adata = AnnData(
        X=x,
        obs=obs,
        var=var,
        layers={"counts": x.astype(int) + 1},
        obsm={"pca": np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])},
        varm={"loadings": np.array([[1.0, 0.0], [0.5, 0.5], [0.0, 1.0]])},
        obsp={"neighbors": np.eye(3)},
    )
    return adata


@ad.register_anndata_namespace("disco_demo")
class DisCoDemoNamespace:
    def __init__(self, adata: AnnData) -> None:
        self._adata = adata

    def missing(self, refs: Iterable[AdRef]) -> list[str]:
        return [str(ref) for ref in refs if ref not in self._adata]

    def require_obs_column(self, key: str) -> str:
        ref = A.obs[key]
        if ref not in self._adata:
            raise KeyError(f"Missing required reference: {ref}")
        return f"{ref} is present"


def summarize_value(value: object) -> object:
    if hasattr(value, "tolist"):
        return value.tolist()
    return str(value)


def run_demo() -> dict[str, object]:
    adata = make_adata()
    refs = [
        A.obs["batch"],
        A.var["symbol"],
        A.obsm["pca"][:, 1],
        A.layers["counts"][:, "gene-b"],
        A.obsp["neighbors"][:, "cell-a"],
    ]
    missing_ref = A.obs["missing"]

    extracted = {str(ref): summarize_value(adata[ref]) for ref in refs}
    payload = A.to_json(A.layers["counts"][:, "gene-b"])
    roundtrip_ref = A.from_json(payload)
    resolved_ref = A.resolve("obsm.pca.1")

    return {
        "shape": list(adata.shape),
        "refs": [
            {
                "repr": repr(ref),
                "dims": sorted(ref.dims),
                "present": ref in adata,
            }
            for ref in refs
        ],
        "missing": str(missing_ref),
        "missing_present": missing_ref in adata,
        "extracted": extracted,
        "json_payload": payload,
        "json_roundtrip": str(roundtrip_ref),
        "resolved_string": str(resolved_ref),
        "namespace_missing": adata.disco_demo.missing([*refs, missing_ref]),
        "namespace_validation": adata.disco_demo.require_obs_column("batch"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny AnnData object, demonstrate anndata.acc references, "
            "membership/extraction, JSON/string parsing, and a demo extension namespace."
        )
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation.",
    )
    args = parser.parse_args()
    result = run_demo()
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
