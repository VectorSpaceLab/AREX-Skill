#!/usr/bin/env python3
"""Launch the installed RL_Environment training entry point explicitly.

Default behavior is a dry-run usage message. Pass --run followed by Hydra
KEY=VALUE overrides after `--` to start a long-running Isaac Gym job, for
example: `python scripts/run_training.py --run -- task=Aliengo headless=True`.
The wrapper resolves the installed public package and does not require a
source-checkout path.
"""
from __future__ import print_function

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def find_package_dir():
    spec = importlib.util.find_spec("RL_Environment")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError(
            "RL_Environment is not importable; install the current project package first"
        )
    package_dir = Path(next(iter(spec.submodule_search_locations))).resolve()
    train_file = package_dir / "train.py"
    if not train_file.is_file():
        raise RuntimeError("installed RL_Environment package has no train.py entry point")
    return package_dir, train_file


def build_parser():
    parser = argparse.ArgumentParser(
        description="Plan or explicitly launch the installed RL_Environment Hydra entry point."
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="actually start the long-running training/evaluation process",
    )
    parser.add_argument(
        "--show-entry-point",
        action="store_true",
        help="print the resolved installed entry-point path without launching it",
    )
    parser.add_argument(
        "--run-root",
        help="user-owned Hydra output directory; adds hydra.run.dir when launching",
    )
    parser.add_argument(
        "overrides",
        nargs=argparse.REMAINDER,
        help="Hydra KEY=VALUE overrides; put `--` before the first override",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        package_dir, train_file = find_package_dir()
    except Exception as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 2

    overrides = list(args.overrides)
    if overrides and overrides[0] == "--":
        overrides = overrides[1:]
    if any("=" not in value for value in overrides):
        print("ERROR: every training argument after -- must be a Hydra KEY=VALUE override", file=sys.stderr)
        return 2

    print("Installed training entry point: {}".format(train_file))
    print("Working directory: {}".format(package_dir))
    if args.run_root:
        if any(value.startswith("hydra.run.dir=") for value in overrides):
            print("ERROR: specify the output directory either with --run-root or hydra.run.dir, not both", file=sys.stderr)
            return 2
        overrides.append("hydra.run.dir={}".format(os.path.abspath(os.path.expanduser(args.run_root))))
    if not args.run:
        print("DRY RUN: pass --run -- followed by Hydra overrides to start the process")
        if overrides:
            print("Planned overrides: {}".format(" ".join(overrides)))
        return 0
    if not overrides:
        print("WARNING: no overrides supplied; use at least task=Aliengo and an explicit headless setting")

    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, str(train_file)] + overrides,
        cwd=str(package_dir),
        env=env,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
