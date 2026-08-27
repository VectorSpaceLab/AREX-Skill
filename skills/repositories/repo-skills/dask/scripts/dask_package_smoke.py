#!/usr/bin/env python3
"""Small Dask package smoke check for generated skill users."""

from __future__ import annotations

import argparse

import dask
from dask import delayed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny Dask import, delayed, and scheduler smoke check.")
    parser.add_argument(
        "--scheduler",
        default="synchronous",
        choices=["synchronous", "sync", "threads", "threading", "processes", "multiprocessing"],
        help="Local scheduler to use for the tiny delayed computation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    @delayed
    def inc(value: int) -> int:
        return value + 1

    total = dask.delayed(sum)([inc(1), inc(2), inc(3)])
    result = total.compute(scheduler=args.scheduler)
    if result != 9:
        raise AssertionError(f"unexpected delayed result: {result!r}")
    graph = total.__dask_graph__()
    print(f"dask={dask.__version__}")
    print(f"scheduler={args.scheduler}")
    print(f"graph_tasks={len(graph)}")
    print(f"result={result}")


if __name__ == "__main__":
    main()
