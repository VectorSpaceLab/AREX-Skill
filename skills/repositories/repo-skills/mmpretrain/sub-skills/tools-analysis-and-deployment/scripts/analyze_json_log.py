#!/usr/bin/env python3
"""Safe JSON log summary and curve plotting helper."""

from __future__ import annotations

import argparse
import os
import re
import sys
from itertools import groupby
from pathlib import Path

import numpy as np


def locate_repo_root() -> Path:
    """Find the repository root that contains the mmpretrain package."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / 'mmpretrain' / '__init__.py').is_file():
            return parent
    raise RuntimeError(
        'Unable to locate the repository root that contains the mmpretrain '
        'package.')


REPO_ROOT = locate_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mmpretrain.utils import load_json_log  # noqa: E402


def resolve_existing_path(raw: str) -> Path:
    """Resolve an input path against the current working directory and repo."""
    candidate = Path(raw).expanduser()
    search_order = [candidate]
    if not candidate.is_absolute():
        search_order = [Path.cwd() / candidate, REPO_ROOT / candidate, candidate]
    for path in search_order:
        if path.exists():
            return path.resolve()
    raise FileNotFoundError(f'Cannot find log file: {raw}')


def load_logs(paths: list[str]) -> tuple[list[Path], list[dict]]:
    resolved_paths = [resolve_existing_path(path) for path in paths]
    log_dicts = [load_json_log(str(path)) for path in resolved_paths]
    return resolved_paths, log_dicts


def available_keys(log_dict: dict, phase: str) -> set[str]:
    logs = log_dict.get(phase, [])
    keys: set[str] = set()
    for entry in logs:
        keys.update(entry.keys())
    return keys - {'step', 'epoch'}


def summarize_train_time(log_path: Path, log_dict: dict,
                         include_outliers: bool) -> list[str]:
    train_logs = log_dict.get('train', [])
    lines = [f'-----Analyze train time of {log_path}-----']
    if not train_logs:
        lines.append('No train records were found.')
        return lines

    epoch_ave_times = []
    if 'epoch' in train_logs[0]:
        for _, logs in groupby(train_logs, lambda log: log.get('epoch')):
            times = np.asarray([log.get('time') for log in logs], dtype=float)
            times = times[np.isfinite(times)]
            if times.size == 0:
                continue
            if not include_outliers and times.size > 1:
                times = times[1:]
            if times.size == 0:
                times = np.asarray([np.nan])
            epoch_ave_times.append(float(np.nanmean(times)))

        if epoch_ave_times:
            epoch_ave_times = np.asarray(epoch_ave_times, dtype=float)
            slowest_epoch = int(epoch_ave_times.argmax())
            fastest_epoch = int(epoch_ave_times.argmin())
            std_over_epoch = float(epoch_ave_times.std())
            lines.append(
                f'slowest epoch {slowest_epoch + 1}, average time is '
                f'{epoch_ave_times[slowest_epoch]:.4f}')
            lines.append(
                f'fastest epoch {fastest_epoch + 1}, average time is '
                f'{epoch_ave_times[fastest_epoch]:.4f}')
            lines.append(f'time std over epochs is {std_over_epoch:.4f}')

    iter_times = np.asarray(
        [log.get('time') for log in train_logs if 'time' in log], dtype=float)
    iter_times = iter_times[np.isfinite(iter_times)]
    if iter_times.size:
        lines.append(f'average iter time: {iter_times.mean():.4f} s/iter')
    else:
        lines.append('average iter time: unavailable')
    return lines


def summarize_metric(log_dict: dict, key: str) -> str:
    for phase in ('val', 'train'):
        logs = log_dict.get(phase, [])
        values = [entry[key] for entry in logs if key in entry]
        if values:
            arr = np.asarray(values, dtype=float)
            arr = arr[np.isfinite(arr)]
            if arr.size == 0:
                break
            return (
                f'  {key} [{phase}]: last={arr[-1]:.4f} min={arr.min():.4f} '
                f'max={arr.max():.4f} mean={arr.mean():.4f}')
    raise ValueError(f'Key "{key}" was not found in the log records.')


def default_legend_name(path: Path) -> str:
    name = path.name
    if name.endswith('.json'):
        name = name[:-5]
    if name.endswith('.log'):
        name = name[:-4]
    return name


def build_legends(paths: list[Path], keys: list[str], custom_legend: list[str] | None) -> list[str]:
    if custom_legend is not None:
        if len(custom_legend) != len(paths) * len(keys):
            raise ValueError(
                'The legend count must equal len(json_logs) * len(keys).')
        return custom_legend

    legends: list[str] = []
    for path in paths:
        base = default_legend_name(path)
        for key in keys:
            legends.append(f'{base}_{key}')
    return legends


def extract_series(logs: list[dict], key: str, phase: str) -> tuple[np.ndarray, np.ndarray]:
    records = [entry for entry in logs if key in entry]
    if not records:
        raise ValueError(f'Invalid key "{key}" for {phase} logs.')

    xs = np.asarray([entry.get('step', idx + 1) for idx, entry in enumerate(records)],
                     dtype=float)
    ys = np.asarray([entry[key] for entry in records], dtype=float)

    if phase == 'train' and logs and 'epoch' in logs[0]:
        steps = [entry.get('step', idx + 1) for idx, entry in enumerate(logs)]
        epochs = [entry.get('epoch', 1) for entry in logs]
        if steps and epochs and epochs[-1]:
            scale_factor = steps[-1] / epochs[-1]
            xs = xs / scale_factor
    return xs, np.asarray([entry[key] for entry in records], dtype=float)


def plot_curves(log_paths: list[Path], log_dicts: list[dict], args: argparse.Namespace) -> None:
    if not args.out and not args.show:
        raise ValueError('Provide --out to save the plot or --show to display it.')
    if args.out or (args.show and not os.environ.get('DISPLAY')):
        import matplotlib
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    try:
        import seaborn as sns
        sns.set_style(args.style)
    except ImportError:
        pass

    window_match = re.fullmatch(r'(\d+)\*(\d+)', args.window_size)
    if not window_match:
        raise ValueError("'window-size' must be in format 'W*H'.")
    wind_w, wind_h = map(int, window_match.groups())
    plt.figure(figsize=(wind_w, wind_h))

    legends = build_legends(log_paths, args.keys, args.legend)
    for i, log_dict in enumerate(log_dicts):
        train_logs = log_dict.get('train', [])
        val_logs = log_dict.get('val', [])
        train_keys = available_keys(log_dict, 'train')
        val_keys = available_keys(log_dict, 'val')
        for j, key in enumerate(args.keys):
            legend = legends[i * len(args.keys) + j]
            if key in val_keys:
                xs, ys = extract_series(val_logs, key, 'val')
            elif key in train_keys:
                xs, ys = extract_series(train_logs, key, 'train')
            else:
                raise ValueError(
                    f'Invalid key "{key}", please choose from '
                    f'{sorted(train_keys | val_keys)}.')
            print(f'plot curve of {log_paths[i]}, metric is {key}')
            plt.plot(xs, ys, label=legend, linewidth=0.75)

    if args.title is not None:
        plt.title(args.title)
    plt.legend()

    if args.out is not None:
        out = Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out, bbox_inches='tight')
        print(f'save curve to: {out}')

    if args.show:
        if os.environ.get('DISPLAY'):
            plt.show()
        elif args.out is None:
            raise RuntimeError('No display is available; use --out instead.')
        else:
            print('Display is unavailable; the plot was saved to disk only.')
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Summarize or plot MMEngine JSON logs safely.')
    subparsers = parser.add_subparsers(dest='task', required=True)

    summary_parser = subparsers.add_parser('summary', help='summarize log timing and chosen keys')
    summary_parser.add_argument('json_logs', nargs='+', help='JSON log file paths')
    summary_parser.add_argument(
        '--keys', nargs='+', default=None, help='metric keys to summarize')
    summary_parser.add_argument(
        '--include-outliers', action='store_true', help='keep the first record in each epoch')

    plot_parser = subparsers.add_parser('plot', help='plot selected log keys')
    plot_parser.add_argument('json_logs', nargs='+', help='JSON log file paths')
    plot_parser.add_argument(
        '--keys', nargs='+', default=['loss'], help='metric keys to plot')
    plot_parser.add_argument(
        '--legend', nargs='+', default=None, help='custom legend labels')
    plot_parser.add_argument('--title', type=str, default=None, help='figure title')
    plot_parser.add_argument(
        '--style', type=str, default='whitegrid', help='seaborn style when available')
    plot_parser.add_argument('--out', type=str, default=None, help='output image path')
    plot_parser.add_argument(
        '--show', action='store_true', help='display the figure when a display is available')
    plot_parser.add_argument(
        '--window-size', default='12*7', help='plot size in W*H format')

    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()
    log_paths, log_dicts = load_logs(args.json_logs)

    if args.task == 'summary':
        for log_path, log_dict in zip(log_paths, log_dicts):
            for line in summarize_train_time(log_path, log_dict, args.include_outliers):
                print(line)
            if args.keys:
                for key in args.keys:
                    print(summarize_metric(log_dict, key))
            print()
        return

    if args.task == 'plot':
        plot_curves(log_paths, log_dicts, args)
        return

    raise RuntimeError(f'Unsupported task: {args.task}')


if __name__ == '__main__':
    main()
