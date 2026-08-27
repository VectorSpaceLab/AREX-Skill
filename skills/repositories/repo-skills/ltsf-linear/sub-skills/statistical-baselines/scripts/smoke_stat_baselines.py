#!/usr/bin/env python3
"""Tiny synthetic smoke test for statistical baselines.

The script creates a small custom-format CSV, runs one or more statistical
baselines through run_stat_baselines.py, and checks that numeric outputs were
written. It is intended for fast route validation, not benchmark reporting.
"""

from __future__ import annotations

import argparse
import csv
import math
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

MODEL_CHOICES = ("Naive", "GBRT", "ARIMA", "SARIMA")


def write_fixture(path: Path, rows: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2021, 1, 1)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "feat_a", "feat_b", "OT"])
        for idx in range(rows):
            when = start + timedelta(hours=idx)
            trend = idx / max(rows - 1, 1)
            feat_a = math.sin(idx / 6.0) + 0.1 * trend
            feat_b = math.cos(idx / 9.0) - 0.05 * trend
            target = 0.7 * feat_a + 0.3 * feat_b + 0.01 * idx
            writer.writerow([when.strftime("%Y-%m-%d %H:%M:%S"), f"{feat_a:.8f}", f"{feat_b:.8f}", f"{target:.8f}"])


def find_outputs(work_dir: Path, expected_runs: int) -> None:
    results_root = work_dir / "results"
    metric_files = sorted(results_root.glob("*/metrics.npy"))
    pred_files = sorted(results_root.glob("*/pred.npy"))
    true_files = sorted(results_root.glob("*/true.npy"))
    if len(metric_files) < expected_runs:
        raise SystemExit(f"expected at least {expected_runs} metrics.npy files under {results_root}, found {len(metric_files)}")
    if len(pred_files) < expected_runs or len(true_files) < expected_runs:
        raise SystemExit("missing pred.npy or true.npy outputs from smoke run")

    for metric_file in metric_files:
        metrics = np.load(metric_file, allow_pickle=True)
        numeric = np.asarray(metrics[:6], dtype=float)
        if numeric.shape[0] != 6 or not np.isfinite(numeric).all():
            raise SystemExit(f"non-finite metric values in {metric_file}")

    for pred_file, true_file in zip(pred_files, true_files):
        pred = np.load(pred_file, allow_pickle=True)
        true = np.load(true_file, allow_pickle=True)
        if pred.shape != true.shape:
            raise SystemExit(f"prediction/target shape mismatch: {pred_file} {pred.shape} vs {true_file} {true.shape}")
        if pred.ndim != 3 or pred.shape[1] <= 0 or pred.shape[2] <= 0:
            raise SystemExit(f"unexpected prediction shape in {pred_file}: {pred.shape}")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny synthetic statistical-baseline smoke test")
    parser.add_argument("--repo-root", help="Repository root containing run_stat.py; forwarded to the wrapper when set")
    parser.add_argument("--python", default=sys.executable, help="Python interpreter for the wrapper and run_stat.py")
    parser.add_argument("--models", nargs="+", choices=MODEL_CHOICES, default=["Naive"], help="Model keys to smoke-test")
    parser.add_argument("--rows", type=int, default=160, help="Rows in the synthetic hourly CSV")
    parser.add_argument("--seq-len", type=int, default=16, help="Small look-back window for the smoke")
    parser.add_argument("--label-len", type=int, default=8, help="Small label length for the smoke")
    parser.add_argument("--pred-len", type=int, default=4, help="Small forecast horizon for the smoke")
    parser.add_argument("--batch-size", type=int, default=8, help="Small test batch size")
    parser.add_argument("--sample", type=float, help="Optional sample fraction; omitted uses wrapper model-specific defaults")
    parser.add_argument("--work-dir", help="Existing or new work directory; defaults to a temporary directory")
    parser.add_argument("--keep-tmp", action="store_true", help="Keep the temporary directory after the smoke")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.rows < 80:
        raise SystemExit("--rows should be at least 80 so the custom test split is non-empty")
    if args.seq_len + args.pred_len >= int(args.rows * 0.2):
        raise SystemExit("increase --rows or reduce --seq-len/--pred-len so the custom test split is non-empty")

    wrapper = Path(__file__).resolve().with_name("run_stat_baselines.py")
    if not wrapper.is_file():
        raise SystemExit(f"missing wrapper script: {wrapper}")

    temp_dir_obj = None
    if args.work_dir:
        work_dir = Path(args.work_dir).expanduser().resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
    elif args.keep_tmp:
        work_dir = Path(tempfile.mkdtemp(prefix="stat-baselines-smoke-"))
    else:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="stat-baselines-smoke-")
        work_dir = Path(temp_dir_obj.name).resolve()

    data_root = work_dir / "data"
    data_path = data_root / "synthetic_stat.csv"
    run_dir = work_dir / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_fixture(data_path, args.rows)

    command = [
        args.python,
        str(wrapper),
        "--python",
        args.python,
        "--work-dir",
        str(run_dir),
        "--data-root",
        str(data_root),
        "--data-path",
        data_path.name,
        "--data",
        "custom",
        "--features",
        "M",
        "--target",
        "OT",
        "--seq-len",
        str(args.seq_len),
        "--label-len",
        str(args.label_len),
        "--pred-len",
        str(args.pred_len),
        "--batch-size",
        str(args.batch_size),
        "--num-workers",
        "0",
        "--des",
        "Smoke",
        "--models",
        *args.models,
    ]
    if args.repo_root:
        command.extend(["--repo-root", args.repo_root])
    if args.sample is not None:
        command.extend(["--sample", str(args.sample)])

    print("[stat-baselines-smoke] running wrapper")
    result = subprocess.run(command, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    find_outputs(run_dir, expected_runs=len(args.models))
    print(f"[stat-baselines-smoke] ok: outputs under {run_dir}")

    if temp_dir_obj is not None:
        temp_dir_obj.cleanup()
    elif args.keep_tmp:
        print(f"[stat-baselines-smoke] kept temp directory: {work_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
