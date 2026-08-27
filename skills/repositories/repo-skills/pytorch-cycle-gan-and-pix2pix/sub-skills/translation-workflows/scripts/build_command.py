#!/usr/bin/env python3
"""Build safe train/test commands for pytorch-CycleGAN-and-pix2pix workflows.

This helper prints command lines; it never imports repository code, downloads
assets, starts training, or writes checkpoints. Run the printed command from a
checkout of the target repository after validating the dataset layout and
checkpoint paths.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import List, Optional

TRAIN_WORKFLOWS = {"cyclegan-train", "pix2pix-train", "colorization-train"}
TEST_WORKFLOWS = {"cyclegan-test", "cyclegan-single-test", "pix2pix-test", "colorization-test"}
ALL_WORKFLOWS = sorted(TRAIN_WORKFLOWS | TEST_WORKFLOWS)


def q(parts: List[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def append_common(args: argparse.Namespace, cmd: List[str]) -> None:
    if args.checkpoints_dir:
        cmd.extend(["--checkpoints_dir", args.checkpoints_dir])
    if args.direction:
        cmd.extend(["--direction", args.direction])
    if args.netG:
        cmd.extend(["--netG", args.netG])
    if args.norm:
        cmd.extend(["--norm", args.norm])
    if args.preprocess:
        cmd.extend(["--preprocess", args.preprocess])
    if args.load_size is not None:
        cmd.extend(["--load_size", str(args.load_size)])
    if args.crop_size is not None:
        cmd.extend(["--crop_size", str(args.crop_size)])
    if args.extra:
        cmd.extend(args.extra)


def device_prefix(args: argparse.Namespace) -> List[str]:
    if args.cpu:
        return ["CUDA_VISIBLE_DEVICES="]
    if args.gpu_ids:
        return [f"CUDA_VISIBLE_DEVICES={args.gpu_ids}"]
    return []


def build_train(args: argparse.Namespace) -> List[str]:
    if args.workflow == "cyclegan-train":
        model = "cycle_gan"
        default_name = "experiment_cyclegan"
    elif args.workflow == "pix2pix-train":
        model = "pix2pix"
        default_name = "experiment_pix2pix"
    elif args.workflow == "colorization-train":
        model = "colorization"
        default_name = "experiment_colorization"
    else:  # pragma: no cover - guarded by caller
        raise ValueError(args.workflow)

    name = args.name or default_name
    cmd: List[str] = ["train.py", "--dataroot", args.dataroot, "--name", name, "--model", model]
    if args.n_epochs is not None:
        cmd.extend(["--n_epochs", str(args.n_epochs)])
    if args.n_epochs_decay is not None:
        cmd.extend(["--n_epochs_decay", str(args.n_epochs_decay)])
    if args.no_html:
        cmd.append("--no_html")
    if args.use_wandb:
        cmd.append("--use_wandb")
    append_common(args, cmd)

    if args.ddp_procs:
        if args.cpu:
            raise SystemExit("--ddp-procs is for CUDA/multi-process training and cannot be combined with --cpu")
        if args.ddp_procs < 2:
            raise SystemExit("--ddp-procs must be >= 2")
        cmd = device_prefix(args) + ["torchrun", f"--nproc_per_node={args.ddp_procs}"] + cmd
    else:
        cmd = device_prefix(args) + ["python"] + cmd
    return cmd


def build_test(args: argparse.Namespace) -> List[str]:
    if args.workflow == "cyclegan-test":
        model = "cycle_gan"
        default_name = "experiment_cyclegan"
    elif args.workflow == "cyclegan-single-test":
        model = "test"
        default_name = "pretrained_or_trained_cyclegan"
    elif args.workflow == "pix2pix-test":
        model = "pix2pix"
        default_name = "experiment_pix2pix"
    elif args.workflow == "colorization-test":
        model = "colorization"
        default_name = "experiment_colorization"
    else:  # pragma: no cover - guarded by caller
        raise ValueError(args.workflow)

    name = args.name or default_name
    cmd: List[str] = device_prefix(args) + ["python", "test.py", "--dataroot", args.dataroot, "--name", name, "--model", model]
    if args.results_dir:
        cmd.extend(["--results_dir", args.results_dir])
    if args.phase:
        cmd.extend(["--phase", args.phase])
    if args.epoch:
        cmd.extend(["--epoch", args.epoch])
    if args.num_test is not None:
        cmd.extend(["--num_test", str(args.num_test)])
    if args.eval:
        cmd.append("--eval")
    if args.model_suffix is not None and args.workflow == "cyclegan-single-test":
        cmd.extend(["--model_suffix", args.model_suffix])
    elif args.model_suffix is not None:
        raise SystemExit("--model-suffix is only valid for --workflow cyclegan-single-test")
    append_common(args, cmd)
    return cmd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a safe command for a common CycleGAN/pix2pix train or test workflow.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workflow", required=True, choices=ALL_WORKFLOWS)
    parser.add_argument("--dataroot", required=True, help="Dataset/input root interpreted by the chosen workflow.")
    parser.add_argument("--name", help="Experiment/checkpoint name. Defaults to a workflow-specific placeholder.")
    parser.add_argument("--checkpoints-dir", dest="checkpoints_dir", help="Override checkpoint root.")
    parser.add_argument("--results-dir", dest="results_dir", help="Override test results root.")
    parser.add_argument("--direction", choices=("AtoB", "BtoA"), help="A/B mapping direction when relevant.")
    parser.add_argument("--netG", choices=("resnet_9blocks", "resnet_6blocks", "unet_128", "unet_256"), help="Generator architecture override.")
    parser.add_argument("--norm", choices=("instance", "batch", "none", "syncbatch"), help="Normalization override. Keep this stable between train and test checkpoints.")
    parser.add_argument("--preprocess", choices=("resize_and_crop", "crop", "scale_width", "scale_width_and_crop", "none"), help="Image preprocessing override.")
    parser.add_argument("--load-size", dest="load_size", type=int)
    parser.add_argument("--crop-size", dest="crop_size", type=int)
    parser.add_argument("--cpu", action="store_true", help="Prefix the command with CUDA_VISIBLE_DEVICES= so current source auto-selects CPU.")
    parser.add_argument("--cuda-visible-devices", dest="gpu_ids", help="Prefix with CUDA_VISIBLE_DEVICES=<ids>, e.g. 0 or 0,1,2. Ignored when --cpu is set.")
    parser.add_argument("--ddp-procs", type=int, help="For training workflows, emit torchrun with this number of local processes.")
    parser.add_argument("--n-epochs", dest="n_epochs", type=int, help="Training epochs at initial learning rate.")
    parser.add_argument("--n-epochs-decay", dest="n_epochs_decay", type=int, help="Training epochs for linear decay.")
    parser.add_argument("--no-html", action="store_true", help="Append --no_html for training.")
    parser.add_argument("--use-wandb", action="store_true", help="Append --use_wandb for training.")
    parser.add_argument("--phase", help="Test/train phase option, usually test or train.")
    parser.add_argument("--epoch", help="Checkpoint epoch to load during test, often latest.")
    parser.add_argument("--num-test", dest="num_test", type=int, help="Number of images to process during test.")
    parser.add_argument("--eval", action="store_true", help="Append --eval during test.")
    parser.add_argument("--model-suffix", dest="model_suffix", help="Generator suffix for cyclegan-single-test, e.g. _A.")
    parser.add_argument("--extra", nargs=argparse.REMAINDER, help="Extra raw repo flags appended after --. Example: --extra --serial_batches")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.workflow in TRAIN_WORKFLOWS:
        cmd = build_train(args)
        if args.ddp_procs and not args.norm:
            print("warning: DDP usually needs a synchronized or otherwise compatible normalization choice; verify the current checkout's accepted --norm value before running.", file=sys.stderr)
    else:
        if args.ddp_procs:
            parser.error("--ddp-procs is only valid for training workflows")
        if args.no_html or args.use_wandb or args.n_epochs is not None or args.n_epochs_decay is not None:
            parser.error("training-only options cannot be used with test workflows")
        cmd = build_test(args)
    print(q(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
