#!/usr/bin/env python3
"""Summarize local FLA benchmark JSON without importing FLA or using hardware."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

METRIC_KEYS = {
    'median_ms',
    'p20_ms',
    'p80_ms',
    'base_ms',
    'head_ms',
    'change_pct',
    'speedup',
}
PREFERRED_ID_KEYS = ['op', 'mode', 'L', 'B', 'T', 'H', 'D', 'HQ', 'S', 'block_size']


def _as_hashable(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(',', ':'))
    return value


def _row_key(row: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return tuple(
        sorted(
            (key, _as_hashable(value))
            for key, value in row.items()
            if key not in METRIC_KEYS
        )
    )


def _shape_label(row: dict[str, Any]) -> str:
    parts: list[str] = []
    used = set()
    for key in PREFERRED_ID_KEYS:
        if key in row:
            used.add(key)
            if key in {'op', 'mode'}:
                parts.append(str(row[key]))
            else:
                parts.append(f'{key}{row[key]}')
    for key in sorted(k for k in row if k not in used and k not in METRIC_KEYS):
        parts.append(f'{key}={row[key]}')
    return ' / '.join(parts) if parts else '<unknown row>'


def _float(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _geomean(values: list[float]) -> float | None:
    positive = [v for v in values if v > 0 and math.isfinite(v)]
    if not positive:
        return None
    return math.exp(sum(math.log(v) for v in positive) / len(positive))


def _machine_line(data: dict[str, Any]) -> str | None:
    info = data.get('machine_info')
    if not isinstance(info, dict):
        return None
    gpu = info.get('gpu_name', 'N/A')
    backend = info.get('device_platform', 'N/A')
    cuda = info.get('cuda_version')
    torch = info.get('pytorch_version', 'N/A')
    triton = info.get('triton_version', 'N/A')
    git = info.get('git_label', 'unknown')
    if backend == 'cuda' and cuda:
        backend = f'cuda {cuda}'
    return f'Machine: {gpu} | {backend} | torch {torch} | triton {triton} | {git}'


def _print_rows(title: str, rows: list[dict[str, Any]], *, top: int, reverse: bool) -> None:
    if not rows:
        return
    print(f'\n{title}:')
    for row in sorted(rows, key=lambda item: item['change_pct'], reverse=reverse)[:top]:
        marker = '+' if row['change_pct'] > 0 else ''
        print(
            f"  {marker}{row['change_pct']:.1f}% "
            f"speedup={row['speedup']:.2f}x "
            f"base={row['base_ms']:.3f}ms head={row['head_ms']:.3f}ms  "
            f"{row['label']}"
        )


def summarize_comparison(data: dict[str, Any], *, threshold: float, top: int) -> int:
    base_results = data.get('base_results') or []
    head_results = data.get('head_results') or []
    if not isinstance(base_results, list) or not isinstance(head_results, list):
        raise ValueError('comparison JSON must contain list fields base_results and head_results')

    base_map = {_row_key(row): row for row in base_results if isinstance(row, dict)}
    head_map = {_row_key(row): row for row in head_results if isinstance(row, dict)}
    all_keys = sorted(set(base_map) | set(head_map))

    matched: list[dict[str, Any]] = []
    base_only = 0
    head_only = 0
    for key in all_keys:
        base = base_map.get(key)
        head = head_map.get(key)
        if base is None:
            head_only += 1
            continue
        if head is None:
            base_only += 1
            continue
        base_ms = _float(base, 'median_ms')
        head_ms = _float(head, 'median_ms')
        if base_ms is None or head_ms is None or base_ms <= 0 or head_ms <= 0:
            continue
        change_pct = (head_ms - base_ms) / base_ms * 100.0
        matched.append({
            'label': _shape_label(head),
            'base_ms': base_ms,
            'head_ms': head_ms,
            'change_pct': change_pct,
            'speedup': base_ms / head_ms,
        })

    regressions = [row for row in matched if row['change_pct'] > threshold]
    speedups = [row for row in matched if row['change_pct'] < -threshold]
    neutral = len(matched) - len(regressions) - len(speedups)
    geomean = _geomean([row['speedup'] for row in matched])

    print('Benchmark comparison summary')
    if data.get('base_sha') or data.get('head_sha'):
        print(f"Refs: base={data.get('base_sha', 'base')} head={data.get('head_sha', 'head')}")
    line = _machine_line(data)
    if line:
        print(line)
    print(f'Rows: matched={len(matched)} neutral={neutral} regressions={len(regressions)} speedups={len(speedups)}')
    print(f'Unmatched: base_only={base_only} head_only={head_only}')
    if geomean is not None:
        print(f'Equal-row geomean speedup: {geomean:.3f}x')
    print(f'Threshold: +/-{threshold:.1f}%')

    _print_rows('Worst regressions', regressions, top=top, reverse=True)
    _print_rows('Best speedups', speedups, top=top, reverse=False)
    return 1 if regressions else 0


def summarize_results(data: dict[str, Any] | list[Any], *, top: int) -> int:
    if isinstance(data, dict):
        results = data.get('results') or []
    else:
        results = data
    if not isinstance(results, list):
        raise ValueError('results JSON must be a list or contain a list field named results')

    rows = [row for row in results if isinstance(row, dict) and _float(row, 'median_ms') is not None]
    print('Benchmark results summary')
    if isinstance(data, dict):
        line = _machine_line(data)
        if line:
            print(line)
    print(f'Rows: {len(rows)}')
    if not rows:
        return 0

    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get('op', '<op>')), str(row.get('mode', '<mode>')))].append(float(row['median_ms']))

    print('\nBy op/mode median latency:')
    for (op, mode), values in sorted(groups.items()):
        values = sorted(values)
        print(
            f'  {op:<32s} {mode:<7s} '
            f'n={len(values):<3d} median={statistics.median(values):.3f}ms '
            f'min={values[0]:.3f}ms max={values[-1]:.3f}ms'
        )

    print('\nSlowest rows:')
    for row in sorted(rows, key=lambda item: float(item['median_ms']), reverse=True)[:top]:
        print(f"  {float(row['median_ms']):.3f}ms  {_shape_label(row)}")
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Summarize benchmark_results-like JSON files without running FLA benchmarks.',
    )
    parser.add_argument('json_file', help='Path to comparison JSON, unified run JSON, or raw result-row list.')
    parser.add_argument('--threshold', type=float, default=5.0, help='Regression/speedup threshold in percent. Default: 5.0.')
    parser.add_argument('--top', type=int, default=10, help='Number of notable rows to print per section. Default: 10.')
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit non-zero when comparison regressions exceed the threshold.',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    with Path(args.json_file).open(encoding='utf-8') as handle:
        data = json.load(handle)

    if isinstance(data, dict) and 'base_results' in data and 'head_results' in data:
        code = summarize_comparison(data, threshold=args.threshold, top=max(0, args.top))
        return code if args.strict else 0
    code = summarize_results(data, top=max(0, args.top))
    return code if args.strict else 0


if __name__ == '__main__':
    raise SystemExit(main())
