#!/usr/bin/env python3
"""Tiny EntitySet smoke script for the entitysets-and-data route."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import pandas as pd

import featuretools as ft


def build_base_entityset() -> ft.EntitySet:
    customers = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "signup_time": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "segment": ["gold", "silver"],
        },
    )
    sessions = pd.DataFrame(
        {
            "session_id": [10, 11, 12],
            "customer_id": [1, 1, 2],
            "session_start": pd.to_datetime(
                ["2024-01-03 09:00", "2024-01-03 13:00", "2024-01-04 08:30"],
            ),
            "session_end": pd.to_datetime(
                ["2024-01-03 09:10", "2024-01-03 13:20", "2024-01-04 08:50"],
            ),
            "device_type": ["web", "mobile", "web"],
        },
    )

    es = ft.EntitySet("shop")
    es.add_dataframe(
        dataframe=customers,
        dataframe_name="customers",
        index="customer_id",
        time_index="signup_time",
    )
    es.add_dataframe(
        dataframe=sessions,
        dataframe_name="sessions",
        index="session_id",
        time_index="session_start",
    )
    es.add_relationship(
        parent_dataframe_name="customers",
        parent_column_name="customer_id",
        child_dataframe_name="sessions",
        child_column_name="customer_id",
    )
    return es


def build_normalized_entityset() -> ft.EntitySet:
    es = build_base_entityset()
    es.normalize_dataframe(
        base_dataframe_name="sessions",
        new_dataframe_name="devices",
        index="device_type",
        additional_columns=["session_end"],
        make_time_index=False,
    )
    return es


def maybe_plot(es: ft.EntitySet, tmpdir: str) -> bool:
    try:
        import graphviz  # noqa: F401
    except Exception:
        return False

    output = Path(tmpdir) / "entityset_plot.png"
    es.plot(to_file=str(output))
    return output.exists()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the smoke result as JSON only.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Attempt an optional Graphviz plot smoke when graphviz is installed.",
    )
    args = parser.parse_args()

    es = build_base_entityset()
    _forward_dataframes = list(es.get_forward_dataframes("customers", deep=True))
    customer_rows = es.query_by_values("sessions", [1], column_name="customer_id")

    normalized_es = build_normalized_entityset()
    normalized_tables = list(normalized_es.dataframe_dict.keys())

    with tempfile.TemporaryDirectory() as tmpdir:
        pickle_dir = Path(tmpdir) / "pickle"
        csv_dir = Path(tmpdir) / "csv"
        es.set_secondary_time_index("sessions", {"session_end": ["session_end"]})
        es.to_pickle(str(pickle_dir))
        es.to_csv(str(csv_dir))
        reloaded_pickle = ft.read_entityset(str(pickle_dir))
        reloaded_csv = ft.read_entityset(str(csv_dir))
        plot_written = maybe_plot(es, tmpdir) if args.plot else False

    result = {
        "entityset_name": es.id,
        "dataframes": list(es.dataframe_dict.keys()),
        "relationships": len(es.relationships),
        "query_rows": int(len(customer_rows)),
        "normalized_tables": normalized_tables,
        "pickle_dataframes": list(reloaded_pickle.dataframe_dict.keys()),
        "csv_dataframes": list(reloaded_csv.dataframe_dict.keys()),
        "plot_written": plot_written,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"EntitySet smoke OK: {result['entityset_name']}")
        print(f"Dataframes: {result['dataframes']}")
        print(f"Relationships: {result['relationships']}")
        print(f"Query rows for customer 1: {result['query_rows']}")
        print(f"Reloaded pickle dataframes: {result['pickle_dataframes']}")
        print(f"Reloaded csv dataframes: {result['csv_dataframes']}")
        print(f"Plot written: {result['plot_written']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
