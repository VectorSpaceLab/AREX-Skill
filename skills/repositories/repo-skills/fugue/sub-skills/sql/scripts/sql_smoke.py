#!/usr/bin/env python3
"""Run a tiny FugueSQL smoke check."""
import argparse
from typing import Sequence

import pandas as pd

import fugue.api as fa


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        default="duckdb",
        help="Execution engine alias to try first (default: duckdb).",
    )
    return parser


def _resolve_engine(name: str):
    if name in {"", "native"}:
        return None
    return name


def _run_query(engine, label: str) -> None:
    pdf = pd.DataFrame({"a": [0, 1], "b": [2, 3]})
    res = fa.fugue_sql(
        "SELECT a, b FROM pdf WHERE a < {{limit}}",
        pdf=pdf,
        limit=1,
        engine=engine,
        as_fugue=True,
    )
    print(f"fugue_sql[{label}]: {res.as_array()}")

    raw = fa.raw_sql("SELECT * FROM", pdf, "WHERE a < 1", engine=engine, as_fugue=True)
    print(f"raw_sql[{label}]: {raw.as_array()}")

    flow = fa.fugue_sql_flow(
        """
        CREATE [[0], [1]] SCHEMA a:int
        YIELD DATAFRAME AS result
        """
    )
    result = flow.run(engine)
    print(f"fugue_sql_flow[{label}]: {result['result'].as_array()}")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = _resolve_engine(args.engine)
    try:
        _run_query(engine, args.engine)
    except Exception as first_exc:
        if engine is not None:
            print(f"sql smoke with {args.engine} failed, retrying on native: {first_exc}")
            _run_query(None, "native")
        else:
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
