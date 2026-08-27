#!/usr/bin/env python3
"""Inspect a PySR hall-of-fame CSV without importing PySR.

The script is intentionally read-only and uses only the Python standard library.
It validates that the CSV has equation, loss, and complexity columns, then emits
a compact summary of row positions and candidate equations.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ("equation", "loss", "complexity")
OPTIONAL_COLUMNS = ("score", "pick", "sympy_format", "lambda_format", "jax_format", "torch_format")
CANONICAL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
JULIA_FLOAT_SUFFIX_RE = re.compile(r"(?<=\d)[fF]([+-]?\d+)$")


def normalize_header(name: str | None, index: int) -> str:
    if name is None:
        return f"unnamed_{index}"
    stripped = name.strip().lstrip("\ufeff")
    if not stripped:
        return f"unnamed_{index}"
    return stripped.lower().replace(" ", "_")


def build_column_map(headers: list[str]) -> tuple[dict[str, str], list[str]]:
    canonical_to_original: dict[str, str] = {}
    warnings: list[str] = []
    seen_normalized: dict[str, str] = {}

    for idx, original in enumerate(headers):
        normalized = normalize_header(original, idx)
        if normalized in seen_normalized:
            warnings.append(
                f"duplicate normalized column {normalized!r}: {seen_normalized[normalized]!r} and {original!r}"
            )
        else:
            seen_normalized[normalized] = original

        if normalized in CANONICAL_COLUMNS:
            if normalized in canonical_to_original:
                warnings.append(
                    f"duplicate canonical column {normalized!r}; using first occurrence {canonical_to_original[normalized]!r}"
                )
            else:
                canonical_to_original[normalized] = original

    return canonical_to_original, warnings


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lower = text.lower()
    if lower in {"inf", "+inf", "infinity", "+infinity"}:
        return math.inf
    if lower in {"-inf", "-infinity"}:
        return -math.inf
    if lower in {"nan", "+nan", "-nan"}:
        return math.nan
    text = JULIA_FLOAT_SUFFIX_RE.sub(r"e\1", text)
    try:
        return float(text)
    except ValueError:
        return None


def finite_sort_value(value: float | None, *, descending: bool = False) -> tuple[int, float]:
    if value is None or math.isnan(value):
        return (1, 0.0)
    if descending:
        return (0, -value)
    return (0, value)


def truncate(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 1:
        return "…"
    return text[: width - 1] + "…"


def load_csv(path: Path, max_rows: int) -> tuple[list[str], list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("CSV has no header row")
            headers = list(reader.fieldnames)
            rows: list[dict[str, str]] = []
            for idx, row in enumerate(reader):
                if idx >= max_rows:
                    raise ValueError(
                        f"CSV has more than --max-rows={max_rows} data rows; raise the limit if intentional"
                    )
                if None in row:
                    warnings.append(
                        f"row {idx} has extra fields beyond the header; extra fields are ignored"
                    )
                    row.pop(None, None)
                rows.append(row)
            return headers, rows, warnings
    except FileNotFoundError as exc:
        raise ValueError(f"file does not exist: {path}") from exc
    except OSError as exc:
        raise ValueError(f"could not read CSV: {exc}") from exc
    except csv.Error as exc:
        raise ValueError(f"CSV parse error: {exc}") from exc


def row_value(row: dict[str, str], column_map: dict[str, str], canonical: str) -> str:
    original = column_map.get(canonical)
    if original is None:
        return ""
    return str(row.get(original, "")).strip()


def summarize(path: Path, rows: list[dict[str, str]], headers: list[str], column_map: dict[str, str], warnings: list[str], sort: str, limit: int, equation_width: int) -> dict[str, Any]:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in column_map]
    if missing_columns:
        raise ValueError(
            "missing required column(s): " + ", ".join(missing_columns) + "; expected equation/loss/complexity columns"
        )

    records: list[dict[str, Any]] = []
    missing_required_values: dict[str, int] = {col: 0 for col in REQUIRED_COLUMNS}
    parseable_numeric: dict[str, int] = {"loss": 0, "complexity": 0, "score": 0}

    for row_position, row in enumerate(rows):
        equation = row_value(row, column_map, "equation")
        loss_text = row_value(row, column_map, "loss")
        complexity_text = row_value(row, column_map, "complexity")
        score_text = row_value(row, column_map, "score")
        pick = row_value(row, column_map, "pick")

        for col, value in (("equation", equation), ("loss", loss_text), ("complexity", complexity_text)):
            if value == "":
                missing_required_values[col] += 1

        loss = parse_number(loss_text)
        complexity = parse_number(complexity_text)
        score = parse_number(score_text) if score_text else None

        if loss is not None:
            parseable_numeric["loss"] += 1
        if complexity is not None:
            parseable_numeric["complexity"] += 1
        if score is not None:
            parseable_numeric["score"] += 1

        records.append(
            {
                "row_position": row_position,
                "equation": equation,
                "equation_preview": truncate(equation, equation_width),
                "loss": loss,
                "loss_text": loss_text,
                "complexity": complexity,
                "complexity_text": complexity_text,
                "score": score,
                "score_text": score_text,
                "pick": pick,
            }
        )

    if sort == "loss":
        selected = sorted(records, key=lambda item: finite_sort_value(item["loss"]))
    elif sort == "complexity":
        selected = sorted(records, key=lambda item: finite_sort_value(item["complexity"]))
    elif sort == "score":
        selected = sorted(records, key=lambda item: finite_sort_value(item["score"], descending=True))
    else:
        selected = list(records)

    best_loss = min(records, key=lambda item: finite_sort_value(item["loss"]), default=None)
    simplest = min(records, key=lambda item: finite_sort_value(item["complexity"]), default=None)
    highest_score = None
    if "score" in column_map:
        highest_score = min(records, key=lambda item: finite_sort_value(item["score"], descending=True), default=None)

    summary = {
        "path": str(path),
        "row_count": len(rows),
        "columns": headers,
        "detected_columns": {key: column_map[key] for key in CANONICAL_COLUMNS if key in column_map},
        "missing_required_values": missing_required_values,
        "parseable_numeric_counts": parseable_numeric,
        "best_loss_row": best_loss,
        "simplest_row": simplest,
        "highest_score_row": highest_score,
        "rows": selected[:limit],
        "warnings": warnings,
    }
    return summary


def render_text(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"CSV: {summary['path']}")
    lines.append(f"Rows: {summary['row_count']}")
    lines.append("Columns: " + ", ".join(summary["columns"]))
    detected = summary["detected_columns"]
    lines.append("Detected schema: " + ", ".join(f"{k}={v!r}" for k, v in detected.items()))

    missing_values = {k: v for k, v in summary["missing_required_values"].items() if v}
    if missing_values:
        lines.append("Missing required values: " + ", ".join(f"{k}:{v}" for k, v in missing_values.items()))
    else:
        lines.append("Missing required values: none")

    numeric = summary["parseable_numeric_counts"]
    lines.append(
        "Numeric parse counts: "
        + ", ".join(f"{k}:{v}" for k, v in numeric.items())
    )

    def describe_row(label: str, row: dict[str, Any] | None) -> None:
        if row is None:
            return
        lines.append(
            f"{label}: row={row['row_position']} complexity={row['complexity_text'] or 'NA'} "
            f"loss={row['loss_text'] or 'NA'} score={row['score_text'] or 'NA'} "
            f"equation={row['equation_preview']!r}"
        )

    describe_row("Best loss", summary["best_loss_row"])
    describe_row("Simplest", summary["simplest_row"])
    describe_row("Highest score", summary["highest_score_row"])

    lines.append("Selected rows:")
    if not summary["rows"]:
        lines.append("  (none)")
    for row in summary["rows"]:
        pick = f" pick={row['pick']!r}" if row["pick"] else ""
        lines.append(
            f"  [{row['row_position']}] complexity={row['complexity_text'] or 'NA'} "
            f"loss={row['loss_text'] or 'NA'} score={row['score_text'] or 'NA'}{pick} "
            f"equation={row['equation_preview']!r}"
        )

    if summary["warnings"]:
        lines.append("Warnings:")
        for warning in summary["warnings"]:
            lines.append(f"  - {warning}")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a PySR hall-of-fame CSV without importing PySR or evaluating equations.",
    )
    parser.add_argument("csv_path", help="Path to hall_of_fame.csv, hall_of_fame.csv.bak, or hall_of_fame_output*.csv")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of rows to print or include in the selected-row summary (default: 10)")
    parser.add_argument("--sort", choices=("input", "loss", "complexity", "score"), default="input", help="How to order selected rows (default: input)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format (default: text)")
    parser.add_argument("--equation-width", type=int, default=120, help="Maximum equation preview width for text/JSON summaries (default: 120)")
    parser.add_argument("--max-rows", type=int, default=100000, help="Safety cap on data rows read from the CSV (default: 100000)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.limit < 0:
        print("error: --limit must be non-negative", file=sys.stderr)
        return 2
    if args.equation_width < 0:
        print("error: --equation-width must be non-negative", file=sys.stderr)
        return 2
    if args.max_rows <= 0:
        print("error: --max-rows must be positive", file=sys.stderr)
        return 2

    path = Path(args.csv_path)
    try:
        headers, rows, read_warnings = load_csv(path, args.max_rows)
        column_map, schema_warnings = build_column_map(headers)
        summary = summarize(
            path=path,
            rows=rows,
            headers=headers,
            column_map=column_map,
            warnings=read_warnings + schema_warnings,
            sort=args.sort,
            limit=args.limit,
            equation_width=args.equation_width,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
