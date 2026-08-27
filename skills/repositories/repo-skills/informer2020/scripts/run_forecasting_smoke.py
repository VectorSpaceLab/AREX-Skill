#!/usr/bin/env python3
"""Generate a tiny custom CSV and dry-run or execute an Informer2020 smoke run.

The default is safe: it writes a small fixture and prints the exact command but
DOES NOT launch training. Add --execute to run the source forecasting CLI from a
repo checkout, using this helper's tiny settings.

Examples:
  python run_forecasting_smoke.py --repo-root /path/to/Informer2020 --work-dir /tmp/informer-smoke
  python run_forecasting_smoke.py --repo-root . --work-dir /tmp/informer-smoke --execute --backend cpu --do-predict
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import shlex
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or execute a tiny Informer2020 custom-data smoke run")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Path to an Informer2020 checkout; defaults to current directory")
    parser.add_argument("--work-dir", type=Path, default=Path("informer2020-smoke"), help="Directory for generated data, checkpoints, and results")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run the repo CLI")
    parser.add_argument("--execute", action="store_true", help="Actually run training/testing; otherwise only print the command")
    parser.add_argument("--backend", choices=["cpu", "cuda", "auto"], default="cpu", help="Backend selection for the launched smoke command")
    parser.add_argument("--do-predict", action="store_true", help="Also request future prediction output")
    parser.add_argument("--model", choices=["informer", "informerstack"], default="informer", help="Model family")
    parser.add_argument("--features", choices=["S", "M", "MS"], default="M", help="Forecasting feature mode")
    parser.add_argument("--rows", type=int, default=160, help="Rows in the generated tiny CSV")
    parser.add_argument("--covariates", type=int, default=2, help="Number of non-target feature columns in the generated CSV")
    parser.add_argument("--target", default="target", help="Target column name")
    parser.add_argument("--freq", default="h", help="Frequency passed to the repo CLI and fixture generator")
    parser.add_argument("--start", default="2021-01-01", help="Start timestamp for generated data")
    parser.add_argument("--seq-len", type=int, default=16, help="Smoke encoder length")
    parser.add_argument("--label-len", type=int, default=8, help="Smoke decoder label length")
    parser.add_argument("--pred-len", type=int, default=4, help="Smoke prediction horizon")
    parser.add_argument("--batch-size", type=int, default=4, help="Smoke batch size")
    parser.add_argument("--train-epochs", type=int, default=1, help="Smoke epoch cap")
    parser.add_argument("--itr", type=int, default=1, help="Smoke repeat count")
    parser.add_argument("--des", default="skill_smoke", help="Experiment description string")
    parser.add_argument("--attn", choices=["prob", "full"], default="prob", help="Attention mode")
    parser.add_argument("--embed", choices=["timeF", "fixed", "learned"], default="timeF", help="Time embedding mode")
    return parser.parse_args()


def make_fixture(path: Path, rows: int, freq: str, start: str, covariates: int, target: str) -> None:
    if rows <= 0:
        raise SystemExit("--rows must be positive")
    if covariates < 0:
        raise SystemExit("--covariates must be non-negative")
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - user-facing guard
        raise SystemExit("pandas is required to generate the smoke CSV") from exc
    try:
        dates = pd.date_range(start, periods=rows, freq=freq)
    except Exception as exc:
        raise SystemExit(f"Could not generate dates for freq={freq!r}: {exc}") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date"] + [f"feat_{idx}" for idx in range(covariates)] + [target]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        denom = max(rows - 1, 1)
        for i, timestamp in enumerate(dates):
            trend = i / denom
            row = {"date": timestamp.isoformat()}
            cov_values = []
            for idx in range(covariates):
                value = math.sin(i / (5.0 + idx)) + math.cos(i / (9.0 + idx)) + (idx + 1) * 0.05 * trend
                cov_values.append(value)
                row[f"feat_{idx}"] = f"{value:.6f}"
            if cov_values:
                target_value = 0.6 * cov_values[0] + 0.2 * cov_values[-1] + 0.1 * math.sin(i / 11.0) + 0.2 * trend
            else:
                target_value = math.sin(i / 7.0) + 0.2 * trend
            row[target] = f"{target_value:.6f}"
            writer.writerow(row)


def dimensions(features: str, total_channels: int) -> tuple[int, int, int]:
    if features == "S":
        return 1, 1, 1
    if features == "M":
        return total_channels, total_channels, total_channels
    return total_channels, total_channels, 1


def build_command(args: argparse.Namespace, repo_root: Path, data_file: Path, work_dir: Path) -> list[str]:
    enc_in, dec_in, c_out = dimensions(args.features, args.covariates + 1)
    main_path = repo_root / "main_informer.py"
    checkpoints = work_dir / "checkpoints"
    cmd = [
        args.python,
        str(main_path),
        "--model", args.model,
        "--data", "custom",
        "--root_path", str(data_file.parent),
        "--data_path", data_file.name,
        "--features", args.features,
        "--target", args.target,
        "--freq", args.freq,
        "--checkpoints", str(checkpoints),
        "--seq_len", str(args.seq_len),
        "--label_len", str(args.label_len),
        "--pred_len", str(args.pred_len),
        "--enc_in", str(enc_in),
        "--dec_in", str(dec_in),
        "--c_out", str(c_out),
        "--d_model", "16",
        "--n_heads", "2",
        "--e_layers", "1",
        "--d_layers", "1",
        "--s_layers", "1",
        "--d_ff", "32",
        "--factor", "1",
        "--attn", args.attn,
        "--embed", args.embed,
        "--dropout", "0.0",
        "--num_workers", "0",
        "--itr", str(args.itr),
        "--train_epochs", str(args.train_epochs),
        "--batch_size", str(args.batch_size),
        "--patience", "1",
        "--learning_rate", "0.001",
        "--des", args.des,
    ]
    if args.do_predict:
        cmd.append("--do_predict")
    return cmd


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    work_dir = args.work_dir.expanduser().resolve()
    main_path = repo_root / "main_informer.py"
    if not main_path.exists():
        raise SystemExit(f"Could not find main_informer.py under repo root: {repo_root}")

    work_dir.mkdir(parents=True, exist_ok=True)
    data_file = work_dir / "data" / "tiny_informer_custom.csv"
    make_fixture(data_file, args.rows, args.freq, args.start, args.covariates, args.target)
    cmd = build_command(args, repo_root, data_file, work_dir)

    printable = " ".join(shlex.quote(part) for part in cmd)
    print(f"Generated fixture: {data_file}")
    print(f"Work directory: {work_dir}")
    print("Smoke command:")
    print(printable)

    if not args.execute:
        print("Dry run only. Add --execute to launch the smoke training/testing command.")
        return 0

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    if args.backend == "cpu":
        env["CUDA_VISIBLE_DEVICES"] = ""
    elif args.backend == "cuda":
        env.pop("CUDA_VISIBLE_DEVICES", None)

    result = subprocess.run(cmd, cwd=work_dir, env=env)
    if result.returncode != 0:
        return result.returncode

    results_dir = work_dir / "results"
    print(f"Smoke run completed. Results directory: {results_dir}")
    if results_dir.exists():
        for path in sorted(results_dir.rglob("*.npy")):
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
