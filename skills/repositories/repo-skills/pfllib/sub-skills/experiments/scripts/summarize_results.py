#!/usr/bin/env python3
"""Summarize PFLlib experiment outputs from h5 result files or .out logs.

This helper understands the two common result formats used by the repository:

- h5 files written by `serverbase.save_results()`
- text logs that contain repeated `Best accuracy` blocks

Examples:
  python summarize_results.py results/MNIST_FedAvg_test_0.h5
  python summarize_results.py runs/FedAvg.out
  python summarize_results.py results/*.h5 runs/*.out
"""
from __future__ import annotations

import argparse
from pathlib import Path
from statistics import mean

import h5py
import numpy as np


def load_h5_summary(path: Path) -> tuple[str, float, int]:
    with h5py.File(path, "r") as handle:
        series = np.asarray(handle.get("rs_test_acc", []), dtype=float)
    if series.size == 0:
        raise ValueError(f"{path} does not contain any rs_test_acc values")
    return ("h5", float(series.max()), int(series.size))


def load_out_summary(path: Path) -> tuple[str, float, int]:
    values: list[float] = []
    capture_next = False
    for line in path.read_text().splitlines():
        if capture_next:
            try:
                values.append(float(line.strip()))
            except ValueError:
                pass
            capture_next = False
        elif "Best accuracy" in line:
            capture_next = True
    if not values:
        raise ValueError(f"{path} does not contain any parsable Best accuracy entries")
    return ("out", max(values), len(values))


def expand_inputs(paths: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            expanded.extend(sorted(path.glob("*.h5")))
            expanded.extend(sorted(path.glob("*.out")))
        else:
            expanded.append(path)
    return expanded


def summarize(path: Path) -> tuple[str, float, int]:
    suffix = path.suffix.lower()
    if suffix == ".h5":
        return load_h5_summary(path)
    if suffix == ".out":
        return load_out_summary(path)
    raise ValueError(f"unsupported result file type: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="One or more h5 result files, .out logs, or directories containing them.")
    args = parser.parse_args()

    files = expand_inputs(args.paths)
    if not files:
        print("error: no result files found", flush=True)
        return 2

    best_values: list[float] = []
    for path in files:
        if not path.exists():
            print(f"error: missing file: {path}", flush=True)
            return 2
        try:
            kind, best, count = summarize(path)
        except Exception as exc:  # pragma: no cover - surfaced to the user
            print(f"error: {path}: {exc}", flush=True)
            return 1
        best_values.append(best)
        print(f"{path} [{kind}] runs={count} best_accuracy={best:.6f}")

    print(f"mean_best_accuracy={mean(best_values):.6f}")
    print(f"std_best_accuracy={np.std(best_values):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
