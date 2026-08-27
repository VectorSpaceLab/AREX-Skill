#!/usr/bin/env python3
"""Summarize JSONL metrics written by post-training stages.

Read-only: the script opens a metrics JSONL file, reports columns, the last valid row,
and min/max for numeric fields. Use --demo for tiny built-in fixture behavior.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

DEMO_ROWS = [
    {"step": 0, "train_loss": 1.25, "lr": 1e-5},
    {"step": 20, "train_loss": 0.95, "lr": 9e-6, "dev_loss": 1.10},
    {"step": 40, "train_loss": 0.80, "lr": 8e-6, "dev_loss": 1.02, "note": "demo"},
]


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"warning: skip invalid JSON line {lineno}: {exc}", file=sys.stderr)
                continue
            if not isinstance(row, dict):
                print(f"warning: skip non-object JSON line {lineno}", file=sys.stderr)
                continue
            yield lineno, row


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def summarize(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, Any]:
    columns: Counter[str] = Counter()
    types: dict[str, Counter[str]] = defaultdict(Counter)
    numeric: dict[str, dict[str, float]] = {}
    first_line = rows[0][0] if rows else None
    last_line = rows[-1][0] if rows else None

    for _, row in rows:
        for key, value in row.items():
            columns[key] += 1
            types[key][type(value).__name__] += 1
            if is_number(value):
                v = float(value)
                if key not in numeric:
                    numeric[key] = {"min": v, "max": v}
                else:
                    numeric[key]["min"] = min(numeric[key]["min"], v)
                    numeric[key]["max"] = max(numeric[key]["max"], v)

    return {
        "rows": len(rows),
        "first_line": first_line,
        "last_line": last_line,
        "columns": columns,
        "types": types,
        "numeric": numeric,
        "last_row": rows[-1][1] if rows else None,
    }


def print_summary(summary: dict[str, Any], *, json_output: bool = False) -> None:
    if json_output:
        serializable = {
            "rows": summary["rows"],
            "first_line": summary["first_line"],
            "last_line": summary["last_line"],
            "columns": dict(summary["columns"]),
            "types": {k: dict(v) for k, v in summary["types"].items()},
            "numeric": summary["numeric"],
            "last_row": summary["last_row"],
        }
        print(json.dumps(serializable, indent=2, sort_keys=True))
        return

    print(f"rows: {summary['rows']}")
    if summary["rows"] == 0:
        print("no valid JSON object rows found")
        return
    print(f"line range: {summary['first_line']}..{summary['last_line']}")

    print("\ncolumns:")
    for key, count in sorted(summary["columns"].items()):
        type_bits = ", ".join(f"{name}:{n}" for name, n in sorted(summary["types"][key].items()))
        print(f"  {key}: present {count}/{summary['rows']} ({type_bits})")

    print("\nnumeric min/max:")
    if not summary["numeric"]:
        print("  none")
    else:
        for key, mm in sorted(summary["numeric"].items()):
            print(f"  {key}: min={mm['min']:.6g} max={mm['max']:.6g}")

    print("\nlast row:")
    print(json.dumps(summary["last_row"], indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Summarize a post-training JSONL metrics file without modifying it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("path", nargs="?", help="metrics JSONL file")
    p.add_argument("--demo", action="store_true", help="summarize a built-in tiny fixture")
    p.add_argument("--max-rows", type=int, default=0, help="read at most this many valid rows; 0 means all")
    p.add_argument("--json", action="store_true", help="emit machine-readable summary JSON")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.demo:
        rows = list(enumerate(DEMO_ROWS, 1))
    else:
        if not args.path:
            raise SystemExit("provide a JSONL path or use --demo")
        path = Path(args.path)
        if not path.exists():
            raise SystemExit(f"metrics file not found: {path}")
        rows = list(iter_jsonl(path))

    if args.max_rows and args.max_rows > 0:
        rows = rows[: args.max_rows]
    print_summary(summarize(rows), json_output=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
