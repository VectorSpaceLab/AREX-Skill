#!/usr/bin/env python3
"""Summarize and optionally plot MMSegmentation/MMEngine JSON-line logs."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any


RecordMap = dict[str, list[tuple[int, float]]]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _load_records(paths: list[Path], keys: list[str] | None) -> dict[str, RecordMap]:
    all_logs: dict[str, RecordMap] = {}
    key_filter = set(keys or [])
    for path in paths:
        records: RecordMap = defaultdict(list)
        previous_step = 0
        with path.open('r', encoding='utf-8') as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f'{path}:{line_number}: invalid JSON: {exc}') from exc
                if not isinstance(row, dict):
                    continue
                step_value = row.get('step', previous_step)
                if _is_number(step_value) and int(step_value) != 0:
                    previous_step = int(step_value)
                step = previous_step
                for key, value in row.items():
                    if key == 'step':
                        continue
                    if key_filter and key not in key_filter:
                        continue
                    if _is_number(value):
                        records[key].append((step, float(value)))
        all_logs[str(path)] = dict(records)
    return all_logs


def _summarize(records: dict[str, RecordMap]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for path, metrics in records.items():
        summary[path] = {}
        for key, values in sorted(metrics.items()):
            numeric_values = [value for _, value in values]
            steps = [step for step, _ in values]
            if not numeric_values:
                continue
            summary[path][key] = {
                'count': len(numeric_values),
                'first_step': steps[0],
                'last_step': steps[-1],
                'first': numeric_values[0],
                'last': numeric_values[-1],
                'min': min(numeric_values),
                'max': max(numeric_values),
                'mean': statistics.fmean(numeric_values),
            }
    return summary


def _print_summary(summary: dict[str, Any]) -> None:
    for path, metrics in summary.items():
        print(path)
        if not metrics:
            print('  no numeric metrics matched')
            continue
        for key, stats in metrics.items():
            print(
                f"  {key}: count={stats['count']} "
                f"steps={stats['first_step']}..{stats['last_step']} "
                f"last={stats['last']:.6g} min={stats['min']:.6g} "
                f"max={stats['max']:.6g} mean={stats['mean']:.6g}")


def _write_plot(records: dict[str, RecordMap], plot_out: Path, title: str | None) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError('matplotlib is required for --plot-out') from exc

    plotted = False
    for path, metrics in records.items():
        for key, values in sorted(metrics.items()):
            if not values:
                continue
            steps = [step for step, _ in values]
            numeric_values = [value for _, value in values]
            plt.plot(steps, numeric_values, label=f'{Path(path).name}:{key}', linewidth=1.0)
            plotted = True
    if not plotted:
        raise RuntimeError('no numeric records available to plot')
    plt.xlabel('step')
    plt.ylabel('value')
    if title:
        plt.title(title)
    plt.legend()
    plot_out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(plot_out)
    plt.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Summarize MMSegmentation/MMEngine JSON-line logs without importing MMSegmentation.')
    parser.add_argument('json_logs', nargs='+', help='JSON-line log files')
    parser.add_argument('--keys', nargs='+', help='metric keys to include; defaults to all numeric keys')
    parser.add_argument('--summary-out', help='write JSON summary to this path')
    parser.add_argument('--plot-out', help='write a line plot to this path; requires matplotlib')
    parser.add_argument('--title', help='optional plot title')
    parser.add_argument('--strict-files', action='store_true', help='fail if any log path is missing')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = [Path(item) for item in args.json_logs]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing and args.strict_files:
        print(f"missing log file(s): {', '.join(missing)}", file=sys.stderr)
        return 2
    paths = [path for path in paths if path.is_file()]
    if not paths:
        print('no existing log files to analyze', file=sys.stderr)
        return 2

    try:
        records = _load_records(paths, args.keys)
        summary = _summarize(records)
        _print_summary(summary)
        if args.summary_out:
            summary_path = Path(args.summary_out)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding='utf-8')
        if args.plot_out:
            _write_plot(records, Path(args.plot_out), args.title)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failures.
        print(f'error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
