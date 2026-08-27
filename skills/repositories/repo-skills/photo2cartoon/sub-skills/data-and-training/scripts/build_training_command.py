#!/usr/bin/env python3
"""Build a guarded Photo2Cartoon training/test command.

This helper is a safe replacement for copying source train.py commands into an
agent response. It validates the target checkout, dataset layout, and key assets,
then prints the exact command. It executes only with --execute.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List

SPLITS = ("trainA", "trainB", "testA", "testB")


def bool_arg(value: bool) -> str:
    return "true" if value else "false"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or execute a guarded Photo2Cartoon train.py command.")
    parser.add_argument("--repo-root", required=True, type=Path, help="Target Photo2Cartoon checkout root.")
    parser.add_argument("--dataset", default="photo2cartoon", help="Dataset name under <repo-root>/dataset/.")
    parser.add_argument("--dataset-root", type=Path, help="Explicit dataset root; default is <repo-root>/dataset/<dataset>.")
    parser.add_argument("--phase", choices=("train", "test"), default="train")
    parser.add_argument("--pretrained-weights", type=Path, help="Optional pretrained checkpoint path.")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gpu-ids", nargs="+", type=int, default=[0])
    parser.add_argument("--iteration", type=int, default=None)
    parser.add_argument("--resume", action="store_true", help="Pass --resume true to train.py.")
    parser.add_argument("--light", choices=("true", "false"), default=None, help="Override train.py --light.")
    parser.add_argument("--img-size", type=int, default=None)
    parser.add_argument("--ch", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--faceid-weight", type=float, default=None)
    parser.add_argument("--extra-arg", action="append", default=[], help="Additional raw train.py argument token; repeat for each token.")
    parser.add_argument("--python", default=sys.executable, help="Python executable for --execute.")
    parser.add_argument("--execute", action="store_true", help="Actually run the command. Default only prints and validates.")
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    train_script = repo_root / "train.py"
    dataset_root = (args.dataset_root or repo_root / "dataset" / args.dataset).expanduser()
    face_model = repo_root / "models" / "model_mobilefacenet.pth"

    problems: List[str] = []
    warnings: List[str] = []
    if not repo_root.is_dir():
        problems.append(f"repo root is not a directory: {repo_root}")
    if not train_script.is_file():
        problems.append(f"missing source-compatible training entrypoint: {train_script}")
    if not dataset_root.is_dir():
        problems.append(f"dataset root is not a directory: {dataset_root}")
    else:
        for split in SPLITS:
            split_dir = dataset_root / split
            if not split_dir.is_dir():
                problems.append(f"missing required split directory: {split_dir}")
    if args.phase == "train" and not face_model.is_file():
        warnings.append(f"missing Face ID model used during training: {face_model}")
    if args.pretrained_weights and not args.pretrained_weights.expanduser().is_file():
        problems.append(f"pretrained checkpoint is not a file: {args.pretrained_weights}")
    if args.batch_size > 1:
        warnings.append("repo docs still recommend batch_size=1; larger batches can quickly exhaust GPU memory")

    cmd = [args.python, str(train_script), "--phase", args.phase, "--dataset", args.dataset, "--batch_size", str(args.batch_size), "--gpu_ids", *map(str, args.gpu_ids)]
    if args.pretrained_weights:
        cmd.extend(["--pretrained_weights", str(args.pretrained_weights.expanduser())])
    if args.iteration is not None:
        cmd.extend(["--iteration", str(args.iteration)])
    if args.resume:
        cmd.extend(["--resume", "true"])
    if args.light is not None:
        cmd.extend(["--light", args.light])
    if args.img_size is not None:
        cmd.extend(["--img_size", str(args.img_size)])
    if args.ch is not None:
        cmd.extend(["--ch", str(args.ch)])
    if args.lr is not None:
        cmd.extend(["--lr", str(args.lr)])
    if args.faceid_weight is not None:
        cmd.extend(["--faceid_weight", str(args.faceid_weight)])
    cmd.extend(args.extra_arg)

    print("training command:", " ".join(cmd))
    print(f"dataset root expected by train.py: {repo_root / 'dataset' / args.dataset}")
    if dataset_root != repo_root / "dataset" / args.dataset:
        warnings.append("train.py resolves datasets under <repo-root>/dataset/<dataset>; symlink or copy your explicit --dataset-root there before execution")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if problems:
        print("problems:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    if not args.execute:
        print("dry-run only; add --execute after dependencies, GPU, assets, and dataset layout are verified")
        return 0 if not warnings else 2

    if warnings:
        print("refusing to execute until warnings are resolved")
        return 2
    completed = subprocess.run(cmd, cwd=str(repo_root), check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
