#!/usr/bin/env python3
"""Plot MimicKit text training logs with explicit paths and headless defaults."""

from __future__ import annotations

import argparse
import io
from pathlib import Path
from typing import Iterable

import numpy as np


def _expand_logs(paths: Iterable[str]) -> list[Path]:
    logs: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            matches = sorted(p for p in path.iterdir() if p.is_file() and "log" in p.name.lower())
            if not matches:
                raise FileNotFoundError(f"no log-like files found in directory: {path}")
            logs.extend(matches)
        elif path.is_file():
            logs.append(path)
        else:
            raise FileNotFoundError(f"log path does not exist: {path}")
    if not logs:
        raise ValueError("no logs were provided")
    return logs


def _load_table(path: Path) -> np.ndarray:
    text = path.read_text(errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(",", "\t")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError(f"{path} does not contain a header plus numeric rows")
    data = np.genfromtxt(io.StringIO("\n".join(lines)), delimiter=None, dtype=float, names=True)
    if data.dtype.names is None:
        raise ValueError(f"could not parse column headers from {path}")
    if data.shape == ():
        data = data.reshape(1)
    return data


def _window_mean(values: np.ndarray, window: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if window <= 1:
        return values
    count = len(values) // window
    if count <= 0:
        raise ValueError(f"window size {window} is larger than series length {len(values)}")
    return values[: count * window].reshape(count, window).mean(axis=1)


def _extract_series(table: np.ndarray, path: Path, x_key: str, y_key: str, std_key: str | None, window: int):
    names = table.dtype.names or ()
    missing = [key for key in (x_key, y_key) if key not in names]
    if missing:
        raise KeyError(f"{path} missing {missing}; available columns: {', '.join(names)}")
    xs = _window_mean(table[x_key], window)
    ys = _window_mean(table[y_key], window)
    stds = None
    if std_key:
        if std_key not in names:
            raise KeyError(f"{path} missing std key {std_key!r}; available columns: {', '.join(names)}")
        stds = _window_mean(table[std_key], window)
    return xs, ys, stds


def plot_logs(args: argparse.Namespace) -> None:
    if not args.show:
        import matplotlib

        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    logs = _expand_logs(args.log)
    x_series = []
    y_series = []
    std_series = []
    for path in logs:
        table = _load_table(path)
        xs, ys, stds = _extract_series(table, path, args.x_key, args.y_key, args.std_key, args.window)
        x_series.append(xs)
        y_series.append(ys)
        if stds is not None:
            std_series.append(stds)

    fig, ax = plt.subplots(figsize=(5.5 * 0.8, 4.0 * 0.8))
    default_label = logs[0].parent.name if len(logs) > 1 else logs[0].stem
    label = args.label or (default_label if default_label else logs[0].stem)

    if args.no_band or len(logs) == 1:
        first_line = None
        for idx, (xs, ys, path) in enumerate(zip(x_series, y_series, logs)):
            run_label = label if len(logs) == 1 else f"{label}:{path.stem}"
            if idx == 0:
                first_line = ax.plot(xs, ys, label=run_label, alpha=1.0)[0]
            else:
                ax.plot(xs, ys, label=run_label if args.legend_each else "_nolegend_", color=first_line.get_color() if first_line else None, alpha=0.8)
            if idx < len(std_series):
                stds = std_series[idx]
                min_len = min(len(xs), len(ys), len(stds))
                ax.fill_between(xs[:min_len], ys[:min_len] - stds[:min_len], ys[:min_len] + stds[:min_len], alpha=0.25, linewidth=0)
    else:
        min_len = min(min(len(x) for x in x_series), min(len(y) for y in y_series))
        xs_stack = np.stack([x[:min_len] for x in x_series], axis=0)
        ys_stack = np.stack([y[:min_len] for y in y_series], axis=0)
        xs = xs_stack.mean(axis=0)
        ys = ys_stack.mean(axis=0)
        line = ax.plot(xs, ys, label=label)[0]
        if std_series:
            stds = np.stack([s[:min_len] for s in std_series], axis=0).mean(axis=0)
        elif len(y_series) > 1:
            stds = ys_stack.std(axis=0)
        else:
            stds = None
        if stds is not None:
            ax.fill_between(xs, ys - stds, ys + stds, alpha=0.25, linewidth=0, facecolor=line.get_color())

    min_len = min(len(y) for y in y_series)
    final_x = float(np.mean([x[min_len - 1] for x in x_series]))
    final_y = np.array([y[min_len - 1] for y in y_series], dtype=float)
    print(f"Final value at {args.x_key}={final_x:.6g}: {args.y_key}={final_y.mean():.6g} +/- {final_y.std():.6g}")

    ax.set_xlabel(args.x_key)
    ax.set_ylabel(args.y_key)
    ax.ticklabel_format(style="sci", axis="x", scilimits=(0, 0))
    ax.grid(linestyle="dotted")
    ax.legend()
    ax.set_title(args.title)
    fig.tight_layout()

    out_path = Path(args.out).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=args.dpi)
    print(f"Saved plot: {out_path}")
    if args.show:
        plt.show()
    plt.close(fig)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot MimicKit text log columns to an image.")
    parser.add_argument("--log", nargs="+", required=True, help="One or more log files or directories containing log files")
    parser.add_argument("--out", required=True, help="Output image path, for example plots/test_return.png")
    parser.add_argument("--x-key", default="Samples", help="Column to use for the x axis")
    parser.add_argument("--y-key", default="Test_Return", help="Column to use for the y axis")
    parser.add_argument("--std-key", default=None, help="Optional column containing y-axis standard deviation")
    parser.add_argument("--window", type=int, default=1, help="Non-overlapping averaging window")
    parser.add_argument("--title", default="Performance", help="Plot title")
    parser.add_argument("--label", default=None, help="Legend label for an aggregate plot")
    parser.add_argument("--no-band", action="store_true", help="Plot individual runs instead of mean/std band")
    parser.add_argument("--legend-each", action="store_true", help="When --no-band and multiple logs, show every run in the legend")
    parser.add_argument("--dpi", type=int, default=150, help="Output image DPI")
    parser.add_argument("--show", action="store_true", help="Also open an interactive window after saving")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.window <= 0:
        raise ValueError("--window must be positive")
    plot_logs(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
