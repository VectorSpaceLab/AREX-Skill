#!/usr/bin/env python3
"""Create a headless VPG performance plot from one or more sessions.

This standalone helper preserves the historical plot.py curve formulas while
adding validation, deterministic method selection, and an explicit output path.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class PlotError(ValueError):
    """An actionable plot-input error."""


def _load(path: Path, *, ndmin: int) -> np.ndarray:
    try:
        value = np.asarray(np.loadtxt(path, delimiter=" ", ndmin=ndmin))
    except (OSError, ValueError) as exc:
        raise PlotError(f"cannot read {path}: expected whitespace-separated numeric values ({exc})") from exc
    if value.size == 0:
        raise PlotError(f"{path} is empty; restore the missing log rows")
    if not np.all(np.isfinite(value)):
        raise PlotError(f"{path} contains NaN or infinite values")
    return value


def _scalar_log(path: Path) -> np.ndarray:
    values = _load(path, ndmin=2)
    if values.ndim != 2 or values.shape[1] != 1:
        raise PlotError(
            f"{path} must contain one scalar per row; got shape {values.shape}"
        )
    return values.reshape(-1)


def _session_data(session_arg: str, method_override: str) -> tuple[str, Path, str, np.ndarray, np.ndarray]:
    session = Path(session_arg).expanduser().resolve()
    if not session.is_dir():
        raise PlotError(f"session directory does not exist or is not a directory: {session}")
    transitions = session / "transitions"
    action_path = transitions / "executed-action.log.txt"
    reward_path = transitions / "reward-value.log.txt"
    missing = [str(p) for p in (action_path, reward_path) if not p.is_file()]
    if missing:
        raise PlotError("missing required plot log file(s): " + ", ".join(missing))
    actions = _load(action_path, ndmin=2)
    rewards = _scalar_log(reward_path)
    if actions.ndim != 2 or actions.shape[1] < 1 or actions.shape[0] < 3:
        raise PlotError(
            f"{action_path} needs at least 3 rows and an action-ID column; got shape {actions.shape}"
        )
    if rewards.shape[0] < actions.shape[0] - 2:
        raise PlotError(
            f"{reward_path} has {rewards.shape[0]} values but the plot needs at least "
            f"{actions.shape[0] - 2} rewards after the source two-row tail exclusion"
        )
    if not np.all(np.isin(actions[:, 0], (0, 1))):
        raise PlotError(f"{action_path} column 0 must contain only 0=push or 1=grasp")

    if method_override != "auto":
        method = method_override
    else:
        models = session / "models"
        if not models.is_dir():
            raise PlotError(
                f"cannot infer method: missing {models}; pass --method reactive or --method reinforcement"
            )
        markers = []
        for candidate in sorted(models.iterdir(), key=lambda p: p.name):
            if not candidate.is_file():
                continue
            name = candidate.name.lower()
            if "reactive" in name:
                markers.append("reactive")
            elif "reinforcement" in name:
                markers.append("reinforcement")
        if not markers:
            raise PlotError(
                f"cannot infer method from {models}; use a filename containing reactive/reinforcement "
                "or pass --method"
            )
        method = markers[0]
    return str(session_arg), session, method, actions, rewards


def _success_values(rewards: np.ndarray, indices: np.ndarray, method: str) -> int:
    if method == "reactive":
        return int(np.sum(rewards[indices] == 0))
    return int(np.sum(rewards[indices] >= 0.5))


def _curves(actions: np.ndarray, rewards: np.ndarray, method: str, interval_size: int, max_plot_iteration: int) -> tuple[np.ndarray, np.ndarray]:
    # plot.py deliberately excludes two trailing action rows.
    max_iteration = min(actions.shape[0] - 2, max_plot_iteration)
    action_ids = actions[:max_iteration, 0]
    reward_values = rewards[:max_iteration]
    grasp_success = np.zeros(max_iteration, dtype=float)
    push_then_grasp_success = np.zeros(max_iteration, dtype=float)

    for step in range(max_iteration):
        grasp_before = np.flatnonzero(action_ids[:step] == 1)
        grasp_over_interval = grasp_before[max(0, len(grasp_before) - interval_size) :]
        denominator = float(min(interval_size, max(step, 1)))
        value = float(_success_values(reward_values, grasp_over_interval, method)) / denominator
        if step < interval_size:
            value *= float(step) / float(interval_size)
        grasp_success[step] = value

        push_indices = np.flatnonzero(action_ids[: max_iteration - 1] == 0)
        after_push = push_indices[action_ids[push_indices + 1] == 1] + 1
        after_push_before = after_push[after_push < step]
        after_push_over_interval = after_push_before[max(0, len(after_push_before) - interval_size) :]
        value = float(_success_values(reward_values, after_push_over_interval, method)) / denominator
        if step < interval_size:
            value *= float(step) / float(interval_size)
        push_then_grasp_success[step] = value
    return grasp_success, push_then_grasp_success


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot VPG grasp and push-then-grasp performance headlessly.")
    parser.add_argument("session_directories", metavar="N", nargs="+", help="one or more session roots (source-compatible positional input)")
    parser.add_argument("--output", default="performance.png", help="output image path (default: performance.png)")
    parser.add_argument("--method", choices=("auto", "reactive", "reinforcement"), default="auto", help="override model-name method detection")
    parser.add_argument("--interval-size", type=int, default=200, help="preceding action window (default: 200)")
    parser.add_argument("--max-plot-iteration", type=int, default=2500, help="maximum plotted steps (default: 2500)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.interval_size <= 0:
        print("plot error: --interval-size must be positive", file=sys.stderr)
        return 2
    if args.max_plot_iteration <= 0:
        print("plot error: --max-plot-iteration must be positive", file=sys.stderr)
        return 2
    try:
        loaded = [_session_data(arg, args.method) for arg in args.session_directories]
        colors = [
            (78.0 / 255.0, 121.0 / 255.0, 167.0 / 255.0),
            (255.0 / 255.0, 87.0 / 255.0, 89.0 / 255.0),
            (89.0 / 255.0, 169.0 / 255.0, 79.0 / 255.0),
            (237.0 / 255.0, 201.0 / 255.0, 72.0 / 255.0),
            (242.0 / 255.0, 142.0 / 255.0, 43.0 / 255.0),
            (176.0 / 255.0, 122.0 / 255.0, 161.0 / 255.0),
            (255.0 / 255.0, 157.0 / 255.0, 167.0 / 255.0),
            (118.0 / 255.0, 183.0 / 255.0, 178.0 / 255.0),
            (156.0 / 255.0, 117.0 / 255.0, 95.0 / 255.0),
            (186.0 / 255.0, 176.0 / 255.0, 172.0 / 255.0),
        ]
        fig, ax = plt.subplots()
        ax.set_ylim((0, 1))
        ax.set_ylabel("Grasping performance (success rate)")
        ax.set_xlim((0, args.max_plot_iteration))
        ax.set_xlabel("Number of training steps")
        ax.grid(True, linestyle="-", color=(0.8, 0.8, 0.8))
        for spine in ax.spines.values():
            spine.set_color("#000000")
        handles = []
        labels = []
        for index, (display_name, _session, method, actions, rewards) in enumerate(loaded):
            grasp, after_push = _curves(actions, rewards, method, args.interval_size, args.max_plot_iteration)
            color = colors[index % len(colors)]
            x = np.arange(len(grasp))
            (line,) = ax.plot(x, grasp, color=color, linewidth=3)
            ax.plot(x, after_push, dashes=(8, 7), color=color, linewidth=3, alpha=1.0, label="_nolegend_")
            handles.append(line)
            labels.append(display_name)
        if handles:
            ax.legend(handles, labels, loc="lower right", fontsize=10)
        fig.tight_layout()
        output = Path(args.output).expanduser()
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output)
        except (OSError, ValueError) as exc:
            raise PlotError(f"cannot write plot to {output}: {exc}") from exc
        finally:
            plt.close(fig)
        print(f"wrote {output}")
        return 0
    except PlotError as exc:
        print(f"plot error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
