#!/usr/bin/env python3
"""Build a safe imgclsmob train/eval command plan without importing a backend."""

from __future__ import annotations

import argparse
import shlex
import sys


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Build a no-download imgclsmob classification command plan.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--framework", choices=("gluon", "pytorch"), required=True)
    p.add_argument("--mode", choices=("train", "eval"), required=True)
    p.add_argument("--dataset", default=None, help="exact dataset metainfo name")
    p.add_argument("--data-dir", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--resume")
    p.add_argument("--resume-state")
    p.add_argument("--start-epoch", type=int)
    p.add_argument("--num-gpus", type=int, default=0)
    p.add_argument("--num-data-workers", type=int, default=0)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--save-dir")
    p.add_argument("--data-subset", choices=("val", "test"), default="val")
    p.add_argument("--use-pretrained", action="store_true")
    p.add_argument("--not-show-progress", action="store_true")
    p.add_argument("--remove-module", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    dataset = args.dataset or ("ImageNet1K_rec" if args.framework == "gluon" else "ImageNet1K")
    if args.framework == "pytorch" and dataset == "ImageNet1K_rec":
        print("ERROR: ImageNet1K_rec is Gluon-only; choose ImageNet1K for PyTorch", file=sys.stderr)
        return 2
    if args.num_gpus < 0 or args.num_data_workers < 0 or args.batch_size <= 0:
        print("ERROR: device/worker counts must be nonnegative and batch size must be positive", file=sys.stderr)
        return 2
    if args.mode == "eval" and args.resume_state:
        print("ERROR: --resume-state is a training-state option; omit it for eval", file=sys.stderr)
        return 2
    if args.use_pretrained and args.resume:
        print("ERROR: choose --use-pretrained or --resume for an offline-safe plan", file=sys.stderr)
        return 2
    if args.start_epoch is not None and args.start_epoch < 1:
        print("ERROR: --start-epoch is 1-based and must be positive", file=sys.stderr)
        return 2

    executable = "train_gl.py" if args.framework == "gluon" and args.mode == "train" else None
    if executable is None:
        if args.framework == "gluon" and args.mode == "eval":
            executable = "eval_gl.py"
        elif args.framework == "pytorch" and args.mode == "train":
            executable = "train_pt.py"
        else:
            executable = "eval_pt.py"
    command = ["python", executable, "--dataset", dataset, "--data-dir", args.data_dir,
               "--model", args.model, "--num-gpus", str(args.num_gpus),
               "--num-data-workers", str(args.num_data_workers), "--batch-size", str(args.batch_size)]
    if args.mode == "eval":
        command += ["--data-subset", args.data_subset]
    if args.resume:
        command += ["--resume", args.resume]
    if args.resume_state:
        command += ["--resume-state", args.resume_state]
    if args.start_epoch is not None:
        command += ["--start-epoch", str(args.start_epoch)]
    if args.save_dir:
        command += ["--save-dir", args.save_dir]
    if args.use_pretrained:
        command.append("--use-pretrained")
    if args.framework == "gluon" and args.mode == "eval" and args.not_show_progress:
        command.append("--not-show-progress")
    if args.framework == "pytorch" and args.mode == "eval" and args.remove_module:
        command.append("--remove-module")

    print("status: VALID COMMAND PLAN")
    print("network: pretrained weights are {}".format("requested" if args.use_pretrained else "not requested"))
    print("command: " + " ".join(shlex.quote(part) for part in command))
    print("next: run dataset preflight, then execute the repository CLI only in an environment that provides it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
