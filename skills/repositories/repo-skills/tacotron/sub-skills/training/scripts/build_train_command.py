#!/usr/bin/env python3
"""Build a Tacotron training command without starting TensorFlow training."""
import argparse
import os
import shlex
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout-root", default=".",
                        help="Tacotron checkout whose cwd will run train.py")
    parser.add_argument("--base-dir", default="~/tacotron")
    parser.add_argument("--input", default="training/train.txt")
    parser.add_argument("--model", default="tacotron")
    parser.add_argument("--name")
    parser.add_argument("--hparams", default="")
    parser.add_argument("--restore-step", type=int)
    parser.add_argument("--summary-interval", type=int, default=100)
    parser.add_argument("--checkpoint-interval", type=int, default=1000)
    parser.add_argument("--tf-log-level", type=int, default=1)
    parser.add_argument("--git", action="store_true")
    args = parser.parse_args()
    if args.restore_step is not None and args.restore_step < 0:
        parser.error("--restore-step must be non-negative")
    if args.summary_interval <= 0 or args.checkpoint_interval <= 0:
        parser.error("intervals must be positive")
    if args.hparams:
        for item in args.hparams.split(","):
            if "=" not in item or not item.split("=", 1)[0].strip():
                parser.error("hparams must use comma-separated name=value pairs")
    command = ["python", "train.py", "--base_dir", os.path.abspath(os.path.expanduser(args.base_dir)),
               "--input", args.input, "--model", args.model,
               "--summary_interval", str(args.summary_interval),
               "--checkpoint_interval", str(args.checkpoint_interval),
               "--tf_log_level", str(args.tf_log_level)]
    if args.name:
        command += ["--name", args.name]
    if args.hparams:
        command += ["--hparams", args.hparams]
    if args.restore_step is not None:
        command += ["--restore_step", str(args.restore_step)]
    if args.git:
        command.append("--git")
    rendered = " ".join(shlex.quote(x) for x in command)
    print("cd %s && %s" % (shlex.quote(os.path.abspath(os.path.expanduser(args.checkout_root))), rendered))
    print("dry-run: no training started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
