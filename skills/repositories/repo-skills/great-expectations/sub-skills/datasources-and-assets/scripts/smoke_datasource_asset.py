#!/usr/bin/env python3
"""Smoke test GX Core pandas dataframe and local CSV filesystem datasource setup."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create an ephemeral GX context, add pandas dataframe and local CSV "
            "filesystem assets, retrieve batches, and print stable JSON signals."
        )
    )
    parser.add_argument(
        "--head-rows",
        type=int,
        default=3,
        help="Number of rows to request from the CSV batch head output. Default: 3.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for the printed summary. Default: 2.",
    )
    return parser


def load_runtime_dependencies() -> tuple[Any, Any]:
    try:
        import pandas as pd
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "This smoke workflow requires pandas because it creates dataframe and CSV "
            "assets. Install GX with pandas support or add pandas to the environment."
        ) from error

    try:
        import great_expectations as gx
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "This smoke workflow requires great_expectations to be importable in the "
            "active Python environment."
        ) from error

    return pd, gx


def make_dataframe(pd: Any) -> Any:
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "amount": [10.0, 20.5, 30.0],
            "event_date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
        }
    )


def serializable_identifiers(identifiers: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {key: str(value) for key, value in identifier.items()}
        for identifier in identifiers
    ]


def main() -> int:
    args = build_parser().parse_args()
    try:
        pd, gx = load_runtime_dependencies()
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    dataframe = make_dataframe(pd)
    context = gx.get_context(mode="ephemeral")

    dataframe_datasource = context.data_sources.add_pandas(name="runtime_pandas")
    dataframe_asset = dataframe_datasource.add_dataframe_asset(name="orders_dataframe")
    dataframe_batch_definition = dataframe_asset.add_batch_definition_whole_dataframe(
        name="whole_dataframe"
    )
    dataframe_batch = dataframe_batch_definition.get_batch(
        batch_parameters={"dataframe": dataframe}
    )

    with tempfile.TemporaryDirectory(prefix="gx_datasource_smoke_") as temp_dir:
        data_dir = Path(temp_dir) / "data"
        data_dir.mkdir()
        csv_path = data_dir / "orders_2026_01.csv"
        dataframe.to_csv(csv_path, index=False)

        filesystem_datasource = context.data_sources.add_pandas_filesystem(
            name="local_csv_files",
            base_directory=data_dir,
        )
        csv_asset = filesystem_datasource.add_csv_asset(name="orders_csv")
        csv_batch_definition = csv_asset.add_batch_definition_monthly(
            name="monthly_orders",
            regex=r"orders_(?P<year>\d{4})_(?P<month>\d{2})\.csv",
        )

        batch_parameter_keys = csv_asset.get_batch_parameters_keys(
            partitioner=csv_batch_definition.partitioner
        )
        batch_identifiers = csv_batch_definition.get_batch_identifiers_list()
        csv_batch = csv_batch_definition.get_batch(
            batch_parameters={"year": "2026", "month": "01"}
        )
        csv_head = csv_batch.head(n_rows=args.head_rows).data

        summary = {
            "context_type": type(context).__name__,
            "gx_version": getattr(gx, "__version__", "unknown"),
            "datasources": sorted(context.data_sources.all().keys()),
            "dataframe_batch_columns": dataframe_batch.columns(),
            "csv_batch_columns": csv_batch.columns(),
            "csv_batch_id": csv_batch.id,
            "csv_head_rows": int(len(csv_head)),
            "csv_head_columns": list(csv_head.columns),
            "csv_batch_parameter_keys": list(batch_parameter_keys),
            "csv_batch_identifiers": serializable_identifiers(batch_identifiers),
        }

    print(json.dumps(summary, indent=args.indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
