#!/usr/bin/env python
"""Build safer ShapeNetPart part-segmentation commands for pointnet2.

This script does not import the pointnet2 repository. It distills the command
surface from part_seg/command.sh, command_one_hot.sh, train*.py, evaluate.py,
and test.py into explicit arguments.
"""
from __future__ import print_function

import argparse
import os
import shlex
import sys


def q(value):
    text = str(value)
    if hasattr(shlex, "quote"):
        return shlex.quote(text)
    # Python 2 fallback equivalent to pipes.quote without importing the removed module.
    safe = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@%+=:,./-"
    if text and all(ch in safe for ch in text):
        return text
    return "'" + text.replace("'", "'\\''") + "'"


WORKFLOW_DEFAULTS = {
    "train": {
        "script": "train.py",
        "model": "pointnet2_part_seg",
        "gpu": "1",  # preserves part_seg/command.sh; override to 0 on single-GPU hosts
        "log_dir": "log",
        "batch_size": 32,
        "max_epoch": 201,
        "redirect_log": "log.txt",
    },
    "train-one-hot": {
        "script": "train_one_hot.py",
        "model": "pointnet2_part_seg_msg_one_hot",
        "gpu": "0",
        "log_dir": "log_msg_one_hot",
        "batch_size": 8,
        "max_epoch": 201,
        "redirect_log": "log_msg_one_hot.txt",
    },
    "evaluate": {
        "script": "evaluate.py",
        "model": "pointnet2_part_seg",
        "gpu": "0",
        "log_dir": "log_eval",
        "batch_size": 32,
        "model_path": "log/model.ckpt",
    },
    "test": {
        "script": "test.py",
        "model": "pointnet2_part_seg",
        "gpu": "0",
        "model_path": "log/model.ckpt",
        "category": "Airplane",
    },
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Build pointnet2 ShapeNetPart train/evaluate/test commands without importing TensorFlow."
    )
    parser.add_argument(
        "workflow",
        choices=sorted(WORKFLOW_DEFAULTS),
        help="Workflow to command: plain train, one-hot train, plain evaluate, or legacy test visualization.",
    )
    parser.add_argument("--python", default="python", help="Python executable to place in the command.")
    parser.add_argument(
        "--part-seg-dir",
        default="part_seg",
        help="Repository-relative part_seg directory. Commands cd here by default.",
    )
    parser.add_argument(
        "--no-cd",
        action="store_true",
        help="Do not prefix the command with 'cd <part-seg-dir> &&'. Use only if already inside part_seg.",
    )
    parser.add_argument("--gpu", default=None, help="GPU index for the source --gpu flag.")
    parser.add_argument("--model", default=None, help="Model module name. Defaults are workflow-specific.")
    parser.add_argument("--log_dir", default=None, help="Log/checkpoint directory for train/evaluate workflows.")
    parser.add_argument("--num_point", type=int, default=2048, help="Point count for source --num_point.")
    parser.add_argument("--batch_size", type=int, default=None, help="Batch size for train/evaluate workflows.")
    parser.add_argument("--max_epoch", type=int, default=None, help="Max epochs for train workflows.")
    parser.add_argument("--learning_rate", type=float, default=None, help="Training learning rate; omit to use source default.")
    parser.add_argument("--momentum", type=float, default=None, help="Training momentum; omit to use source default.")
    parser.add_argument("--optimizer", choices=["adam", "momentum"], default=None, help="Training optimizer.")
    parser.add_argument("--decay_step", type=int, default=None, help="Training decay step; omit to use source default.")
    parser.add_argument("--decay_rate", type=float, default=None, help="Training decay rate; omit to use source default.")
    parser.add_argument("--model_path", default=None, help="Checkpoint path for evaluate/test workflows.")
    parser.add_argument("--category", default=None, help="Single category for the legacy test visualization workflow.")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Append shell redirection and '&' like the original command.sh snippets.",
    )
    parser.add_argument(
        "--redirect-log",
        default=None,
        help="Log file used when --background is set. Defaults to source command log names for train workflows.",
    )
    parser.add_argument(
        "--allow-custom-model",
        action="store_true",
        help="Allow model names that do not match the workflow's known source model.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Print workflow notes to stderr in addition to the command on stdout.",
    )
    return parser


def add_flag(parts, flag, value):
    if value is not None:
        parts.extend([flag, str(value)])


def workflow_notes(workflow):
    if workflow == "train":
        return [
            "Plain all-category training uses PartNormalDataset without cls_labels_pl.",
            "Run from part_seg so the source script copies the correct train.py into --log_dir.",
        ]
    if workflow == "train-one-hot":
        return [
            "One-hot training must use train_one_hot.py and pointnet2_part_seg_msg_one_hot.",
            "Category labels are loader-derived from synsetoffset2category.txt; keep that mapping stable.",
            "The repository has no standalone one-hot evaluate.py; patch evaluation if needed.",
        ]
    if workflow == "evaluate":
        return [
            "evaluate.py is for the plain pointnet2_part_seg interface and uses 12-vote accumulation.",
            "Do not evaluate pointnet2_part_seg_msg_one_hot with this script unless you patch cls_labels_pl feeding.",
        ]
    return [
        "test.py is a legacy visualization reference with a known ROOT_DIR bug and stale layout/model assumptions.",
        "Patch ROOT_DIR, sys.path, dataset layout, and 50-logit category masking before relying on it.",
    ]


def validate_args(parser, args, model, defaults):
    if args.num_point <= 0:
        parser.error("--num_point must be positive")
    if args.batch_size is not None and args.batch_size <= 0:
        parser.error("--batch_size must be positive")
    if args.max_epoch is not None and args.max_epoch <= 0:
        parser.error("--max_epoch must be positive")

    expected = defaults.get("model")
    if model != expected and not args.allow_custom_model:
        parser.error(
            "workflow %s expects --model %s; pass --allow-custom-model only for a patched/custom source tree"
            % (args.workflow, expected)
        )

    if args.workflow == "evaluate" and "one_hot" in model:
        parser.error(
            "evaluate.py does not support the one-hot model signature; patch evaluator or use train_one_hot.py's built-in eval"
        )

    if args.workflow == "test" and args.background:
        parser.error("Do not background legacy visualization test.py; it is interactive and should be patched first")


def build_command(args):
    defaults = WORKFLOW_DEFAULTS[args.workflow]
    model = args.model or defaults["model"]
    validate_args(build_parser(), args, model, defaults)

    gpu = args.gpu if args.gpu is not None else defaults.get("gpu")
    log_dir = args.log_dir if args.log_dir is not None else defaults.get("log_dir")
    batch_size = args.batch_size if args.batch_size is not None else defaults.get("batch_size")
    max_epoch = args.max_epoch if args.max_epoch is not None else defaults.get("max_epoch")
    model_path = args.model_path if args.model_path is not None else defaults.get("model_path")
    category = args.category if args.category is not None else defaults.get("category")

    parts = [args.python, defaults["script"]]
    add_flag(parts, "--model", model)
    add_flag(parts, "--gpu", gpu)
    add_flag(parts, "--num_point", args.num_point)

    if args.workflow in ("train", "train-one-hot"):
        add_flag(parts, "--log_dir", log_dir)
        add_flag(parts, "--batch_size", batch_size)
        add_flag(parts, "--max_epoch", max_epoch)
        add_flag(parts, "--learning_rate", args.learning_rate)
        add_flag(parts, "--momentum", args.momentum)
        add_flag(parts, "--optimizer", args.optimizer)
        add_flag(parts, "--decay_step", args.decay_step)
        add_flag(parts, "--decay_rate", args.decay_rate)
    elif args.workflow == "evaluate":
        add_flag(parts, "--model_path", model_path)
        add_flag(parts, "--log_dir", log_dir)
        add_flag(parts, "--batch_size", batch_size)
    elif args.workflow == "test":
        add_flag(parts, "--model_path", model_path)
        add_flag(parts, "--category", category)

    command = " ".join(q(p) for p in parts)
    if not args.no_cd:
        command = "cd %s && %s" % (q(args.part_seg_dir), command)

    if args.background:
        redirect_log = args.redirect_log or defaults.get("redirect_log") or "part_seg_%s.log" % args.workflow
        command = "%s > %s 2>&1 &" % (command, q(redirect_log))

    return command


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    command = build_command(args)
    if args.explain:
        for note in workflow_notes(args.workflow):
            print("note: " + note, file=sys.stderr)
    print(command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
