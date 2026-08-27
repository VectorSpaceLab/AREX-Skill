#!/usr/bin/env python3
"""Cross-cutting Featuretools smoke check.

This script is safe to run in a clean CPU-only environment with the base
Featuretools install. It exercises the main public routes without needing
Graphviz, Dask, S3, or network-backed demo loaders.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import featuretools as ft
from featuretools.selection import remove_low_information_features


def run_smoke() -> dict:
    es = ft.demo.load_mock_customer(return_entityset=True)
    feature_matrix, features = ft.dfs(
        entityset=es,
        target_dataframe_name="customers",
        max_depth=1,
    )
    pruned_matrix, pruned_features = remove_low_information_features(
        feature_matrix,
        features,
    )
    primitive_catalog = ft.list_primitives()
    feature = pruned_features[0] if pruned_features else features[0]
    description = ft.describe_feature(feature)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "features.json"
        ft.save_features(pruned_features[:3] if pruned_features else features[:3], str(path))
        reloaded = ft.load_features(str(path))

    return {
        "version": ft.__version__,
        "entityset_name": es.id,
        "feature_matrix_shape": list(feature_matrix.shape),
        "pruned_shape": list(pruned_matrix.shape),
        "feature_count": len(features),
        "pruned_feature_count": len(pruned_features),
        "primitive_rows": len(primitive_catalog),
        "description": description,
        "reloaded_feature_count": len(reloaded),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the smoke result as JSON only.",
    )
    args = parser.parse_args()

    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Featuretools {result['version']} smoke OK")
        print(f"EntitySet: {result['entityset_name']}")
        print(f"Feature matrix shape: {result['feature_matrix_shape']}")
        print(f"Pruned shape: {result['pruned_shape']}")
        print(f"Feature count: {result['feature_count']}")
        print(f"Pruned feature count: {result['pruned_feature_count']}")
        print(f"Primitive catalog rows: {result['primitive_rows']}")
        print(f"Description sample: {result['description']}")
        print(f"Reloaded feature count: {result['reloaded_feature_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
