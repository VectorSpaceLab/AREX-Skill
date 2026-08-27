#!/usr/bin/env python3
"""Run a PFLlib dataset generator from a checkout.

This helper keeps the checkout path explicit, switches to `dataset/` before
running the generator, and defaults to a dry run so network downloads stay
intentional.

Examples:
  python run_dataset_generator.py --repo-root /path/to/PFLlib --generator generate_MNIST.py -- noniid - dir
  python run_dataset_generator.py --repo-root /path/to/PFLlib --generator generate_HAR.py --execute
  python run_dataset_generator.py --repo-root /path/to/PFLlib --list
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def available_generators(dataset_dir: Path) -> list[str]:
    return sorted(p.name for p in dataset_dir.glob("generate_*.py"))


def normalize_generator_name(name: str) -> str:
    return name if name.endswith(".py") else f"{name}.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Path to the PFLlib checkout.")
    parser.add_argument("--generator", help="Generator filename or stem, such as generate_MNIST.py or generate_MNIST.")
    parser.add_argument("--execute", action="store_true", help="Actually run the generator instead of printing the command.")
    parser.add_argument("--list", action="store_true", help="List the available dataset generators and exit.")
    args, passthrough = parser.parse_known_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    dataset_dir = repo_root / "dataset"

    if not dataset_dir.is_dir():
        print(f"error: expected a dataset/ directory under {repo_root}", file=sys.stderr)
        return 2

    if args.list:
        for item in available_generators(dataset_dir):
            print(item)
        return 0

    if not args.generator:
        print("error: --generator is required unless --list is set", file=sys.stderr)
        return 2

    generator_name = normalize_generator_name(args.generator)
    generator_path = dataset_dir / generator_name
    if not generator_path.is_file():
        print(f"error: generator not found: {generator_path}", file=sys.stderr)
        return 2

    if passthrough[:1] == ["--"]:
        passthrough = passthrough[1:]

    cmd = [sys.executable, str(generator_path), *passthrough]
    print(f"cwd: {dataset_dir}")
    print("command:", " ".join(cmd))

    if not args.execute:
        print("dry-run only; add --execute to run the generator.")
        return 0

    completed = subprocess.run(cmd, cwd=str(dataset_dir))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
