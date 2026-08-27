#!/usr/bin/env python3
"""Forward the standard I2VGen-XL local inference launch to a VGen checkout.

This wrapper is designed to run from the generated skill tree or any other
working directory as long as --repo-root points at a checkout that contains the
VGen runtime files.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def parse_args(argv: List[str]) -> tuple[argparse.Namespace, List[str]]:
    parser = argparse.ArgumentParser(
        description="Forward an I2VGen-XL inference launch to the repo dispatcher.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path('.'),
        help="VGen checkout root that contains inference.py.",
    )
    parser.add_argument(
        "--cfg",
        default="configs/i2vgen_xl_infer.yaml",
        help="Config file to forward to the repo dispatcher.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the dispatcher command without running GPU inference.",
    )
    args, remainder = parser.parse_known_args(argv)
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    return args, remainder


def main(argv: List[str]) -> int:
    args, remainder = parse_args(argv)
    repo_root = args.repo_root.resolve()
    inference_entry = repo_root / "inference.py"
    if not inference_entry.exists():
        print(
            f"ERROR: {inference_entry} was not found. Point --repo-root at a VGen checkout.",
            file=sys.stderr,
        )
        return 1

    command = [sys.executable, str(inference_entry), "--cfg", args.cfg, *remainder]
    if args.dry_run:
        print("Would run:", " ".join(command))
        return 0
    print("Running:", " ".join(command))
    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
