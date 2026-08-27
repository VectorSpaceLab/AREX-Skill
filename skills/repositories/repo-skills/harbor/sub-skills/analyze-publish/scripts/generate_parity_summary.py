#!/usr/bin/env python3
"""Build a local parity CSV from generic parity_experiment.json files.

This helper intentionally has no Harbor checkout, network, credential, or
adapter import dependency. It only reads immediate child directories under
--adapters-dir and writes the selected CSV path.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

KNOWN_VALUE_KEYS = {"original", "harbor", "tb_adapter", "original_json", "original_llm"}
KNOWN_RUNS_KEYS = {
    "original_trials",
    "harbor_trials",
    "tb_adapter_trials",
    "original_runs",
    "harbor_runs",
    "original_json_trials",
    "original_llm_trials",
}
SKIP_METRIC_KEYS = {
    "benchmark_name",
    "metric",
    "harbor_std_error",
    "harbor_success_counts",
    "original_success_counts",
}
CSV_FIELDS = [
    "Name",
    "Harbor Status",
    "Harbor Adapter PR",
    "Metric",
    "Parity between",
    "Source value",
    "Source Std",
    "Source runs",
    "Target value",
    "Target Std",
    "Target runs",
    "Parity task num",
    "# runs",
    "Model",
    "Agent",
]


def parse_mean(value: Any) -> str:
    if value is None or not str(value).strip():
        return ""
    text = str(value).strip()
    match = re.match(r"^([+-]?\d+\.?\d*)", text)
    return match.group(1) if match else text


def parse_std(value: Any) -> str:
    if value is None or not str(value).strip():
        return ""
    match = re.search(r"[±]\s*([+-]?\d+\.?\d*)|[+]/-\s*([+-]?\d+\.?\d*)", str(value))
    return (match.group(1) or match.group(2)) if match else ""


def format_runs(value: Any) -> str:
    return ", ".join(str(item) for item in value) if isinstance(value, list) else ""


def detect_sides(metric: dict[str, Any]) -> tuple[str, str, str, str]:
    value_keys = [
        key
        for key in metric
        if key in KNOWN_VALUE_KEYS
        and key not in KNOWN_RUNS_KEYS
        and key not in SKIP_METRIC_KEYS
    ]
    if len(value_keys) == 2:
        if "harbor" in value_keys:
            source, target = next(key for key in value_keys if key != "harbor"), "harbor"
        elif "tb_adapter" in value_keys:
            source, target = next(key for key in value_keys if key != "tb_adapter"), "tb_adapter"
        else:
            source, target = sorted(value_keys)
        return source, source, target, target
    if len(value_keys) == 1:
        key = value_keys[0]
        return ("original", "original", "harbor", "harbor") if key == "harbor" else (key, key, "", "")
    return "original", "original", "harbor", "harbor"


def find_runs_key(metric: dict[str, Any], label: str) -> str:
    return next((f"{label}{suffix}" for suffix in ("_runs", "_trials") if f"{label}{suffix}" in metric), "")


def infer_parity_between(entry: dict[str, Any]) -> str:
    metrics = entry.get("metrics") or []
    if not metrics:
        return "harbor adapter x original"
    metric = metrics[0]
    has_tb = any(str(key).startswith("tb_adapter") for key in metric)
    has_harbor = any(str(key).startswith("harbor") for key in metric)
    has_original = any(str(key).startswith("original") for key in metric)
    notes = str(entry.get("notes") or "").lower()
    if has_tb and has_harbor:
        return "harbor adapter x terminal-bench adapter"
    if has_tb and has_original:
        return "terminal-bench adapter x original"
    if has_harbor and has_original:
        return "harbor adapter x terminal-bench adapter" if ("terminal" in notes or "tb" in notes) else "harbor adapter x original"
    return "harbor adapter x original"


def process_file(path: Path) -> list[dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: skipping {path}: {exc}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        print(f"Warning: skipping {path}: expected a JSON list", file=sys.stderr)
        return []

    rows: list[dict[str, str]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        adapter_name = str(entry.get("adapter_name") or path.parent.name)
        prs = entry.get("adapter_pr")
        adapter_pr = str(prs[0]) if isinstance(prs, list) and prs else ""
        num_runs = entry.get("number_of_runs") or entry.get("number_of_trials") or ""
        parity_num = entry.get("parity_benchmark_size") or ""
        between = str(entry.get("parity_between") or infer_parity_between(entry))
        metrics = entry.get("metrics") or []
        for metric in metrics:
            if not isinstance(metric, dict):
                continue
            source_label, source_key, target_label, target_key = detect_sides(metric)
            source_raw = metric.get(source_key, "")
            target_raw = metric.get(target_key, "")
            source_runs_key = find_runs_key(metric, source_label)
            target_runs_key = find_runs_key(metric, target_label)
            rows.append(
                {
                    "Name": adapter_name,
                    "Harbor Status": "Merged",
                    "Harbor Adapter PR": adapter_pr,
                    "Metric": str(metric.get("metric") or ""),
                    "Parity between": between,
                    "Source value": parse_mean(source_raw),
                    "Source Std": parse_std(source_raw),
                    "Source runs": format_runs(metric.get(source_runs_key, [])),
                    "Target value": parse_mean(target_raw),
                    "Target Std": parse_std(target_raw),
                    "Target runs": format_runs(metric.get(target_runs_key, [])),
                    "Parity task num": str(parity_num),
                    "# runs": str(num_runs),
                    "Model": str(entry.get("model") or ""),
                    "Agent": str(entry.get("agent") or ""),
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapters-dir", type=Path, default=Path("adapters"))
    parser.add_argument("--output", "-o", type=Path, default=Path("parity_summary.csv"))
    parser.add_argument("--no-header", action="store_true")
    args = parser.parse_args()
    if not args.adapters_dir.is_dir():
        parser.error(f"--adapters-dir is not a directory: {args.adapters_dir}")

    rows: list[dict[str, str]] = []
    n_inputs = 0
    for child in sorted(args.adapters_dir.iterdir()):
        if not child.is_dir():
            continue
        parity_file = child / "parity_experiment.json"
        if parity_file.is_file():
            n_inputs += 1
            rows.extend(process_file(parity_file))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        if not args.no_header:
            writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} rows from {n_inputs} parity file(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
