#!/usr/bin/env python3
"""Summarize local gptme eval result CSV files without running models.

This helper reads one or more ``eval_results.csv`` files or directories that
contain them, then prints a compact pass/fail summary that works even for tiny
fixtures with only ``Model``, ``Tool Format``, ``Test``, and ``Passed`` columns.

Examples:
    python scripts/summarize_eval_results.py
    python scripts/summarize_eval_results.py eval_results/20260323_050922Z
    python scripts/summarize_eval_results.py run.csv --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TRUE_VALUES = {"1", "true", "t", "yes", "y", "pass", "passed"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "fail", "failed"}


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be zero or positive")
    return parsed


@dataclass(frozen=True)
class EvalRow:
    model: str
    tool_format: str
    test: str
    passed: bool

    @property
    def key(self) -> str:
        if self.tool_format and self.tool_format != "default":
            return f"{self.model}@{self.tool_format}"
        return self.model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize local gptme eval result CSV files without running models",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("eval_results")],
        help=(
            "CSV file(s) or directories to scan. Directories are searched recursively "
            "for eval_results.csv files. Default: eval_results"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--limit-tests",
        type=non_negative_int,
        default=12,
        help="Maximum number of passed/failed test names to show per file.",
    )
    return parser.parse_args()


def _field(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None:
            value = value.strip()
            if value:
                return value
    return ""


def _parse_passed(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def _normalize_model(model: str, tool_format: str) -> tuple[str, str]:
    model = model.strip() or "unknown"
    tool_format = tool_format.strip()
    if "@" in model and not tool_format:
        base, suffix = model.rsplit("@", 1)
        if suffix:
            return base, suffix
    return model, tool_format or "default"


def discover_csv_files(paths: list[Path]) -> list[Path]:
    csv_files: set[Path] = set()
    for raw in paths:
        path = raw.expanduser()
        if not path.exists():
            print(f"warning: missing path skipped: {path}", file=sys.stderr)
            continue
        if path.is_file():
            if path.suffix.lower() == ".csv" or path.name == "eval_results.csv":
                csv_files.add(path)
            continue
        for csv_path in path.rglob("eval_results.csv"):
            csv_files.add(csv_path)
    return sorted(csv_files)


def read_rows(csv_path: Path) -> tuple[list[EvalRow], int]:
    rows: list[EvalRow] = []
    ignored = 0
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            model, tool_format = _normalize_model(
                _field(row, "Model", "model"),
                _field(row, "Tool Format", "tool_format", "format"),
            )
            test = _field(row, "Test", "test", "name")
            passed = _parse_passed(_field(row, "Passed", "passed"))
            if not test or passed is None:
                ignored += 1
                continue
            rows.append(EvalRow(model=model, tool_format=tool_format, test=test, passed=passed))
    return rows, ignored


def summarize_file(csv_path: Path, limit_tests: int) -> dict[str, Any]:
    rows, ignored = read_rows(csv_path)
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    passed_tests: list[str] = []
    failed_tests: list[str] = []

    for row in rows:
        by_model[row.key]["rows"] += 1
        by_model[row.key]["passed" if row.passed else "failed"] += 1
        if row.passed:
            passed_tests.append(f"{row.test} [{row.key}]")
        else:
            failed_tests.append(f"{row.test} [{row.key}]")

    passed = sum(1 for row in rows if row.passed)
    failed = sum(1 for row in rows if not row.passed)
    total = len(rows)
    pass_rate = passed / total if total else 0.0
    return {
        "path": str(csv_path),
        "rows": total,
        "passed": passed,
        "failed": failed,
        "ignored": ignored,
        "pass_rate": round(pass_rate, 4),
        "models": [
            {
                "model": model,
                "rows": counts["rows"],
                "passed": counts["passed"],
                "failed": counts["failed"],
                "pass_rate": round(counts["passed"] / counts["rows"], 4)
                if counts["rows"]
                else 0.0,
            }
            for model, counts in sorted(by_model.items())
        ],
        "passed_tests": passed_tests[:limit_tests],
        "failed_tests": failed_tests[:limit_tests],
    }


def summarize(paths: list[Path], limit_tests: int) -> dict[str, Any]:
    csv_files = discover_csv_files(paths)
    if not csv_files:
        raise FileNotFoundError("no eval_results.csv files found")

    file_summaries = [summarize_file(csv_path, limit_tests) for csv_path in csv_files]
    totals = Counter()
    for summary in file_summaries:
        totals["rows"] += summary["rows"]
        totals["passed"] += summary["passed"]
        totals["failed"] += summary["failed"]
        totals["ignored"] += summary["ignored"]

    totals_dict = {
        "files": len(file_summaries),
        "rows": totals["rows"],
        "passed": totals["passed"],
        "failed": totals["failed"],
        "ignored": totals["ignored"],
        "pass_rate": round(totals["passed"] / totals["rows"], 4)
        if totals["rows"]
        else 0.0,
    }
    return {"totals": totals_dict, "files": file_summaries}


def format_report(data: dict[str, Any], limit_tests: int) -> str:
    totals = data["totals"]
    lines = [
        "gptme eval results summary",
        f"files: {totals['files']}",
        f"rows: {totals['rows']}  passed: {totals['passed']}  failed: {totals['failed']}  pass_rate: {totals['pass_rate']:.1%}",
    ]
    if totals["ignored"]:
        lines.append(f"ignored rows: {totals['ignored']}")

    for summary in data["files"]:
        lines.append("")
        lines.append(f"file: {summary['path']}")
        lines.append(
            f"  rows: {summary['rows']}  passed: {summary['passed']}  failed: {summary['failed']}  pass_rate: {summary['pass_rate']:.1%}"
        )
        if summary["ignored"]:
            lines.append(f"  ignored rows: {summary['ignored']}")
        if summary["models"]:
            lines.append("  models:")
            for model in summary["models"]:
                lines.append(
                    f"    {model['model']}: {model['passed']}/{model['rows']} ({model['pass_rate']:.1%})"
                )
        if summary["passed_tests"]:
            lines.append("  passed tests:")
            for test in summary["passed_tests"][:limit_tests]:
                lines.append(f"    PASS {test}")
        if summary["failed_tests"]:
            lines.append("  failed tests:")
            for test in summary["failed_tests"][:limit_tests]:
                lines.append(f"    FAIL {test}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        data = summarize(args.paths, args.limit_tests)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_report(data, args.limit_tests))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
