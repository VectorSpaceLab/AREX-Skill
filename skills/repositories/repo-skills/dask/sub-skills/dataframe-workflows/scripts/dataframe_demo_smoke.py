#!/usr/bin/env python3
"""Tiny public-API adaptation of Dask DataFrame demo dataset workflows."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create tiny synthetic DataFrames with dask.datasets.timeseries and "
            "dask.dataframe.demo.with_spec, then run deterministic aggregations."
        )
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic demo data.")
    parser.add_argument("--nrecords", type=_positive_int, default=24, help="Rows for the with_spec demo dataset.")
    parser.add_argument(
        "--scheduler",
        default="synchronous",
        choices=["synchronous", "threads", "processes"],
        help="Local scheduler used for compute calls.",
    )
    parser.add_argument(
        "--skip-with-spec",
        action="store_true",
        help="Only run dask.datasets.timeseries, skipping the demo.with_spec API.",
    )
    return parser


def _run(args: argparse.Namespace) -> dict[str, Any]:
    import dask
    import dask.dataframe as dd

    timeseries = dask.datasets.timeseries(
        start="2000-01-01",
        end="2000-01-03",
        freq="6h",
        partition_freq="1D",
        dtypes={"name": str, "value": float, "id": int},
        seed=args.seed,
    )
    projected = timeseries[["name", "value"]]
    summary = projected.groupby("name").value.mean(split_out=1).compute(scheduler=args.scheduler).sort_index()

    result: dict[str, Any] = {
        "ok": True,
        "timeseries_npartitions": timeseries.npartitions,
        "timeseries_known_divisions": bool(timeseries.known_divisions),
        "timeseries_columns": list(timeseries.columns),
        "timeseries_group_count": int(summary.shape[0]),
    }

    if not args.skip_with_spec:
        from dask.dataframe.io.demo import ColumnSpec, DatasetSpec, RangeIndexSpec, with_spec

        spec = DatasetSpec(
            npartitions=3,
            nrecords=args.nrecords,
            index_spec=RangeIndexSpec(dtype=int, step=1),
            column_specs=[
                ColumnSpec(prefix="amount", dtype=int, number=1, low=1, high=10, random=True),
                ColumnSpec(prefix="score", dtype=float, number=1, random=True),
                ColumnSpec(prefix="kind", dtype="category", choices=["new", "returning"]),
                ColumnSpec(prefix="name", dtype=str, choices=["Alice", "Bob"]),
            ],
        )
        demo = with_spec(spec, seed=args.seed)
        demo = demo.categorize(columns=["kind1"])
        grouped = demo.groupby("kind1").amount1.sum(split_out=1).compute(scheduler=args.scheduler).sort_index()
        result.update(
            {
                "with_spec_npartitions": demo.npartitions,
                "with_spec_known_divisions": bool(demo.known_divisions),
                "with_spec_kind_known": bool(demo["kind1"].cat.known),
                "with_spec_grouped": {str(key): int(value) for key, value in grouped.to_dict().items()},
            }
        )

    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = _run(args)
    except ModuleNotFoundError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"Missing dependency: {exc.name}",
                    "hint": "Install Dask with dataframe dependencies, including pandas and pyarrow when string conversion requires it.",
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except Exception as exc:  # pragma: no cover - diagnostic script boundary
        print(json.dumps({"ok": False, "error": repr(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
