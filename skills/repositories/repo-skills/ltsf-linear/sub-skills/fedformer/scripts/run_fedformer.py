#!/usr/bin/env python3
"""Build or run the native FEDformer CLI from an LTSF-Linear checkout.

This helper keeps the execution rooted in the FEDformer subtree so the local
`exp/`, `models/`, `layers/`, and `utils/` imports resolve the same way they do
in the source repository.

Examples:
  python scripts/run_fedformer.py --repo-root <repo-root> --run -- --help
  python scripts/run_fedformer.py --repo-root <repo-root> --run -- \
    --is_training 1 --model FEDformer --version Fourier ...
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print or run the native FEDformer CLI from a checkout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the repository root that contains the FEDformer subtree.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to launch the native CLI.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the native command instead of only printing it.",
    )
    parser.add_argument(
        "fedformer_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to FEDformer/run.py after --.",
    )
    return parser.parse_args()


def resolve_fedformer_root(repo_root: str) -> Path:
    root = Path(repo_root).expanduser().resolve()
    fedformer_root = root / "FEDformer"
    run_py = fedformer_root / "run.py"
    if not run_py.is_file():
        raise SystemExit(
            f"Expected FEDformer entry point at {run_py}. Point --repo-root at a checkout that contains the FEDformer subtree."
        )
    return fedformer_root


def main() -> int:
    args = parse_args()
    fedformer_root = resolve_fedformer_root(args.repo_root)
    passthrough = list(args.fedformer_args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    command = [args.python, "-u", "run.py", *passthrough]
    display_command = ["python", "-u", "run.py", *passthrough]
    print(f"cd {shlex.quote(str(fedformer_root))} && {shlex.join(display_command)}")

    if not args.run:
        return 0

    completed = subprocess.run(command, cwd=fedformer_root)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
