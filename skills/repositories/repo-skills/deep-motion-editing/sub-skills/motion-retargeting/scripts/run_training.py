#!/usr/bin/env python3
"""Construct or explicitly run retargeting training from a user checkout.

No environment setup, download, checkpoint creation, or training occurs unless
``--run`` is supplied. The default command is a dry run after layout checks.
"""
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Safely construct or run retargeting train.py.")
    p.add_argument("--repo-root", type=Path, required=True, help="user-supplied repository root or its retargeting directory")
    p.add_argument("--save-dir", type=Path, default=Path("./training"), help="training output directory (upstream example: ./training/)")
    p.add_argument("--dataset-root", type=Path, help="optional Mixamo-style root to check before training")
    p.add_argument("--cuda-device", default="cuda:0", help="requested device (option parser default: cuda:0)")
    p.add_argument("--python", dest="python_executable", default=sys.executable, help="Python executable for the user checkout")
    p.add_argument("--window-size", type=int, default=64, help="time window; upstream default is 64")
    p.add_argument("--rotation", choices=("quaternion", "euler_angle"), default="quaternion")
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--epoch-num", type=int, default=20001)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--num-layers", type=int, default=2)
    p.add_argument("--dataset", default="Mixamo", help="parser dataset label; character lists remain hard-coded in datasets/__init__.py")
    p.add_argument("--extra-arg", action="append", default=[], metavar="ARG=VALUE", help="additional literal train.py option, repeatable")
    p.add_argument("--skip-data-check", action="store_true", help="construct without checking dataset-root contents")
    p.add_argument("--run", action="store_true", help="execute the command; otherwise print it only")
    return p


def locate_retargeting(root: Path) -> Path:
    root = root.expanduser().resolve()
    if (root / "train.py").is_file() and (root / "option_parser.py").is_file():
        return root
    candidate = root / "retargeting"
    if (candidate / "train.py").is_file() and (candidate / "option_parser.py").is_file():
        return candidate
    raise ValueError("--repo-root must contain retargeting/train.py and retargeting/option_parser.py")


def _check_data(root: Path) -> list[str]:
    if not root.is_dir():
        return [f"dataset root is not a directory: {root}"]
    errors = [str(p) for p in (root / "train_list.txt", root / "test_list.txt") if not p.is_file()]
    chars = [p for p in root.iterdir() if p.is_dir() and p.name not in {"std_bvhs", "mean_var"} and not p.name.startswith(".")]
    if not chars:
        errors.append(f"{root} has no character directories")
    for directory in chars:
        if not list(directory.glob("*.npy")) and not list(directory.glob("*.bvh")):
            errors.append(f"{directory} has neither .npy nor .bvh data")
    for directory, pattern in ((root / "std_bvhs", "*.bvh"), (root / "mean_var", "*_mean.npy")):
        if not directory.is_dir() or not list(directory.glob(pattern)):
            errors.append(f"missing generated preprocessing artifacts under {directory} ({pattern})")
    return errors


def _extra_args(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if not value.startswith("--"):
            raise ValueError(f"--extra-arg must begin with --: {value!r}")
        if "=" in value:
            key, val = value.split("=", 1)
            result.extend([key, val])
        else:
            result.append(value)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        retargeting = locate_retargeting(args.repo_root)
        if args.python_executable != sys.executable and not Path(args.python_executable).is_file() and shutil.which(args.python_executable) is None:
            raise ValueError(f"cannot find --python executable: {args.python_executable}")
        if args.window_size <= 0 or args.batch_size <= 0 or args.epoch_num <= 0 or args.num_layers <= 0:
            raise ValueError("window-size, batch-size, epoch-num, and num-layers must be positive")
        dataset_root = args.dataset_root.expanduser().resolve() if args.dataset_root else retargeting / "datasets" / "Mixamo"
        if not args.skip_data_check:
            errors = _check_data(dataset_root)
            if errors:
                raise ValueError("incomplete training dataset layout; missing or invalid:\n  " + "\n  ".join(errors) + "\nUse --skip-data-check only for command construction.")
        save_dir = args.save_dir.expanduser().resolve()
        command = [args.python_executable, "train.py", "--save_dir", str(args.save_dir), "--cuda_device", args.cuda_device,
                   "--window_size", str(args.window_size), "--rotation", args.rotation, "--batch_size", str(args.batch_size),
                   "--epoch_num", str(args.epoch_num), "--learning_rate", str(args.learning_rate), "--num_layers", str(args.num_layers),
                   "--dataset", args.dataset]
        command.extend(_extra_args(args.extra_arg))
    except (ValueError, OSError) as exc:
        print(f"training preflight error: {exc}", file=sys.stderr)
        return 2
    print("Command:", shlex.join(command))
    print("Working directory:", retargeting)
    print("Expected output:", save_dir)
    if not args.run:
        print("Dry run: no training, downloads, environment changes, or files were created.")
        return 0
    save_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(command, cwd=retargeting, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"upstream training command failed with exit status {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1
    if not (save_dir / "para.txt").is_file():
        print(f"training returned but expected configuration record is absent: {save_dir / 'para.txt'}", file=sys.stderr)
        return 3
    print(f"Training command completed; configuration record: {save_dir / 'para.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
