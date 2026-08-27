#!/usr/bin/env python3
"""Safe wrapper for the repository's run_stat.py statistical baselines.

The wrapper can launch a single baseline run or an adapted version of the
source Stat_Long.sh sweep. It keeps slow ARIMA/SARIMA sampling explicit and can
run from a separate work directory so generated result files do not have to land
in the repository root.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

MODEL_CHOICES = ("Naive", "GBRT", "ARIMA", "SARIMA")


@dataclass(frozen=True)
class PresetDataset:
    label: str
    data: str
    data_path: str
    seq_len: int
    label_len: int
    pred_lens: Sequence[int]
    batch_size: int = 100
    features: str = "M"
    target: str = "OT"
    freq: str = "h"


STAT_LONG_PRESETS = (
    PresetDataset("ETTh1", "ETTh1", "ETTh1.csv", 96, 48, (96, 192, 336, 720)),
    PresetDataset("ETTh2", "ETTh2", "ETTh2.csv", 96, 48, (96, 192, 336, 720)),
    PresetDataset("ETTm1", "ETTm1", "ETTm1.csv", 96, 48, (96, 192, 336, 720)),
    PresetDataset("ETTm2", "ETTm2", "ETTm2.csv", 96, 48, (96, 192, 336, 720), batch_size=300),
    PresetDataset("exchange_rate", "custom", "exchange_rate.csv", 96, 48, (96, 192, 336, 720)),
    PresetDataset("weather", "custom", "weather.csv", 96, 48, (96, 192, 336, 720)),
    PresetDataset("electricity", "custom", "electricity.csv", 96, 48, (96, 192, 336, 720)),
    PresetDataset("traffic", "custom", "traffic.csv", 96, 48, (96, 192, 336, 720)),
    PresetDataset("ili", "custom", "national_illness.csv", 36, 18, (24, 36, 48, 60)),
)


@dataclass(frozen=True)
class RunTask:
    label: str
    model: str
    data: str
    data_root: Path
    data_path: str
    features: str
    target: str
    seq_len: int
    label_len: int
    pred_len: int
    batch_size: int
    sample: float
    freq: str
    embed: str
    itr: int
    des: str
    model_id: str
    num_workers: int


def find_repo_root(start: Path) -> Optional[Path]:
    """Find a repository root containing run_stat.py and models/Stat_models.py."""
    start = start.resolve()
    candidates = [start]
    if start.is_file():
        candidates = [start.parent]
    for directory in candidates[0:1] + list(candidates[0].parents):
        if (directory / "run_stat.py").is_file() and (directory / "models" / "Stat_models.py").is_file():
            return directory
    return None


def resolve_repo_root(value: Optional[str]) -> Path:
    if value:
        root = Path(value).expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        root = root.resolve()
        if not (root / "run_stat.py").is_file():
            raise SystemExit(f"repo root does not contain run_stat.py: {root}")
        if not (root / "models" / "Stat_models.py").is_file():
            raise SystemExit(f"repo root does not contain models/Stat_models.py: {root}")
        return root

    for start in (Path.cwd(), Path(__file__).resolve()):
        found = find_repo_root(start)
        if found is not None:
            return found
    raise SystemExit("could not auto-detect repo root; pass --repo-root")


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-") or "run"


def model_default_sample(model: str) -> float:
    if model == "SARIMA":
        return 0.005
    if model == "ARIMA":
        return 0.01
    return 1.0


def effective_sample(model: str, requested: Optional[float], allow_slow: bool) -> float:
    sample = model_default_sample(model) if requested is None else requested
    if sample <= 0 or sample > 1:
        raise SystemExit(f"--sample must be in (0, 1], got {sample}")
    if not allow_slow:
        if model == "ARIMA" and sample > 0.1:
            raise SystemExit("ARIMA with --sample > 0.1 is likely slow; lower --sample or pass --allow-slow")
        if model == "SARIMA" and sample > 0.01:
            raise SystemExit("SARIMA with --sample > 0.01 is likely very slow; lower --sample or pass --allow-slow")
    return sample


def build_model_ids(label: str, seq_len: int, pred_len: int) -> str:
    return f"{safe_slug(label)}_{seq_len}_{pred_len}"


def iter_models(args: argparse.Namespace) -> List[str]:
    models = args.models if args.models else [args.model]
    unknown = [model for model in models if model not in MODEL_CHOICES]
    if unknown:
        raise SystemExit(f"unsupported model(s): {', '.join(unknown)}")
    return models


def make_single_tasks(args: argparse.Namespace, data_root: Path) -> List[RunTask]:
    pred_lens = args.pred_lens if args.pred_lens else [args.pred_len]
    tasks: List[RunTask] = []
    for model in iter_models(args):
        sample = effective_sample(model, args.sample, args.allow_slow)
        for pred_len in pred_lens:
            model_id = args.model_id or build_model_ids(Path(args.data_path).stem, args.seq_len, pred_len)
            tasks.append(
                RunTask(
                    label=Path(args.data_path).stem,
                    model=model,
                    data=args.data,
                    data_root=data_root,
                    data_path=args.data_path,
                    features=args.features,
                    target=args.target,
                    seq_len=args.seq_len,
                    label_len=args.label_len,
                    pred_len=pred_len,
                    batch_size=args.batch_size,
                    sample=sample,
                    freq=args.freq,
                    embed=args.embed,
                    itr=args.itr,
                    des=args.des,
                    model_id=model_id,
                    num_workers=args.num_workers,
                )
            )
    return tasks


def make_sweep_tasks(args: argparse.Namespace, data_root: Path) -> List[RunTask]:
    requested = set(args.datasets or [])
    presets = [preset for preset in STAT_LONG_PRESETS if not requested or preset.label in requested]
    if requested and len(presets) != len(requested):
        known = ", ".join(preset.label for preset in STAT_LONG_PRESETS)
        raise SystemExit(f"unknown --datasets entry; known labels: {known}")

    tasks: List[RunTask] = []
    for preset in presets:
        pred_lens = args.pred_lens if args.pred_lens else list(preset.pred_lens)
        for model in iter_models(args):
            sample = effective_sample(model, args.sample, args.allow_slow)
            for pred_len in pred_lens:
                tasks.append(
                    RunTask(
                        label=preset.label,
                        model=model,
                        data=preset.data,
                        data_root=data_root,
                        data_path=preset.data_path,
                        features=preset.features,
                        target=preset.target,
                        seq_len=preset.seq_len,
                        label_len=preset.label_len,
                        pred_len=pred_len,
                        batch_size=preset.batch_size,
                        sample=sample,
                        freq=preset.freq,
                        embed=args.embed,
                        itr=args.itr,
                        des=args.des,
                        model_id=build_model_ids(preset.label, preset.seq_len, pred_len),
                        num_workers=args.num_workers,
                    )
                )
    return tasks


def build_command(task: RunTask, repo_root: Path, python: str) -> List[str]:
    return [
        python,
        "-u",
        str(repo_root / "run_stat.py"),
        "--is_training",
        "1",
        "--model_id",
        task.model_id,
        "--model",
        task.model,
        "--data",
        task.data,
        "--root_path",
        str(task.data_root),
        "--data_path",
        task.data_path,
        "--features",
        task.features,
        "--target",
        task.target,
        "--seq_len",
        str(task.seq_len),
        "--label_len",
        str(task.label_len),
        "--pred_len",
        str(task.pred_len),
        "--batch_size",
        str(task.batch_size),
        "--sample",
        str(task.sample),
        "--freq",
        task.freq,
        "--embed",
        task.embed,
        "--num_workers",
        str(task.num_workers),
        "--des",
        task.des,
        "--itr",
        str(task.itr),
    ]


def validate_data(tasks: Iterable[RunTask], dry_run: bool, skip_data_check: bool) -> None:
    if dry_run or skip_data_check:
        return
    missing = []
    for task in tasks:
        path = task.data_root / task.data_path
        if not path.is_file():
            missing.append(str(path))
    if missing:
        unique = sorted(set(missing))
        raise SystemExit("missing data file(s):\n" + "\n".join(unique))


def run_command(command: Sequence[str], cwd: Path, log_path: Path, env: dict) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            log_file.write(line)
        return process.wait()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    labels = [preset.label for preset in STAT_LONG_PRESETS]
    parser = argparse.ArgumentParser(description="Run repository statistical baselines safely")
    parser.add_argument("--repo-root", help="Repository root containing run_stat.py; auto-detected from cwd when omitted")
    parser.add_argument("--work-dir", help="Working directory for result.txt/results/test_results; defaults to repo root")
    parser.add_argument("--python", default=sys.executable, help="Python interpreter used to run run_stat.py")
    parser.add_argument("--sweep", choices=("none", "stat-long"), default="none", help="Run an adapted source statistical sweep")
    parser.add_argument("--datasets", nargs="+", choices=labels, help="Dataset labels for --sweep stat-long")
    parser.add_argument("--model", choices=MODEL_CHOICES, default="Naive", help="Single model key when --models is not used")
    parser.add_argument("--models", nargs="+", choices=MODEL_CHOICES, help="One or more statistical model keys")
    parser.add_argument("--data", default="custom", help="run_stat.py --data value for single-run mode")
    parser.add_argument("--data-root", "--root-path", dest="data_root", default="dataset", help="Directory containing --data-path; relative paths resolve against repo root")
    parser.add_argument("--data-path", default="exchange_rate.csv", help="CSV file name under --data-root for single-run mode")
    parser.add_argument("--features", choices=("M", "S", "MS"), default="M", help="Forecasting feature mode")
    parser.add_argument("--target", default="OT", help="Target column for S/MS modes")
    parser.add_argument("--seq-len", type=int, default=96, help="Input sequence length for single-run mode")
    parser.add_argument("--label-len", type=int, default=48, help="Label length carried by the data loader")
    parser.add_argument("--pred-len", type=int, default=96, help="Prediction length for single-run mode")
    parser.add_argument("--pred-lens", nargs="+", type=int, help="Prediction lengths; overrides defaults in sweep mode")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for single-run mode")
    parser.add_argument("--sample", type=float, help="Per-batch sampling fraction; safe defaults depend on model when omitted")
    parser.add_argument("--allow-slow", action="store_true", help="Allow large ARIMA/SARIMA samples")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers; 0 is safest for smoke runs")
    parser.add_argument("--freq", default="h", help="Time feature frequency for single-run mode")
    parser.add_argument("--embed", default="timeF", help="Embedding/time-feature mode passed through to run_stat.py")
    parser.add_argument("--des", default="Exp", help="Description suffix used in the setting string")
    parser.add_argument("--itr", type=int, default=1, help="Iteration count argument retained for source compatibility")
    parser.add_argument("--model-id", help="Explicit model_id for single-run mode; ignored in sweep mode")
    parser.add_argument("--log-dir", default="logs/LongForecasting", help="Log directory relative to work-dir unless absolute")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    parser.add_argument("--print-command", action="store_true", help="Print each command before execution")
    parser.add_argument("--skip-data-check", action="store_true", help="Do not check that data files exist before execution")
    parser.add_argument("--continue-on-failure", action="store_true", help="Run remaining tasks after a failed command")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = resolve_repo_root(args.repo_root)
    work_dir = resolve_path(args.work_dir, Path.cwd()) if args.work_dir else repo_root
    work_dir.mkdir(parents=True, exist_ok=True)
    data_root = resolve_path(args.data_root, repo_root)
    log_dir = resolve_path(args.log_dir, work_dir)

    if args.sweep == "stat-long":
        tasks = make_sweep_tasks(args, data_root)
    else:
        tasks = make_single_tasks(args, data_root)

    validate_data(tasks, args.dry_run, args.skip_data_check)

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(repo_root) if not existing_pythonpath else str(repo_root) + os.pathsep + existing_pythonpath

    failures = 0
    for index, task in enumerate(tasks, start=1):
        command = build_command(task, repo_root, args.python)
        log_name = f"{safe_slug(task.model)}_{safe_slug(task.label)}_{task.pred_len}.log"
        log_path = log_dir / log_name
        if args.dry_run or args.print_command:
            print(shlex.join(command))
        if args.dry_run:
            continue
        print(f"[stat-baselines] running {index}/{len(tasks)}: {task.model} {task.label} pred_len={task.pred_len}")
        print(f"[stat-baselines] log: {log_path}")
        code = run_command(command, work_dir, log_path, env)
        if code != 0:
            failures += 1
            print(f"[stat-baselines] failed with exit code {code}: {task.model} {task.label} pred_len={task.pred_len}", file=sys.stderr)
            if not args.continue_on_failure:
                return code
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
