#!/usr/bin/env python3
"""Smoke-check Dask delayed, graph inspection, tokenization, and schedulers."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

import dask
from dask.core import get_dependencies, istask
from dask.highlevelgraph import HighLevelGraph
from dask.tokenize import tokenize


def scale(value: int, factor: int) -> int:
    return value * factor


def add_offset(value: int, offset: int) -> int:
    return value + offset


def combine(values: Sequence[int]) -> int:
    return sum(values)


def build_graph(items: int, factor: int, offset: int) -> Any:
    with dask.annotate(priority=5, retries=1):
        scaled = [dask.delayed(scale, pure=True)(item, factor) for item in range(items)]
    adjusted = [dask.delayed(add_offset, pure=True)(value, offset) for value in scaled]
    return dask.delayed(combine, pure=True)(adjusted)


def summarize_graph(node: Any) -> dict[str, Any]:
    graph = node.__dask_graph__()
    summary: dict[str, Any] = {
        "result_key": str(node.key),
        "graph_type": type(graph).__name__,
        "dask_keys": [str(key) for key in node.__dask_keys__()],
        "token": tokenize(node.key, node.__dask_keys__()),
    }

    if isinstance(graph, HighLevelGraph):
        summary["layers"] = list(graph.layers)
        summary["layer_dependencies"] = {
            name: sorted(dependencies) for name, dependencies in graph.dependencies.items()
        }
        low_level = graph.to_dict()
    else:
        low_level = dict(graph)

    summary["task_count"] = len(low_level)
    summary["sample_dependencies"] = {
        str(key): sorted(str(dep) for dep in get_dependencies(low_level, key))
        for key in list(low_level)[: min(5, len(low_level))]
    }
    summary["sample_task_flags"] = {
        str(key): istask(task) for key, task in list(low_level.items())[: min(5, len(low_level))]
    }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a tiny Dask delayed graph, inspect it, and compute it."
    )
    parser.add_argument(
        "--scheduler",
        choices=("synchronous", "threads", "processes"),
        default="synchronous",
        help="Local scheduler to use for final compute. Use synchronous for debugging.",
    )
    parser.add_argument("--items", type=int, default=5, help="Number of delayed input tasks.")
    parser.add_argument("--factor", type=int, default=2, help="Multiplier used by each input task.")
    parser.add_argument("--offset", type=int, default=1, help="Offset added after scaling.")
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Optional worker count for threads or processes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.items < 1:
        raise SystemExit("--items must be at least 1")

    final = build_graph(args.items, args.factor, args.offset)
    graph_summary = summarize_graph(final)
    result = final.compute(scheduler=args.scheduler, num_workers=args.num_workers)
    expected = sum(item * args.factor + args.offset for item in range(args.items))

    payload = {
        "ok": result == expected,
        "scheduler": args.scheduler,
        "result": result,
        "expected": expected,
        "graph": graph_summary,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if result != expected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
