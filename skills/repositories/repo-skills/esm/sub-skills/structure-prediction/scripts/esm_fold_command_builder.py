#!/usr/bin/env python3
"""Build safe, printable esm-fold commands without running ESMFold inference."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or a positive integer")
    return parsed


def existing_file(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"FASTA file does not exist: {path}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"FASTA path is not a file: {path}")
    return path


def output_directory(value: str) -> Path:
    path = Path(value).expanduser()
    if path.exists() and not path.is_dir():
        raise argparse.ArgumentTypeError(f"PDB output path exists but is not a directory: {path}")
    parent = path.parent if path.parent != Path("") else Path(".")
    if not parent.exists():
        raise argparse.ArgumentTypeError(f"PDB output parent does not exist: {parent}")
    if not parent.is_dir():
        raise argparse.ArgumentTypeError(f"PDB output parent is not a directory: {parent}")
    return path


def optional_directory(value: str) -> Path:
    path = Path(value).expanduser()
    if path.exists() and not path.is_dir():
        raise argparse.ArgumentTypeError(f"model cache path exists but is not a directory: {path}")
    parent = path.parent if path.parent != Path("") else Path(".")
    if not parent.exists():
        raise argparse.ArgumentTypeError(f"model cache parent does not exist: {parent}")
    return path


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate inputs and build an esm-fold command. By default this script "
            "prints the command only; it does not load models, download weights, or run inference."
        )
    )
    parser.add_argument("-i", "--fasta", required=True, type=existing_file, help="input FASTA file")
    parser.add_argument("-o", "--pdb", required=True, type=output_directory, help="output PDB directory")
    parser.add_argument(
        "-m",
        "--model-dir",
        type=optional_directory,
        default=None,
        help="optional torch hub cache/model directory parent for ESM weights",
    )
    parser.add_argument(
        "--num-recycles",
        type=nonnegative_int,
        default=None,
        help="number of ESMFold recycles; omit to use the model default",
    )
    parser.add_argument(
        "--max-tokens-per-batch",
        type=nonnegative_int,
        default=None,
        help="token budget per forward pass; use 0 to disable batching",
    )
    parser.add_argument(
        "--chunk-size",
        type=positive_int,
        default=None,
        help="axial-attention chunk size, commonly 128, 64, or 32",
    )
    parser.add_argument("--cpu-only", action="store_true", help="build a CPU-only esm-fold command")
    parser.add_argument("--cpu-offload", action="store_true", help="build a CUDA command with FSDP CPU offload")
    parser.add_argument(
        "--binary",
        default="esm-fold",
        help="esm-fold executable name or path to place at the start of the command",
    )
    parser.add_argument(
        "--create-output-dir",
        action="store_true",
        help="create the PDB output directory if it does not exist",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="run the generated command after validation; default is print-only",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        default=True,
        help="print the command without running it; this is the default",
    )
    return parser


def build_command(args: argparse.Namespace) -> list[str]:
    command = [args.binary, "-i", str(args.fasta), "-o", str(args.pdb)]
    if args.model_dir is not None:
        command.extend(["--model-dir", str(args.model_dir)])
    if args.num_recycles is not None:
        command.extend(["--num-recycles", str(args.num_recycles)])
    if args.max_tokens_per_batch is not None:
        command.extend(["--max-tokens-per-batch", str(args.max_tokens_per_batch)])
    if args.chunk_size is not None:
        command.extend(["--chunk-size", str(args.chunk_size)])
    if args.cpu_only:
        command.append("--cpu-only")
    if args.cpu_offload:
        command.append("--cpu-offload")
    return command


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.cpu_only and args.cpu_offload:
        parser.error("--cpu-only and --cpu-offload are mutually exclusive")
    if args.create_output_dir:
        args.pdb.mkdir(parents=False, exist_ok=True)
    elif not args.pdb.exists():
        parser.error("PDB output directory does not exist; pass --create-output-dir to create it")
    if args.model_dir is not None and not args.model_dir.exists():
        parser.error("model directory does not exist; create/populate it first or omit --model-dir")


def shell_join(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    command = build_command(args)
    print(shell_join(command))
    if args.run:
        return subprocess.call(command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
