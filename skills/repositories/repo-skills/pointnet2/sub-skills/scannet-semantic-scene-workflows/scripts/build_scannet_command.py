#!/usr/bin/env python3
"""Emit legacy PointNet2 ScanNet workflow commands without executing them."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import List, Optional, Sequence


def q(value: object) -> str:
    return shlex.quote(str(value))


def shell_join(parts: Sequence[object]) -> str:
    return " ".join(q(p) for p in parts)


def scannet_workdir(repo_root: str) -> str:
    return str(Path(repo_root) / "scannet")


def preprocessing_workdir(repo_root: str) -> str:
    return str(Path(repo_root) / "scannet" / "preprocessing")


def emit_train(args: argparse.Namespace) -> None:
    workdir = scannet_workdir(args.repo_root)
    env_parts: List[str] = []
    if args.visible_gpus:
        env_parts.append("CUDA_VISIBLE_DEVICES=%s" % q(args.visible_gpus))
    if args.pythonpath is None:
        # Keep the shell parameter expansion live so an existing PYTHONPATH is appended.
        env_parts.append('PYTHONPATH="../models:../utils:..${PYTHONPATH:+:$PYTHONPATH}"')
    else:
        env_parts.append("PYTHONPATH=%s" % q(args.pythonpath))

    cmd = [
        args.python,
        "train.py",
        "--gpu", args.gpu,
        "--model", args.model,
        "--log_dir", args.log_dir,
        "--num_point", args.num_point,
        "--max_epoch", args.max_epoch,
        "--batch_size", args.batch_size,
        "--learning_rate", args.learning_rate,
        "--momentum", args.momentum,
        "--optimizer", args.optimizer,
        "--decay_step", args.decay_step,
        "--decay_rate", args.decay_rate,
    ]

    print("# Legacy ScanNet semantic segmentation train/eval command")
    print("# Preconditions: Python 2.7 + TensorFlow 1.x, data/scannet_data_pointnet2 pickles, and PointNet++ custom ops if running the full semantic model.")
    print("# The command runs from scannet/ so raw trainer relative copies and data paths match the legacy script.")
    print("# If MODEL_FILE backup prints a cp warning, ensure %s.py is visible in this workdir or keep PYTHONPATH pointing at ../models." % args.model)
    print("cd %s && %s %s" % (q(workdir), " ".join(env_parts), shell_join(cmd)))


def emit_preprocess(args: argparse.Namespace) -> None:
    workdir = preprocessing_workdir(args.repo_root)
    steps = [args.step] if args.step != "all" else ["fetch-labels", "collect", "demo"]
    print("# Legacy ScanNet preprocessing recipe commands")
    print("# Preconditions: original ScanNet download, scannet_all.txt scene list, correct V1/V2 label TSV, and edited/wrapped raw paths.")
    print("# Validate raw root, label TSV, generated .npy files, and demo outputs with validate_scannet_layout.py before relying on artifacts.")
    for step in steps:
        if step == "fetch-labels":
            print("# fetch-labels scans aggregation JSON files and writes class_names.txt; its raw path is hard-coded in the legacy script.")
            print("cd %s && %s" % (q(workdir), shell_join([args.python, "fetch_label_names.py"])))
        elif step == "collect":
            print("# collect expects SCANNET_DIR, scannet_all.txt, and scannet-labels.combined.tsv in the preprocessing working directory unless patched.")
            print("cd %s && %s" % (q(workdir), shell_join([args.python, "collect_scannet_scenes.py"])))
        elif step == "demo":
            print("# demo expects scannet_scenes/scene0001_01.npy and writes demo_output/{scene.obj,scene_instance.obj,scene_semantic.obj}.")
            print("cd %s && %s" % (q(workdir), shell_join([args.python, "demo.py"])))
        else:  # pragma: no cover - argparse choices prevent this
            raise ValueError(step)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build PointNet2 ScanNet legacy commands without executing them.")
    sub = parser.add_subparsers(dest="command", required=True)

    train = sub.add_parser("train", help="Emit the ScanNet train.py command, which also performs periodic random-block and whole-scene evaluation.")
    train.add_argument("--repo-root", default=".", help="PointNet2 checkout root. Default: current directory.")
    train.add_argument("--python", default="python2", help="Python executable for legacy raw trainer. Default: python2.")
    train.add_argument("--pythonpath", default=None, help="PYTHONPATH to use from scannet/. Default includes ../models, ../utils, and repo root.")
    train.add_argument("--visible-gpus", default="0", help="CUDA_VISIBLE_DEVICES value. Use empty string to omit. Default: 0.")
    train.add_argument("--gpu", default="0", help="TensorFlow /gpu:<id> flag passed to train.py. Default: 0.")
    train.add_argument("--model", default="pointnet2_sem_seg", help="Model module name. Default: pointnet2_sem_seg.")
    train.add_argument("--log-dir", default="log_scannet", help="Legacy trainer log/checkpoint directory. Default: log_scannet.")
    train.add_argument("--num-point", default="8192", help="Points per block/tile. Default: 8192.")
    train.add_argument("--max-epoch", default="201", help="Epochs. Default: 201.")
    train.add_argument("--batch-size", default="32", help="Blocks/tiles per model call. Default: 32.")
    train.add_argument("--learning-rate", default="0.001", help="Initial learning rate. Default: 0.001.")
    train.add_argument("--momentum", default="0.9", help="Momentum optimizer value. Default: 0.9.")
    train.add_argument("--optimizer", choices=["adam", "momentum"], default="adam", help="Optimizer. Default: adam.")
    train.add_argument("--decay-step", default="200000", help="Learning-rate decay step. Default: 200000.")
    train.add_argument("--decay-rate", default="0.7", help="Learning-rate decay rate. Default: 0.7.")
    train.set_defaults(func=emit_train)

    prep = sub.add_parser("preprocess", help="Emit reference-only raw preprocessing, label-fetch, or demo commands.")
    prep.add_argument("--repo-root", default=".", help="PointNet2 checkout root. Default: current directory.")
    prep.add_argument("--python", default="python2", help="Python executable for legacy preprocessing scripts. Default: python2.")
    prep.add_argument("--step", choices=["fetch-labels", "collect", "demo", "all"], default="collect", help="Preprocessing step to emit. Default: collect.")
    prep.set_defaults(func=emit_preprocess)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
