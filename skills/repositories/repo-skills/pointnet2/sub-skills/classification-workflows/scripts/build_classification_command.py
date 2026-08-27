#!/usr/bin/env python
"""Build safe PointNet2 ModelNet40 classification commands.

This helper does not import the source repository. It only mirrors the CLI
surfaces of train.py, train_multi_gpu.py, and evaluate.py, validates common
flag mistakes, and prints the command to run from a compatible PointNet2
checkout.
"""
from __future__ import print_function

import argparse
import json
import sys

try:
    from shlex import quote as shell_quote
except ImportError:  # Python 2.7
    from pipes import quote as shell_quote


POINT_LIMITS = {
    "h5": 2048,
    "normal": 10000,
}

POINTNET2_MODELS = set(["pointnet2_cls_ssg", "pointnet2_cls_msg"])
MODEL_CHOICES = ["pointnet2_cls_ssg", "pointnet2_cls_msg", "pointnet_cls_basic"]


def build_parser():
    parser = argparse.ArgumentParser(
        description="Build a source-compatible PointNet2 classification command without running legacy TensorFlow code."
    )
    parser.add_argument("--action", choices=["train", "train-multi-gpu", "evaluate"], required=True,
                        help="Which classification workflow command to build.")
    parser.add_argument("--dataset-mode", choices=["h5", "normal"], default="h5",
                        help="HDF5 XYZ mode omits --normal; normal mode adds --normal and uses normal-resampled text data.")
    parser.add_argument("--model", choices=MODEL_CHOICES, default="pointnet2_cls_ssg",
                        help="Model module name to pass to the legacy script.")
    parser.add_argument("--python", default="python", help="Python executable token to put at the start of the generated command.")
    parser.add_argument("--cuda-visible-devices", default=None,
                        help="Optional CUDA_VISIBLE_DEVICES value to prefix before the command, e.g. 0,1.")

    parser.add_argument("--gpu", type=int, default=0, help="GPU id for train/evaluate scripts [default: 0].")
    parser.add_argument("--num-gpus", type=int, default=1, help="Number of visible GPUs for train-multi-gpu [default: 1].")
    parser.add_argument("--log-dir", default="log", help="Training log/checkpoint directory [default: log].")
    parser.add_argument("--dump-dir", default="dump", help="Evaluation output directory [default: dump].")
    parser.add_argument("--model-path", default="log/model.ckpt", help="Checkpoint prefix for evaluate.py [default: log/model.ckpt].")

    parser.add_argument("--num-point", type=int, default=1024, help="Number of points per shape [default: 1024].")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="Global batch size. Defaults: train/evaluate=16, train-multi-gpu=32.")
    parser.add_argument("--max-epoch", type=int, default=251, help="Training epochs [default: 251].")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Initial learning rate [default: 0.001].")
    parser.add_argument("--momentum", type=float, default=0.9, help="Momentum optimizer momentum [default: 0.9].")
    parser.add_argument("--optimizer", choices=["adam", "momentum"], default="adam", help="Optimizer [default: adam].")
    parser.add_argument("--decay-step", type=int, default=200000, help="Learning-rate decay step [default: 200000].")
    parser.add_argument("--decay-rate", type=float, default=0.7, help="Learning-rate decay rate [default: 0.7].")
    parser.add_argument("--num-votes", type=int, default=1, help="Evaluation voting rotations [default: 1].")

    parser.add_argument("--json", action="store_true", help="Emit JSON with command, notes, and derived constraints.")
    return parser


def add_flag(tokens, name, value):
    tokens.extend(["--" + name, str(value)])


def validate_args(parser, args):
    if args.num_point <= 0:
        parser.error("--num-point must be positive")
    max_points = POINT_LIMITS[args.dataset_mode]
    if args.num_point > max_points:
        parser.error("--num-point %d exceeds %s mode limit %d" % (args.num_point, args.dataset_mode, max_points))

    if args.batch_size is None:
        args.batch_size = 32 if args.action == "train-multi-gpu" else 16
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")

    if args.action == "train-multi-gpu":
        if args.num_gpus <= 0:
            parser.error("--num-gpus must be positive")
        if args.batch_size % args.num_gpus != 0:
            parser.error("--batch-size must be divisible by --num-gpus for train_multi_gpu.py")
    if args.action != "train-multi-gpu" and args.num_gpus != 1:
        parser.error("--num-gpus only applies to --action train-multi-gpu")

    if args.action != "evaluate" and args.num_votes != 1:
        parser.error("--num-votes only applies to --action evaluate")
    if args.action == "evaluate" and args.num_votes < 1:
        parser.error("--num-votes must be >= 1")

    if args.max_epoch <= 0:
        parser.error("--max-epoch must be positive")
    if args.decay_step <= 0:
        parser.error("--decay-step must be positive")


def collect_notes(args):
    notes = []
    if args.model in POINTNET2_MODELS:
        notes.append("PointNet++ model %s requires the shared TensorFlow custom-op backend." % args.model)
    else:
        notes.append("pointnet_cls_basic is the custom-op-free PointNet v1 baseline and is best for CPU smoke/baseline work.")
    if args.dataset_mode == "normal":
        notes.append("normal mode adds --normal and allows <=10000 points, but the stock classification model files observed here declare BxNx3 placeholders while the normal loader returns 6 channels; adapt the model for true XYZ+normal runs.")
    else:
        notes.append("HDF5 mode omits --normal, uses XYZ data, and is limited to <=2048 points.")
    if args.action == "evaluate" and args.num_votes > 1:
        notes.append("evaluation cost scales roughly linearly with --num_votes because every batch is rotated/evaluated once per vote.")
    if args.action == "train-multi-gpu":
        notes.append("train_multi_gpu.py splits the global batch evenly: per-device batch size is %d." % (args.batch_size // args.num_gpus))
    return notes


def command_tokens(args):
    if args.action == "train":
        tokens = [args.python, "train.py"]
        add_flag(tokens, "gpu", args.gpu)
        add_flag(tokens, "model", args.model)
        add_flag(tokens, "log_dir", args.log_dir)
        add_flag(tokens, "num_point", args.num_point)
        add_flag(tokens, "max_epoch", args.max_epoch)
        add_flag(tokens, "batch_size", args.batch_size)
        add_flag(tokens, "learning_rate", args.learning_rate)
        add_flag(tokens, "momentum", args.momentum)
        add_flag(tokens, "optimizer", args.optimizer)
        add_flag(tokens, "decay_step", args.decay_step)
        add_flag(tokens, "decay_rate", args.decay_rate)
    elif args.action == "train-multi-gpu":
        tokens = [args.python, "train_multi_gpu.py"]
        add_flag(tokens, "num_gpus", args.num_gpus)
        add_flag(tokens, "model", args.model)
        add_flag(tokens, "log_dir", args.log_dir)
        add_flag(tokens, "num_point", args.num_point)
        add_flag(tokens, "max_epoch", args.max_epoch)
        add_flag(tokens, "batch_size", args.batch_size)
        add_flag(tokens, "learning_rate", args.learning_rate)
        add_flag(tokens, "momentum", args.momentum)
        add_flag(tokens, "optimizer", args.optimizer)
        add_flag(tokens, "decay_step", args.decay_step)
        add_flag(tokens, "decay_rate", args.decay_rate)
    else:
        tokens = [args.python, "evaluate.py"]
        add_flag(tokens, "gpu", args.gpu)
        add_flag(tokens, "model", args.model)
        add_flag(tokens, "batch_size", args.batch_size)
        add_flag(tokens, "num_point", args.num_point)
        add_flag(tokens, "model_path", args.model_path)
        add_flag(tokens, "dump_dir", args.dump_dir)
        add_flag(tokens, "num_votes", args.num_votes)

    if args.dataset_mode == "normal":
        tokens.append("--normal")
    return tokens


def shell_command(args):
    cmd = " ".join(shell_quote(token) for token in command_tokens(args))
    if args.cuda_visible_devices is not None:
        cmd = "CUDA_VISIBLE_DEVICES=%s %s" % (shell_quote(args.cuda_visible_devices), cmd)
    return cmd


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)
    notes = collect_notes(args)
    command = shell_command(args)
    payload = {
        "command": command,
        "action": args.action,
        "datasetMode": args.dataset_mode,
        "model": args.model,
        "numPoint": args.num_point,
        "batchSize": args.batch_size,
        "requiresPointNetCustomOps": args.model in POINTNET2_MODELS,
        "notes": notes,
    }
    if args.action == "train-multi-gpu":
        payload["numGpus"] = args.num_gpus
        payload["perDeviceBatchSize"] = args.batch_size // args.num_gpus
    if args.action == "evaluate":
        payload["modelPath"] = args.model_path
        payload["numVotes"] = args.num_votes

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(command)
        for note in notes:
            print("NOTE: " + note, file=sys.stderr)


if __name__ == "__main__":
    main()
