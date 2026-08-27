#!/usr/bin/env python3
"""Tiny DFS smoke script for the deep-feature-synthesis route."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import pandas as pd

import featuretools as ft


def run_smoke() -> dict:
    es = ft.demo.load_mock_customer(return_entityset=True)
    customer_ids = list(es["customers"].index[:3])
    cutoff_df = pd.DataFrame(
        {
            "instance_id": customer_ids,
            "time": list(es["customers"]["join_date"].iloc[:3]),
            "label": [0, 1, 0],
        },
    )

    feature_matrix, features = ft.dfs(
        entityset=es,
        target_dataframe_name="customers",
        cutoff_time=cutoff_df,
        max_depth=1,
        include_cutoff_time=True,
    )
    direct_matrix = ft.calculate_feature_matrix(
        features,
        es,
        cutoff_time=cutoff_df,
        include_cutoff_time=True,
    )
    encoded_matrix, encoded_features = ft.encode_features(feature_matrix, features)
    valid_primitives = ft.get_valid_primitives(es, "customers", max_depth=1)
    temporal_cutoffs = ft.make_temporal_cutoffs(
        cutoff_df["instance_id"],
        cutoff_df["time"],
        window_size="1h",
        num_windows=2,
    )
    hours = ft.convert_time_units(7200, "hours")
    trend = ft.calculate_trend(pd.Series([1, 2, 3, 4]))

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "features.json"
        ft.save_features(features[:3], str(path))
        reloaded = ft.load_features(str(path))

    assert list(feature_matrix.columns) == list(direct_matrix.columns)
    assert feature_matrix.shape == direct_matrix.shape

    return {
        "version": ft.__version__,
        "feature_matrix_shape": list(feature_matrix.shape),
        "encoded_shape": list(encoded_matrix.shape),
        "feature_count": len(features),
        "encoded_feature_count": len(encoded_features),
        "valid_primitive_count": len(valid_primitives),
        "temporal_cutoff_rows": int(len(temporal_cutoffs)),
        "hours_conversion": hours,
        "trend": float(trend),
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
        print(f"Featuretools {result['version']} DFS smoke OK")
        print(f"Feature matrix shape: {result['feature_matrix_shape']}")
        print(f"Encoded shape: {result['encoded_shape']}")
        print(f"Feature count: {result['feature_count']}")
        print(f"Encoded feature count: {result['encoded_feature_count']}")
        print(f"Valid primitive count: {result['valid_primitive_count']}")
        print(f"Temporal cutoff rows: {result['temporal_cutoff_rows']}")
        print(f"7200 seconds in hours: {result['hours_conversion']}")
        print(f"Trend sample: {result['trend']}")
        print(f"Reloaded feature count: {result['reloaded_feature_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
