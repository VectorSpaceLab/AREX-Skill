#!/usr/bin/env python3
"""Build a shell-safe EdgeConnect test.py command without executing it."""

import argparse
import shlex
import sys


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Construct a safe python test.py command from checkpoint, stage, "
            "input, mask, edge, and output options. The command is printed only; "
            "it is never executed."
        )
    )
    parser.add_argument("--model", type=int, choices=[1, 2, 3, 4], default=3, help="test stage model id (default: 3)")
    parser.add_argument("--checkpoints", "--path", dest="checkpoints", required=True, help="checkpoint directory passed to test.py")
    parser.add_argument("--input", help="input image file, directory, or flist passed to test.py")
    parser.add_argument("--mask", help="mask file, directory, or flist passed to test.py")
    parser.add_argument("--edge", help="edge file, directory, or flist passed to test.py")
    parser.add_argument("--output", help="output directory passed to test.py")
    parser.add_argument("--python", default="python", help="python executable to place at the start of the command (default: python)")
    return parser.parse_args(argv)


def build_command(args):
    parts = [args.python, "test.py", "--model", str(args.model), "--checkpoints", args.checkpoints]
    if args.input:
        parts.extend(["--input", args.input])
    if args.mask:
        parts.extend(["--mask", args.mask])
    if args.edge:
        parts.extend(["--edge", args.edge])
    if args.output:
        parts.extend(["--output", args.output])
    return " ".join(shlex.quote(part) for part in parts)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    print(build_command(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
