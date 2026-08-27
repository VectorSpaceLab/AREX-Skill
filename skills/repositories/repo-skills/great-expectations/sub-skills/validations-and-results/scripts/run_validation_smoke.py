#!/usr/bin/env python3
"""Run a tiny local Great Expectations validation smoke test."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> str:
    return str(value)


def run_smoke(result_format: str) -> int:
    try:
        import pandas as pd
        import great_expectations as gx
    except Exception as exc:  # noqa: BLE001
        print(f"IMPORT_ERROR: {exc}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="gx-validation-smoke-") as tmpdir:
        csv_path = Path(tmpdir) / "orders.csv"
        pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["alpha", "beta", "gamma"],
            }
        ).to_csv(csv_path, index=False)

        context = gx.get_context(mode="ephemeral")
        batch_definition = (
            context.data_sources.add_pandas_filesystem(
                name="validation_smoke_source",
                base_directory=tmpdir,
            )
            .add_csv_asset(name="validation_smoke_asset")
            .add_batch_definition_path(
                name="validation_smoke_batch",
                path="orders.csv",
            )
        )

        suite = gx.ExpectationSuite(name="validation_smoke_suite")
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="id"))
        suite.add_expectation(
            gx.expectations.ExpectTableRowCountToBeBetween(min_value=1, max_value=10)
        )
        suite = context.suites.add(suite)

        validation_definition = context.validation_definitions.add(
            gx.ValidationDefinition(
                name="validation_smoke_definition",
                data=batch_definition,
                suite=suite,
            )
        )

        result = validation_definition.run(result_format=result_format)

    payload = {
        "success": result.success,
        "statistics": result.statistics,
        "suite_name": result.suite_name,
        "evaluated_expectation_types": [
            evr.expectation_config.type for evr in result.results
        ],
    }
    print(json.dumps(payload, indent=2, default=_json_default))
    return 0 if result.success else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the installed Great Expectations Python API with a tiny "
            "temporary CSV and pandas-filesystem workflow. No network, "
            "credentials, or external services are used."
        )
    )
    parser.add_argument(
        "--result-format",
        choices=["BOOLEAN_ONLY", "BASIC", "SUMMARY", "COMPLETE"],
        default="SUMMARY",
        help="GX result format to request for the smoke validation.",
    )
    args = parser.parse_args()
    return run_smoke(result_format=args.result_format)


if __name__ == "__main__":
    raise SystemExit(main())
