#!/usr/bin/env python3
"""Plot reward curves stored as .npy files.

The helper adapts the repository's More/plot.py workflow into a safe runtime
script: it scans for .npy files, parses algo/env/seed from the file name,
builds a dataframe, saves a plot, and does not require the original checkout.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

FILE_RE = re.compile(r"(?P<algo>.+)_(?P<env>.+)_(?P<seed>\d+)\.npy$")


def discover_files(path: Path) -> List[Path]:
    return sorted(p for p in path.rglob("*.npy") if p.is_file())


def parse_name(path: Path) -> tuple[str, str, int]:
    match = FILE_RE.match(path.name)
    if not match:
        raise ValueError(f"Expected algo_env_seed.npy file name, got {path.name!r}")
    return match.group("algo"), match.group("env"), int(match.group("seed"))


def build_frame(files: Iterable[Path], steps: int | None = None) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for file_path in files:
        algo, env_name, seed = parse_name(file_path)
        values = np.load(file_path).reshape(-1)
        x = np.linspace(0.0, 1.0, len(values)) if steps is None else np.linspace(0.0, 1.0, steps)
        if steps is not None and len(values) != steps:
            x = np.linspace(0.0, 1.0, len(values))
        frame = pd.DataFrame({
            "Average Return": values,
            "Time Steps (1e6)": x,
            "Algorithm": algo,
            "env": env_name,
            "seed": seed,
        })
        frames.append(frame)
    if not frames:
        raise FileNotFoundError("No .npy files found to plot")
    return pd.concat(frames, axis=0, ignore_index=True)


def make_plot(df: pd.DataFrame, output: Path, title: str | None = None, show: bool = False) -> None:
    sns.set(style="darkgrid")
    plt.figure(figsize=(10, 6))
    try:
        sns.lineplot(x="Time Steps (1e6)", y="Average Return", data=df, hue="Algorithm", errorbar=("ci", 90))
    except TypeError:
        sns.lineplot(x="Time Steps (1e6)", y="Average Return", data=df, hue="Algorithm", ci=90)
    env_name = title or str(df["env"].iloc[0])
    plt.title(env_name)
    plt.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output)
    if show:
        plt.show()
    plt.close()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=Path("."), help="Directory to search recursively for .npy files")
    parser.add_argument("--output", type=Path, default=None, help="Output image path. Defaults to <env>.svg")
    parser.add_argument("--title", default=None, help="Optional plot title override")
    parser.add_argument("--steps", type=int, default=None, help="Optional expected step count for the x-axis grid")
    parser.add_argument("--show", action="store_true", help="Open an interactive window after saving")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    files = discover_files(args.path)
    df = build_frame(files, steps=args.steps)
    env_name = args.title or str(df["env"].iloc[0])
    output = args.output or args.path / f"{env_name}.svg"
    make_plot(df, output, title=args.title, show=args.show)
    print(f"saved plot to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
