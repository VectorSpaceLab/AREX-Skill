#!/usr/bin/env python3
"""Tiny DataChain Query Engine smoke test.

Purpose: verify that an installed DataChain package can execute a safe local
Query Engine chain using read_values, mutate, filter, group_by, and order_by.

Example:
    python query_smoke.py
    python query_smoke.py --show-rows
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny DataChain Query Engine smoke test over read_values. "
            "No files, network, credentials, or repository checkout are required."
        )
    )
    parser.add_argument(
        "--show-rows",
        action="store_true",
        help="Print the selected and grouped result rows as JSON.",
    )
    return parser


def import_datachain():
    try:
        import datachain as dc  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "Could not import datachain. Install DataChain in the active Python "
            "environment before running this smoke test."
        ) from exc
    return dc


def run_smoke(show_rows: bool = False) -> dict[str, Any]:
    dc = import_datachain()

    chain = dc.read_values(
        name=["alpha.txt", "beta.jpg", "alpine.jpg", "gamma.txt"],
        score=[1, 2, 3, 4],
        grp=["a", "b", "a", "b"],
        in_memory=True,
    )

    transformed = chain.mutate(
        ext=dc.func.path.file_ext("name"),
        score2=dc.C("score") * 2,
        label=dc.func.ifelse(dc.C("score") >= 3, "high", "low"),
    )
    filtered = transformed.filter(dc.C("score2") >= 4)

    selected_rows = filtered.order_by("score").select(
        "name", "ext", "score2", "label", "grp"
    ).to_list("name", "ext", "score2", "label", "grp")
    expected_selected = [
        ("beta.jpg", "jpg", 4, "low", "b"),
        ("alpine.jpg", "jpg", 6, "high", "a"),
        ("gamma.txt", "txt", 8, "high", "b"),
    ]
    assert selected_rows == expected_selected, selected_rows

    grouped_rows = (
        filtered.group_by(
            total=dc.func.sum("score2"),
            rows=dc.func.count(),
            partition_by="grp",
        )
        .order_by("grp")
        .to_list("grp", "total", "rows")
    )
    expected_grouped = [("a", 6, 1), ("b", 12, 2)]
    assert grouped_rows == expected_grouped, grouped_rows

    summary = {
        "input_rows": chain.count(),
        "filtered_rows": filtered.count(),
        "selected_rows": selected_rows,
        "grouped_rows": grouped_rows,
    }

    if show_rows:
        print(json.dumps(summary, indent=2))
    else:
        print("DataChain query smoke passed")
    return summary


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_smoke(show_rows=args.show_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
