#!/usr/bin/env python3
"""Build a tiny Great Expectations suite from an in-memory dataframe.

The default mode builds and summarizes an ExpectationSuite. Pass --validate to
validate the suite against the tiny dataframe using an ephemeral GX context.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a tiny GX ExpectationSuite and optionally validate it against a dataframe.",
    )
    parser.add_argument(
        "--suite-name",
        default="orders_dataframe_quality",
        help="Name for the generated ExpectationSuite. Default: %(default)s",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the suite against the bundled tiny dataframe using an ephemeral context.",
    )
    parser.add_argument(
        "--max-discount-pct",
        type=float,
        default=0.30,
        help="Runtime parameter value for the parameterized discount expectation. Default: %(default)s",
    )
    parser.add_argument(
        "--result-format",
        choices=["BOOLEAN_ONLY", "BASIC", "SUMMARY", "COMPLETE"],
        default="SUMMARY",
        help="GX result format to use when --validate is passed. Default: %(default)s",
    )
    parser.add_argument(
        "--show-json",
        action="store_true",
        help="Print the suite configuration as JSON when possible.",
    )
    return parser.parse_args()


def import_dependencies():
    try:
        import pandas as pd
        import great_expectations as gx
        from great_expectations.expectations.row_conditions import Column
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"Missing dependency: {exc.name}. Install Great Expectations with its pandas dependencies "
            "before running this helper."
        ) from exc
    return gx, pd, Column


def make_dataframe(pd):
    return pd.DataFrame(
        {
            "order_id": [1001, 1002, 1003, 1004],
            "status": ["new", "paid", "shipped", "cancelled"],
            "amount": [25.0, 80.5, 120.0, 10.0],
            "discount_pct": [0.00, 0.10, 0.20, 0.00],
            "country": ["US", "US", "CA", "US"],
        }
    )


def build_suite(gx, Column, suite_name: str, context):
    class ExpectValidOrderAmount(gx.expectations.ExpectColumnValuesToBeBetween):
        column: str = "amount"
        min_value: float = 0.0
        max_value: float = 10000.0
        mostly: float = 1.0
        severity: str = "critical"
        description: str = "Order amount must be non-negative and below the business safety cap."

    suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="order_id",
            severity="critical",
            notes="Every row needs a stable order identifier.",
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="status",
            value_set=["new", "paid", "shipped", "cancelled"],
            severity="warning",
            meta={"rule_family": "status-vocabulary"},
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="discount_pct",
            min_value=0,
            max_value={"$PARAMETER": "max_discount_pct"},
            mostly=1.0,
            row_condition=Column("status").is_in(["paid", "shipped"]),
            severity="warning",
            notes="Discount limits only apply after an order leaves the new/cancelled states.",
        )
    )
    suite.add_expectation(ExpectValidOrderAmount())
    return suite


def suite_to_jsonable(suite) -> dict[str, Any]:
    if hasattr(suite, "to_json_dict"):
        return suite.to_json_dict()
    if hasattr(suite, "dict"):
        return suite.dict()
    return {"name": suite.name, "expectations": [str(exp) for exp in suite.expectations]}


def validate_suite(context, dataframe, suite, expectation_parameters: dict[str, Any], result_format: str):
    asset = context.data_sources.pandas_default.add_dataframe_asset("orders_dataframe")
    batch_definition = asset.add_batch_definition_whole_dataframe("orders_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": dataframe})
    return batch.validate(
        suite,
        expectation_parameters=expectation_parameters,
        result_format=result_format,
    )


def main() -> int:
    args = parse_args()
    gx, pd, Column = import_dependencies()
    context = gx.get_context(mode="ephemeral")
    dataframe = make_dataframe(pd)
    suite = build_suite(gx, Column, args.suite_name, context)
    expectation_parameters = {"max_discount_pct": args.max_discount_pct}

    print(f"suite_name={suite.name}")
    print(f"expectation_count={len(suite.expectations)}")
    print("required_expectation_parameters=" + json.dumps(expectation_parameters, sort_keys=True))

    if args.show_json:
        print(json.dumps(suite_to_jsonable(suite), indent=2, sort_keys=True, default=str))

    if args.validate:
        result = validate_suite(
            context=context,
            dataframe=dataframe,
            suite=suite,
            expectation_parameters=expectation_parameters,
            result_format=args.result_format,
        )
        print(f"validation_success={bool(result.success)}")
        statistics = getattr(result, "statistics", None)
        if statistics is not None:
            print("statistics=" + json.dumps(statistics, sort_keys=True, default=str))
        return 0 if result.success else 1

    print("validation_skipped=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
