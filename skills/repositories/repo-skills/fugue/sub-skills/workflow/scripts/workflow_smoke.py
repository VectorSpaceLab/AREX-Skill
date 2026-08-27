#!/usr/bin/env python3
"""Run a tiny Fugue workflow smoke check."""
import argparse
from typing import Sequence

import pandas as pd

from fugue import FugueWorkflow, WorkflowDataFrame, module


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        default="native",
        help="Execution engine name or alias (default: native).",
    )
    return parser


def _resolve_engine(name: str):
    if name in {"", "native"}:
        return None
    return name


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = _resolve_engine(args.engine)

    pdf = pd.DataFrame({"a": [0, 1], "b": [2, 3]})

    def add_total(df: pd.DataFrame, inc: int = 1) -> pd.DataFrame:
        return df.assign(total=df.a + df.b + inc)

    @module
    def plus_one(wf: FugueWorkflow, df: WorkflowDataFrame) -> WorkflowDataFrame:
        return df.transform(add_total, schema="*,total:int", params={"inc": 1})

    with FugueWorkflow() as dag:
        df = dag.df(pdf)
        transformed = df.transform(add_total, schema="*,total:int", params={"inc": 1})
        expected = dag.df([[0, 2, 3], [1, 3, 5]], "a:long,b:long,total:int")
        transformed.assert_eq(expected)
        plus_one(df).assert_eq(expected)
        transformed.yield_dataframe_as("result", as_local=True)

    result = dag.run(engine)
    print(f"workflow_smoke[{args.engine}]: {result['result'].as_array()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
