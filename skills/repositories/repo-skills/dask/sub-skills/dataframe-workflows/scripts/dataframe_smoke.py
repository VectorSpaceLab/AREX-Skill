#!/usr/bin/env python3
"""Tiny Dask DataFrame smoke workflow for generated repo skill users."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny pandas-backed Dask DataFrame, exercise partitions, "
            "metadata-aware map_partitions, groupby, joins, CSV IO, and optional Parquet IO."
        )
    )
    parser.add_argument("--npartitions", type=_positive_int, default=2, help="Number of Dask partitions to create.")
    parser.add_argument(
        "--scheduler",
        default="synchronous",
        choices=["synchronous", "threads", "processes"],
        help="Local scheduler used for the final compute calls.",
    )
    parser.add_argument(
        "--parquet",
        action="store_true",
        help="Also write/read a temporary Parquet dataset. Requires pyarrow.",
    )
    parser.add_argument(
        "--keep-output",
        type=Path,
        default=None,
        help="Optional directory for output fixtures. Defaults to an auto-cleaned temporary directory.",
    )
    return parser


def add_double(part: Any) -> Any:
    out = part.reset_index().assign(double=lambda frame: frame["value"] * 2)
    return out[["id", "value", "double", "label"]]


def _run(base_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    import pandas as pd
    import dask.dataframe as dd

    pdf = pd.DataFrame(
        {
            "id": [1, 2, 1, 3, 2, 3],
            "value": [10, 20, 30, 40, 50, 60],
            "label": ["a", "b", "a", "c", "b", "c"],
        }
    ).set_index("id")

    df = dd.from_pandas(pdf, npartitions=args.npartitions, sort=True)

    meta = pd.DataFrame(
        {
            "id": pd.Series(dtype=pdf.index.dtype),
            "value": pd.Series(dtype="int64"),
            "double": pd.Series(dtype="int64"),
            "label": pd.Series(dtype="object"),
        }
    )

    enriched = df.map_partitions(add_double, meta=meta, clear_divisions=True)
    grouped = enriched.groupby("label").value.sum(split_out=1)

    lookup = pd.DataFrame({"label": ["a", "b", "c"], "name": ["alpha", "beta", "gamma"]})
    joined = enriched.merge(lookup, on="label", how="left")

    csv_dir = base_dir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / "input.csv"
    pdf.reset_index().to_csv(csv_path, index=False)
    csv_df = dd.read_csv(csv_path, dtype={"id": "int64", "value": "int64", "label": "object"})
    csv_total = int(csv_df.value.sum().compute(scheduler=args.scheduler))

    parquet_summary: dict[str, Any] | None = None
    if args.parquet:
        parquet_dir = base_dir / "parquet"
        joined.to_parquet(parquet_dir, write_index=False, engine="pyarrow")
        parquet_df = dd.read_parquet(parquet_dir, columns=["label", "value", "name"])
        parquet_summary = {
            "rows": int(parquet_df.shape[0].compute(scheduler=args.scheduler)),
            "columns": list(parquet_df.columns),
        }

    grouped_result = grouped.compute(scheduler=args.scheduler).sort_index()
    joined_result = joined.compute(scheduler=args.scheduler).sort_values(["label", "value"]).reset_index(drop=True)

    return {
        "ok": True,
        "npartitions": df.npartitions,
        "known_divisions": bool(df.known_divisions),
        "divisions": [None if item is None else int(item) for item in df.divisions],
        "grouped": grouped_result.to_dict(),
        "joined_names": joined_result["name"].tolist(),
        "csv_total": csv_total,
        "parquet": parquet_summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.keep_output is not None:
            args.keep_output.mkdir(parents=True, exist_ok=True)
            summary = _run(args.keep_output, args)
        else:
            with TemporaryDirectory(prefix="dask-dataframe-smoke-") as tmp:
                summary = _run(Path(tmp), args)
    except ModuleNotFoundError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"Missing dependency: {exc.name}",
                    "hint": "Install Dask with dataframe dependencies; add pyarrow for --parquet.",
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
