#!/usr/bin/env python3
"""Summarize AIMET GenAILab profiling_data.json without importing GenAILab."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any

NON_METRIC_KEYS = {
    "model_id",
    "model_modifiers",
    "precision",
    "environment",
    "components",
    "export",
    "run_group",
}


def format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def format_duration(ms: float | int) -> str:
    seconds = float(ms) / 1000.0
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.1f}m"
    return f"{minutes / 60.0:.1f}h"


def summarize(path: Path) -> tuple[list[str], list[str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit("profiling JSON must be a dict keyed by model type")

    lines: list[str] = []
    warnings: list[str] = []
    entries: list[tuple[str, dict[str, Any]]] = []
    for model_type, items in data.items():
        if not isinstance(items, list):
            warnings.append(f"model_type {model_type!r} has non-list entries")
            continue
        for item in items:
            if isinstance(item, dict):
                entries.append((model_type, item))
            else:
                warnings.append(f"model_type {model_type!r} contains non-dict entry")

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for model_type, entry in entries:
        groups[(model_type, str(entry.get("model_id", "unknown")))].append(entry)

    lines.append(f"GenAILab profiling summary: {len(entries)} experiment(s) in {path}")
    for (model_type, model_id), group in sorted(groups.items()):
        lines.append("")
        lines.append(f"Model: {model_id}  Type: {model_type}  Experiments: {len(group)}")
        metric_names: list[str] = []
        for entry in group:
            for key in entry:
                if key not in NON_METRIC_KEYS and key not in metric_names:
                    metric_names.append(key)
        metric_versions: dict[str, set[Any]] = defaultdict(set)
        for metric in metric_names:
            for entry in group:
                if metric in entry and isinstance(entry[metric], dict):
                    metric_versions[metric].add(entry[metric].get("scoring_version", 1))
        for metric, versions in sorted(metric_versions.items()):
            if len(versions) > 1:
                warnings.append(
                    f"{model_id}/{metric}: mixed scoring versions {sorted(versions)}; do not compare these rows directly"
                )

        header = ["#", "run_group", "recipe", "cuda_peak", "time", *metric_names]
        lines.append(" | ".join(header))
        lines.append(" | ".join("---" for _ in header))
        for idx, entry in enumerate(group, 1):
            components = entry.get("components", {}) if isinstance(entry.get("components", {}), dict) else {}
            recipe_parts = []
            cuda_peak = 0.0
            elapsed_ms = 0.0
            for comp_name, comp in components.items():
                if isinstance(comp, dict):
                    recipe_parts.append(f"{comp_name}:{comp.get('recipe', '—')}")
                    util = comp.get("resource_utilization", {}) if isinstance(comp.get("resource_utilization", {}), dict) else {}
                    cuda_peak = max(cuda_peak, float(util.get("cuda_peak_mb", 0) or 0))
                    elapsed_ms += float(util.get("elapsed_ms", 0) or 0)
            row = [
                str(idx),
                str(entry.get("run_group", "") or ""),
                ";".join(recipe_parts) or "—",
                f"{cuda_peak:.0f} MB" if cuda_peak else "—",
                format_duration(elapsed_ms) if elapsed_ms else "—",
            ]
            for metric in metric_names:
                payload = entry.get(metric)
                if isinstance(payload, dict):
                    value = format_value(payload.get("result", "—"))
                    version = payload.get("scoring_version", 1)
                    row.append(f"{value} (v{version})")
                else:
                    row.append("—")
            lines.append(" | ".join(row))
    return lines, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiling_json", type=Path, help="Path to GenAILab profiling_data.json")
    parser.add_argument("--json", action="store_true", help="Emit JSON with lines and warnings")
    args = parser.parse_args()

    path = args.profiling_json.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"profiling JSON not found: {path}")
    lines, warnings = summarize(path)
    if args.json:
        print(json.dumps({"path": str(path), "warnings": warnings, "summary_lines": lines}, indent=2))
    else:
        print("\n".join(lines))
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"- {warning}")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
