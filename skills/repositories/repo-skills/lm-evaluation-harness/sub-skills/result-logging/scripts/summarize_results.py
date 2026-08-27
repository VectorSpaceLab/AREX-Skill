#!/usr/bin/env python3
"""Summarize lm-evaluation-harness result JSON files as local Markdown tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

DISPLAY_KEYS = {"alias", "name", "sample_len", "sample_count"}


def load_result(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected a JSON object")
    if "results" not in data or not isinstance(data.get("results"), dict):
        raise SystemExit(f"{path}: expected top-level 'results' object")
    return data


def split_metric_key(key: str) -> tuple[str, str]:
    metric, separator, filter_name = key.partition(",")
    return metric, filter_name if separator else ""


def metric_rows(data: dict[str, Any], section: str) -> Iterable[list[str]]:
    metrics_by_task = data.get(section, {})
    if not isinstance(metrics_by_task, dict):
        return

    versions = data.get("versions", {}) if isinstance(data.get("versions"), dict) else {}
    fewshot = data.get("n-shot", {}) if isinstance(data.get("n-shot"), dict) else {}
    sample_counts = data.get("n-samples", {}) if isinstance(data.get("n-samples"), dict) else {}

    for task_name in sorted(metrics_by_task):
        task_metrics = metrics_by_task.get(task_name, {})
        if not isinstance(task_metrics, dict):
            continue
        version = versions.get(task_name, "")
        shots = fewshot.get(task_name, "")
        count = sample_counts.get(task_name, "")
        if isinstance(count, dict):
            original = count.get("original", "")
            effective = count.get("effective", "")
            count = f"{effective}/{original}" if original != "" else str(effective)
        elif count is None:
            count = ""

        for key in sorted(task_metrics):
            if key in DISPLAY_KEYS or key.endswith("_stderr"):
                continue
            metric, filter_name = split_metric_key(key)
            if metric.endswith("_stderr"):
                continue
            value = task_metrics.get(key)
            stderr_key = f"{metric}_stderr,{filter_name}" if filter_name else f"{metric}_stderr"
            stderr = task_metrics.get(stderr_key, "")
            yield [
                section,
                str(task_name),
                str(version if version is not None else ""),
                str(shots if shots is not None else ""),
                str(count if count is not None else ""),
                str(filter_name),
                str(metric),
                format_value(value),
                format_value(stderr),
            ]


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def markdown_table(rows: list[list[str]]) -> str:
    headers = ["section", "task", "version", "n-shot", "samples", "filter", "metric", "value", "stderr"]
    matrix = [headers, ["---"] * len(headers), *rows]
    widths = [max(len(row[index]) for row in matrix) for index in range(len(headers))]
    lines = []
    for row_index, row in enumerate(matrix):
        padded = [cell.ljust(widths[index]) for index, cell in enumerate(row)]
        lines.append("| " + " | ".join(padded) + " |")
        if row_index == 0:
            separator = ["-" * widths[index] for index in range(len(headers))]
            lines.append("| " + " | ".join(separator) + " |")
            break
    for row in rows:
        padded = [cell.ljust(widths[index]) for index, cell in enumerate(row)]
        lines.append("| " + " | ".join(padded) + " |")
    return "\n".join(lines)


def summarize(paths: list[Path], include_groups: bool) -> str:
    sections = []
    for path in paths:
        data = load_result(path)
        rows = list(metric_rows(data, "results"))
        if include_groups:
            rows.extend(metric_rows(data, "groups"))
        if not rows:
            sections.append(f"## {path}\n\nNo metric rows found.")
        else:
            sections.append(f"## {path}\n\n{markdown_table(rows)}")
    return "\n\n".join(sections) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="+", type=Path, help="Aggregated results_*.json files")
    parser.add_argument("--include-groups", action="store_true", help="Include group metrics when present")
    parser.add_argument("--output", type=Path, help="Write Markdown output to this file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rendered = summarize(args.results, args.include_groups)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
