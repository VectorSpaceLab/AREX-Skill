#!/usr/bin/env python3
"""Tiny primitives-and-feature-definitions smoke script."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import pandas as pd
from woodwork.column_schema import ColumnSchema
from woodwork.logical_types import NaturalLanguage

import featuretools as ft
from featuretools.feature_base import FeatureOutputSlice
from featuretools.primitives import CumSum, Sum, TransformPrimitive


class CaseCount(TransformPrimitive):
    name = "case_count"
    input_types = [ColumnSchema(logical_type=NaturalLanguage)]
    return_type = ColumnSchema(semantic_tags={"numeric"})
    number_output_features = 2

    def __init__(self, marker="case"):
        self.marker = marker

    def get_function(self):
        def case_count(column):
            upper = pd.Series([sum(ch.isupper() for ch in text) for text in column])
            lower = pd.Series([sum(ch.islower() for ch in text) for text in column])
            return upper, lower

        return case_count

    def generate_names(self, base_feature_names):
        name = self.generate_name(base_feature_names)
        return f"{name}[upper]", f"{name}[lower]"


def build_entityset() -> ft.EntitySet:
    customers = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "quote": ["Hello World", "Featuretools Rocks"],
            "age": [30, 40],
        },
    )
    sessions = pd.DataFrame(
        {
            "session_id": [10, 11, 12],
            "customer_id": [1, 1, 2],
            "amount": [5.0, 7.5, 3.0],
            "group_key": ["A", "A", "B"],
        },
    )

    es = ft.EntitySet("demo")
    es.add_dataframe(
        dataframe=customers,
        dataframe_name="customers",
        index="customer_id",
        logical_types={"quote": NaturalLanguage},
    )
    es.add_dataframe(
        dataframe=sessions,
        dataframe_name="sessions",
        index="session_id",
    )
    es.add_relationship(
        parent_dataframe_name="customers",
        parent_column_name="customer_id",
        child_dataframe_name="sessions",
        child_column_name="customer_id",
    )
    return es


def run_smoke() -> dict:
    es = build_entityset()

    quote_feat = ft.IdentityFeature(es["customers"].ww["quote"])
    age_feat = ft.IdentityFeature(es["customers"].ww["age"])
    direct_feat = ft.DirectFeature(age_feat, "sessions")
    agg_feat = ft.AggregationFeature(
        ft.IdentityFeature(es["sessions"].ww["amount"]),
        "customers",
        Sum,
    )
    groupby_feat = ft.GroupByTransformFeature(
        ft.IdentityFeature(es["sessions"].ww["amount"]),
        CumSum,
        ft.IdentityFeature(es["sessions"].ww["customer_id"]),
    )
    transform_feat = ft.TransformFeature(quote_feat, CaseCount(marker="demo"))
    upper_slice = transform_feat[0]

    feature_list = [quote_feat, direct_feat, agg_feat, groupby_feat, transform_feat]
    descriptions = [ft.describe_feature(feat) for feat in feature_list]
    slice_description = ft.describe_feature(upper_slice)
    assert isinstance(upper_slice, FeatureOutputSlice)

    graph_available = False
    try:
        import graphviz  # noqa: F401
    except Exception:
        pass
    else:
        graph_available = True
        graph = ft.graph_feature(transform_feat)
        graph_available = graph.__class__.__name__ == "Digraph"

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "features.json"
        ft.save_features(feature_list + [upper_slice], str(path))
        loaded = ft.load_features(str(path))

    return {
        "version": ft.__version__,
        "feature_count": len(feature_list),
        "loaded_count": len(loaded),
        "graph_available": graph_available,
        "direct_name": direct_feat.get_name(),
        "agg_name": agg_feat.get_name(),
        "groupby_name": groupby_feat.get_name(),
        "transform_name": transform_feat.get_name(),
        "slice_name": upper_slice.get_name(),
        "depth": agg_feat.get_depth(),
        "dependency_count": len(agg_feat.get_dependencies(deep=True, ignored=None)),
        "description_sample": descriptions[0],
        "slice_description": slice_description,
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
        print(f"Featuretools {result['version']} primitives smoke OK")
        print(f"Feature count: {result['feature_count']}")
        print(f"Loaded feature count: {result['loaded_count']}")
        print(f"Graph available: {result['graph_available']}")
        print(f"Direct feature: {result['direct_name']}")
        print(f"Aggregation feature: {result['agg_name']}")
        print(f"Group-by feature: {result['groupby_name']}")
        print(f"Transform feature: {result['transform_name']}")
        print(f"Slice feature: {result['slice_name']}")
        print(f"Depth: {result['depth']}")
        print(f"Dependency count: {result['dependency_count']}")
        print(f"Description sample: {result['description_sample']}")
        print(f"Slice description: {result['slice_description']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
