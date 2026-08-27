#!/usr/bin/env python3
"""Safe Vaex dataframe-core smoke check.

Creates a tiny in-memory DataFrame, exercises column inspection, non-identifier
column access, virtual columns, selections, filters, missing strings, and bounded
evaluation, then prints a JSON summary. No network, credentials, or repository
checkout is required.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _json_default(value: Any) -> Any:
    try:
        import numpy as np  # type: ignore
    except Exception:  # pragma: no cover - numpy import failure is handled elsewhere
        np = None  # type: ignore
    if np is not None:
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    if hasattr(value, "as_py"):
        return value.as_py()
    return str(value)


def run_smoke(limit: int) -> dict[str, Any]:
    import vaex

    df = vaex.from_dict(
        {
            "x": [1, 2, 3, 4],
            "with space": ["alpha", None, "gamma", ""],
            "#": [10, 20, 30, 40],
        }
    )
    df["double x"] = df.x * 2
    df["safe label"] = df["with space"].fillmissing("missing")
    df.select(df.x > 2)
    filtered = df[df.x > 1]

    n = max(0, min(limit, len(df)))
    head = df.head(n).to_records() if n else []

    summary: dict[str, Any] = {
        "ok": True,
        "vaex_version": getattr(vaex, "__version__", "unknown"),
        "shape": list(df.shape),
        "columns": df.get_column_names(),
        "real_columns": df.get_column_names(virtual=False),
        "virtual_columns": sorted(df.virtual_columns.keys()),
        "head_records": head,
        "row_count": int(df.count()),
        "selection_count": int(df.count(selection=True)),
        "missing_strings": int(df["with space"].countmissing()),
        "bounded_symbol_values": df.evaluate(df["#"], i1=0, i2=n, array_type="python"),
        "bounded_virtual_values": df.evaluate(df["double x"], i1=0, i2=n, array_type="python"),
        "filtered_default_x": filtered.evaluate("x", array_type="python"),
        "filtered_false_x": filtered.evaluate("x", filtered=False, array_type="python"),
    }

    expected = {
        "columns": ["x", "with space", "#", "double x", "safe label"],
        "shape": [4, 5],
        "selection_count": 2,
        "missing_strings": 1,
        "filtered_default_x": [2, 3, 4],
        "filtered_false_x": [1, 2, 3, 4],
    }
    for key, value in expected.items():
        if summary[key] != value:
            raise AssertionError(f"unexpected {key}: {summary[key]!r} != {value!r}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny Vaex DataFrame core smoke check and print JSON.")
    parser.add_argument("--limit", type=int, default=3, help="Number of preview rows to include in JSON output (default: 3).")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    try:
        summary = run_smoke(args.limit)
    except Exception as exc:  # keep failure machine-readable for calling agents
        failure = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        print(json.dumps(failure, indent=2 if args.pretty else None, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps(summary, default=_json_default, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
