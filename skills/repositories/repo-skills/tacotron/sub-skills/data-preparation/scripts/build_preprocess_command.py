#!/usr/bin/env python3
"""Build a Tacotron preprocessing command without reading or writing a dataset."""
import argparse
import os
import shlex
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout-root", default=".",
                        help="Tacotron checkout whose cwd will run preprocess.py")
    parser.add_argument("--base-dir", default="~/tacotron")
    parser.add_argument("--output", default="training")
    parser.add_argument("--dataset", choices=("ljspeech", "blizzard"), required=True)
    parser.add_argument("--num-workers", type=int)
    args = parser.parse_args()
    if args.num_workers is not None and args.num_workers < 1:
        parser.error("--num-workers must be positive")
    command = ["python", "preprocess.py", "--base_dir", os.path.abspath(os.path.expanduser(args.base_dir)),
               "--output", args.output, "--dataset", args.dataset]
    if args.num_workers is not None:
        command += ["--num_workers", str(args.num_workers)]
    rendered = " ".join(shlex.quote(x) for x in command)
    print("cd %s && %s" % (shlex.quote(os.path.abspath(os.path.expanduser(args.checkout_root))), rendered))
    print("dry-run: no dataset read and no files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
