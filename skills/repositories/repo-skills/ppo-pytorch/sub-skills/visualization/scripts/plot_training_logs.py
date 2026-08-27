#!/usr/bin/env python3
"""Plot PPO training logs safely.

This helper adapts the repository's `plot_graph.py` workflow into a small CLI
that can be run from any directory. It validates the log schema, smooths the
reward curves, and writes a PNG without requiring an interactive display.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class PlotResolution:
    env_name: Optional[str]
    log_root: str
    output_root: str
    input_files: List[str]
    output_path: Optional[str]
    plot_avg: bool
    window_len_smooth: int
    window_len_var: int
    input_count: int
    warnings: List[str]


DEFAULT_COLUMNS = ["episode", "timestep", "reward"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot PPO training reward logs safely.")
    parser.add_argument("--env-name", help="Environment name such as CartPole-v1.")
    parser.add_argument("--log-root", default="PPO_logs", help="Root directory containing per-environment log folders.")
    parser.add_argument("--output-root", default="PPO_figs", help="Root directory for saved figures.")
    parser.add_argument("--input", nargs="*", help="Explicit log CSV files. If omitted, the helper discovers files from the default layout.")
    parser.add_argument("--fig-num", type=int, default=0, help="Figure number used in the default filename.")
    parser.add_argument("--plot-avg", action=argparse.BooleanOptionalAction, default=True, help="Average all runs by index when more than one CSV is available.")
    parser.add_argument("--window-smooth", type=int, default=20, help="Smoothing window for the primary curve.")
    parser.add_argument("--window-var", type=int, default=5, help="Smoothing window for the secondary low-opacity curve.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser


def _discover_inputs(env_name: Optional[str], log_root: str, explicit: Optional[List[str]]) -> List[Path]:
    if explicit:
        return [Path(item) for item in explicit]
    if not env_name:
        return []
    pattern = Path(log_root) / env_name / f"PPO_{env_name}_log_*.csv"
    return sorted(Path().glob(str(pattern)))


def _validate_frame(df: pd.DataFrame, path: Path) -> None:
    missing = [column for column in DEFAULT_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def _smooth_series(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return series.copy()
    return series.rolling(window=window, min_periods=1).mean()


def _plot_all_runs(dataframes: List[pd.DataFrame], resolution: PlotResolution) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["red", "blue", "green", "orange", "purple", "olive", "brown", "magenta", "cyan", "crimson", "gray", "black"]

    if resolution.plot_avg and len(dataframes) > 1:
        df_concat = pd.concat(dataframes)
        data_avg = df_concat.groupby(df_concat.index).mean(numeric_only=True)
        data_avg["reward_smooth"] = _smooth_series(data_avg["reward"], resolution.window_len_smooth)
        data_avg["reward_var"] = _smooth_series(data_avg["reward"], resolution.window_len_var)
        data_avg.plot(kind="line", x="timestep", y="reward_smooth", ax=ax, color=colors[0], linewidth=1.5, alpha=1)
        data_avg.plot(kind="line", x="timestep", y="reward_var", ax=ax, color=colors[0], linewidth=2, alpha=0.1)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend([handles[0]], [f"reward_avg_{len(dataframes)}_runs"], loc=2)
    else:
        for index, run in enumerate(dataframes):
            run = run.copy()
            run[f"reward_smooth_{index}"] = _smooth_series(run["reward"], resolution.window_len_smooth)
            run[f"reward_var_{index}"] = _smooth_series(run["reward"], resolution.window_len_var)
            color = colors[index % len(colors)]
            run.plot(kind="line", x="timestep", y=f"reward_smooth_{index}", ax=ax, color=color, linewidth=1.5, alpha=1)
            run.plot(kind="line", x="timestep", y=f"reward_var_{index}", ax=ax, color=color, linewidth=2, alpha=0.1)

        handles, labels = ax.get_legend_handles_labels()
        new_handles = []
        new_labels = []
        for index, handle in enumerate(handles):
            if index % 2 == 0:
                new_handles.append(handle)
                new_labels.append(labels[index])
        ax.legend(new_handles, new_labels, loc=2)

    ax.grid(color="gray", linestyle="-", linewidth=1, alpha=0.2)
    ax.set_xlabel("Timesteps", fontsize=12)
    ax.set_ylabel("Rewards", fontsize=12)
    if resolution.env_name:
        plt.title(resolution.env_name, fontsize=14)

    fig.tight_layout()
    fig.savefig(resolution.output_path)
    plt.close(fig)


def resolve(args: argparse.Namespace) -> PlotResolution:
    warnings: List[str] = []
    inputs = _discover_inputs(args.env_name, args.log_root, args.input)
    if args.input and not inputs:
        warnings.append("No input files were resolved from the explicit --input list.")
    if not args.input and not args.env_name:
        warnings.append("Provide --env-name or explicit --input files so the helper can find logs.")

    output_path = None
    if args.env_name:
        output_path = str(Path(args.output_root) / args.env_name / f"PPO_{args.env_name}_fig_{args.fig_num}.png")
    elif inputs:
        output_path = str(Path(args.output_root) / f"ppo_logs_fig_{args.fig_num}.png")

    return PlotResolution(
        env_name=args.env_name,
        log_root=args.log_root,
        output_root=args.output_root,
        input_files=[str(path) for path in inputs],
        output_path=output_path,
        plot_avg=bool(args.plot_avg),
        window_len_smooth=args.window_smooth,
        window_len_var=args.window_var,
        input_count=len(inputs),
        warnings=warnings,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    resolution = resolve(args)

    if args.json:
        print(json.dumps(asdict(resolution), indent=2, sort_keys=True))
        return 0

    print("PPO log plotting helper")
    print("=" * 79)
    print(f"env_name: {resolution.env_name}")
    print(f"log_root: {resolution.log_root}")
    print(f"output_root: {resolution.output_root}")
    print(f"input_files: {resolution.input_files}")
    print(f"output_path: {resolution.output_path}")
    print(f"plot_avg: {resolution.plot_avg}")
    print(f"window_len_smooth: {resolution.window_len_smooth}")
    print(f"window_len_var: {resolution.window_len_var}")
    if resolution.warnings:
        print("warnings:")
        for warning in resolution.warnings:
            print(f"  - {warning}")

    if not resolution.input_files:
        return 2
    if not resolution.output_path:
        parser.error("could not determine an output path")

    dataframes: List[pd.DataFrame] = []
    for raw_path in resolution.input_files:
        path = Path(raw_path)
        if not path.is_file():
            parser.error(f"missing log CSV: {path}")
        df = pd.read_csv(path)
        _validate_frame(df, path)
        dataframes.append(df)

    Path(resolution.output_path).parent.mkdir(parents=True, exist_ok=True)
    _plot_all_runs(dataframes, resolution)
    print(f"figure saved at: {resolution.output_path}")
    print("=" * 79)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
