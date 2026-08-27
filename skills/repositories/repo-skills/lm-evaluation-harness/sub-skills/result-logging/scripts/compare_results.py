#!/usr/bin/env python3
"""Compare metrics from two local lm-evaluation-harness result JSON files."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any

DISPLAY_KEYS = {"alias", "name", "sample_len", "sample_count"}


def load_result(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(data, dict) or not isinstance(data.get("results"), dict):
        raise SystemExit(f"{path}: expected top-level 'results' object")
    return data


def numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def match_metric_key(metrics: dict[str, Any], requested: str) -> str | None:
    if requested in metrics and requested not in DISPLAY_KEYS:
        return requested
    matches = []
    for key in metrics:
        if key in DISPLAY_KEYS or key.endswith("_stderr"):
            continue
        metric, _, _filter_name = key.partition(",")
        if metric == requested:
            matches.append(key)
    if len(matches) == 1:
        return matches[0]
    if not matches and "," not in requested:
        candidate = f"{requested},none"
        if candidate in metrics:
            return candidate
    return None


def stderr_for(metrics: dict[str, Any], key: str) -> float | None:
    metric, separator, filter_name = key.partition(",")
    candidates = []
    if separator:
        candidates.append(f"{metric}_stderr,{filter_name}")
    candidates.append(f"{metric}_stderr")
    for candidate in candidates:
        value = numeric(metrics.get(candidate))
        if value is not None:
            return value
    return None


def higher_is_better(data: dict[str, Any], task: str, key: str) -> bool | None:
    hib = data.get("higher_is_better")
    if not isinstance(hib, dict):
        return None
    task_hib = hib.get(task)
    if not isinstance(task_hib, dict):
        return None
    metric, _, _filter_name = key.partition(",")
    for candidate in (key, metric):
        value = task_hib.get(candidate)
        if isinstance(value, bool):
            return value
    return None


def compare(baseline: dict[str, Any], candidate: dict[str, Any], requested_metric: str, alpha: float) -> list[list[str]]:
    rows: list[list[str]] = []
    baseline_results = baseline["results"]
    candidate_results = candidate["results"]
    for task in sorted(set(baseline_results) & set(candidate_results)):
        left = baseline_results.get(task, {})
        right = candidate_results.get(task, {})
        if not isinstance(left, dict) or not isinstance(right, dict):
            continue
        left_key = match_metric_key(left, requested_metric)
        right_key = match_metric_key(right, requested_metric)
        if not left_key or not right_key or left_key != right_key:
            continue
        left_value = numeric(left.get(left_key))
        right_value = numeric(right.get(right_key))
        if left_value is None or right_value is None:
            continue
        delta = right_value - left_value
        direction = higher_is_better(candidate, task, right_key)
        if direction is None:
            verdict = "delta-only"
        elif delta == 0:
            verdict = "tie"
        elif (delta > 0 and direction) or (delta < 0 and not direction):
            verdict = "candidate better"
        else:
            verdict = "baseline better"

        left_stderr = stderr_for(left, left_key)
        right_stderr = stderr_for(right, right_key)
        z_value = ""
        p_value = ""
        significant = ""
        if left_stderr is not None and right_stderr is not None:
            denom = math.sqrt(left_stderr**2 + right_stderr**2)
            if denom > 0:
                z = delta / denom
                p = 2 * (1 - NormalDist().cdf(abs(z)))
                z_value = f"{z:.6g}"
                p_value = f"{p:.6g}"
                significant = "yes" if p <= alpha else "no"

        rows.append([
            task,
            left_key,
            f"{left_value:.6g}",
            f"{right_value:.6g}",
            f"{delta:.6g}",
            verdict,
            z_value,
            p_value,
            significant,
        ])
    return rows


def markdown_table(rows: list[list[str]]) -> str:
    headers = ["task", "metric", "baseline", "candidate", "delta", "verdict", "z", "p", "p<=alpha"]
    if not rows:
        return "No comparable numeric metric rows found.\n"
    matrix = [headers, *rows]
    widths = [max(len(row[index]) for row in matrix) for index in range(len(headers))]
    lines = []
    header = [headers[index].ljust(widths[index]) for index in range(len(headers))]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("-" * width for width in widths) + " |")
    for row in rows:
        padded = [row[index].ljust(widths[index]) for index in range(len(headers))]
        lines.append("| " + " | ".join(padded) + " |")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Baseline aggregated results_*.json")
    parser.add_argument("candidate", type=Path, help="Candidate aggregated results_*.json")
    parser.add_argument("--metric", default="acc", help="Metric family or exact metric key, e.g. acc or acc,none")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance threshold for rows with stderr")
    parser.add_argument("--output", type=Path, help="Write Markdown output to this file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = load_result(args.baseline)
    candidate = load_result(args.candidate)
    rows = compare(baseline, candidate, args.metric, args.alpha)
    rendered = markdown_table(rows)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
