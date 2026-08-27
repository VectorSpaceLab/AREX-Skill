#!/usr/bin/env python3
"""Inspect metrics JSONL files without repo imports or pandas.

Each valid metrics line should be a JSON object, typically containing keys such
as step, wall, train_loss, lr, reward, kl_ref, or gsm8k_acc. This helper counts
valid rows and malformed lines, reports observed columns, prints the last valid
row, and summarizes numeric min/max values. It is read-only for user-supplied
paths; --demo uses a tiny temporary fixture.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[tuple[int, str]], int]:
    rows: list[dict[str, Any]] = []
    malformed: list[tuple[int, str]] = []
    total_lines = 0
    try:
        fh = path.open("r", encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc

    with fh:
        for lineno, line in enumerate(fh, start=1):
            total_lines = lineno
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                malformed.append((lineno, exc.msg))
                continue
            if not isinstance(obj, dict):
                malformed.append((lineno, f"expected object, got {type(obj).__name__}"))
                continue
            rows.append(obj)
    return rows, malformed, total_lines


def _summarize(label: str, rows: list[dict[str, Any]], malformed: list[tuple[int, str]], total_lines: int, *, sample: int) -> None:
    print(f"## {label}")
    print(f"total lines: {total_lines}")
    print(f"valid rows: {len(rows)}")
    print(f"malformed/non-object lines: {len(malformed)}")
    if malformed:
        print("malformed examples:")
        for lineno, msg in malformed[:sample]:
            print(f"  - line {lineno}: {msg}")

    if not rows:
        print("no valid JSON object rows found\n")
        return

    columns: Counter[str] = Counter()
    types: dict[str, Counter[str]] = defaultdict(Counter)
    numeric: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for key, value in row.items():
            columns[key] += 1
            types[key][type(value).__name__] += 1
            if _is_number(value):
                numeric[key].append(float(value))

    print("columns:")
    for key in sorted(columns):
        type_bits = ", ".join(f"{name}:{count}" for name, count in sorted(types[key].items()))
        numeric_count = len(numeric.get(key, []))
        suffix = f", numeric={numeric_count}" if numeric_count else ""
        print(f"  - {key}: present={columns[key]}/{len(rows)} ({type_bits}{suffix})")

    print("last row:")
    for key in sorted(rows[-1]):
        print(f"  - {key}: {_fmt(rows[-1][key])}")

    if numeric:
        print("numeric min/max:")
        for key in sorted(numeric):
            vals = numeric[key]
            print(f"  - {key}: min={_fmt(min(vals))}, max={_fmt(max(vals))}, last_numeric={_fmt(vals[-1])}")
    else:
        print("numeric min/max: none")
    print()


def _write_demo_file(path: Path) -> None:
    lines = [
        {"step": 0, "wall": 100.0, "train_loss": 2.5, "lr": 1e-5},
        {"step": 20, "wall": 120.0, "train_loss": 2.1, "lr": 9e-6, "dev_loss": 2.3},
        "not valid json",
        {"step": 40, "wall": 140.0, "train_loss": 1.9, "lr": 8e-6, "note": "demo"},
        ["not", "an", "object"],
    ]
    with path.open("w", encoding="utf-8") as fh:
        for item in lines:
            if isinstance(item, str):
                fh.write(item + "\n")
            else:
                fh.write(json.dumps(item) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize metrics JSONL columns, last row, malformed lines, and numeric min/max.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("paths", nargs="*", type=Path, help="metrics JSONL file(s) to inspect")
    parser.add_argument("--sample-malformed", type=int, default=5, help="malformed examples to print per file")
    parser.add_argument("--demo", action="store_true", help="create a tiny temporary metrics JSONL and summarize it")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.demo:
        print("# Metrics JSONL demo")
        print("A temporary tiny metrics file is created and removed automatically.\n")
        with tempfile.TemporaryDirectory(prefix="metrics-jsonl-demo-") as tmpdir:
            demo_path = Path(tmpdir) / "demo_metrics.jsonl"
            _write_demo_file(demo_path)
            rows, malformed, total_lines = _read_jsonl(demo_path)
            _summarize(str(demo_path.name), rows, malformed, total_lines, sample=max(0, args.sample_malformed))
        return 0

    if not args.paths:
        print("error: provide at least one metrics JSONL path or use --demo", file=sys.stderr)
        return 2

    ok = True
    for path in args.paths:
        try:
            rows, malformed, total_lines = _read_jsonl(path)
        except ValueError as exc:
            print(f"warning: {exc}", file=sys.stderr)
            ok = False
            continue
        _summarize(str(path), rows, malformed, total_lines, sample=max(0, args.sample_malformed))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
