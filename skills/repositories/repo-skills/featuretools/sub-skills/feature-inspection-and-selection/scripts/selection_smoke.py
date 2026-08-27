#!/usr/bin/env python3
"""Tiny inspection-and-selection smoke script."""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

import featuretools as ft
from featuretools.selection import (
    remove_highly_correlated_features,
    remove_highly_null_features,
    remove_low_information_features,
    remove_single_value_features,
)


class DummyFeature:
    def __init__(self, name: str):
        self._name = name
        self.number_output_features = 1

    def get_name(self) -> str:
        return self._name


def run_smoke() -> dict:
    ft.show_info()
    primitive_summary = ft.summarize_primitives()
    primitive_catalog = ft.list_primitives()

    matrix = pd.DataFrame(
        {
            "constant": [1, 1, 1, 1],
            "all_null": [None, None, None, None],
            "sparse": [1, None, None, None],
            "signal": [1, 2, 3, 4],
            "signal_clone": [1, 2, 3, 4],
            "noise": [4, 3, 2, 1],
            "inf_col": [1.0, np.inf, 2.0, -np.inf],
        },
    )
    feature_names = [DummyFeature(name) for name in matrix.columns]

    low_info_matrix, low_info_features = remove_low_information_features(matrix, feature_names)
    null_matrix, null_features = remove_highly_null_features(matrix, feature_names, pct_null_threshold=0.5)
    single_matrix, single_features = remove_single_value_features(matrix, feature_names)
    corr_matrix, corr_features = remove_highly_correlated_features(
        matrix,
        feature_names,
        pct_corr_threshold=0.95,
        features_to_keep=["signal"],
    )
    cleaned = ft.replace_inf_values(matrix, replacement_value=0, columns=["inf_col"])

    demo = ft.demo.load_mock_customer(return_single_table=True)
    es = ft.EntitySet("demo")
    es.add_dataframe(
        dataframe=demo,
        dataframe_name="customers",
        index="customer_row_id",
        make_index=True,
    )
    recommendations = ft.get_recommended_primitives(es)

    return {
        "version": ft.__version__,
        "primitive_rows": int(len(primitive_summary)),
        "primitive_catalog_rows": int(len(primitive_catalog)),
        "low_info_columns": list(low_info_matrix.columns),
        "null_columns": list(null_matrix.columns),
        "single_value_columns": list(single_matrix.columns),
        "correlated_columns": list(corr_matrix.columns),
        "cleaned_inf_values": cleaned["inf_col"].tolist(),
        "recommendation_count": len(recommendations),
        "low_info_feature_count": len(low_info_features),
        "null_feature_count": len(null_features),
        "single_feature_count": len(single_features),
        "corr_feature_count": len(corr_features),
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
        print(f"Featuretools {result['version']} inspection smoke OK")
        print(f"Primitive summary rows: {result['primitive_rows']}")
        print(f"Primitive catalog rows: {result['primitive_catalog_rows']}")
        print(f"Low-info columns: {result['low_info_columns']}")
        print(f"Null columns: {result['null_columns']}")
        print(f"Single-value columns: {result['single_value_columns']}")
        print(f"Correlated columns: {result['correlated_columns']}")
        print(f"Cleaned inf values: {result['cleaned_inf_values']}")
        print(f"Primitive recommendations: {result['recommendation_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
