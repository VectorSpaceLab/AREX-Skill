#!/usr/bin/env python3
"""Validate a local AF3 command specification and print it without running it.

This helper deliberately has no dependency on alphafold3_pytorch. It performs
cheap argument/path validation, then emits one shell-quoted command. It never
loads a checkpoint, creates an output/cache directory, imports torch, runs
inference, or launches Gradio.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


PROTEIN_ALPHABET = frozenset("ARDCQEGHILKMNFPSTWYV")
DNA_ALPHABET = frozenset("ACGT")
RNA_ALPHABET = frozenset("ACGU")


def _existing_file(value: str) -> Path:
    """Return an existing regular file or raise an argparse-friendly error."""
    try:
        path = Path(value).expanduser()
        is_file = path.is_file()
    except (OSError, RuntimeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"cannot inspect checkpoint {value!r}: {exc}") from exc
    if not is_file:
        raise argparse.ArgumentTypeError(
            f"checkpoint must be an existing regular file: {value}"
        )
    return path


def _nonempty(value: str) -> str:
    if not value or not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def _sequence(value: str, *, kind: str, minimum_length: int = 1) -> str:
    sequence = value.strip().upper()
    if len(sequence) < minimum_length:
        raise argparse.ArgumentTypeError(
            f"{kind} sequence must contain at least {minimum_length} characters"
        )
    alphabets = {
        "protein": PROTEIN_ALPHABET,
        "rna": RNA_ALPHABET,
        "dna": DNA_ALPHABET,
    }
    allowed = alphabets[kind]
    invalid = sorted(set(sequence) - allowed)
    if invalid:
        shown = ", ".join(repr(char) for char in invalid)
        raise argparse.ArgumentTypeError(
            f"{kind} sequence contains unsupported character(s): {shown}"
        )
    return sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and print an alphafold3_pytorch or "
            "alphafold3_pytorch_app command; never execute it."
        )
    )
    parser.add_argument(
        "--entrypoint",
        choices=("cli", "app"),
        default="cli",
        help="command to construct (default: cli)",
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        type=_existing_file,
        help="existing regular checkpoint file",
    )
    parser.add_argument(
        "--protein",
        action="append",
        default=[],
        metavar="SEQUENCE",
        help="protein sequence; repeat once per protein",
    )
    parser.add_argument(
        "--rna",
        action="append",
        default=[],
        metavar="SEQUENCE",
        help="single-stranded RNA sequence; repeat once per RNA",
    )
    parser.add_argument(
        "--dna",
        action="append",
        default=[],
        metavar="SEQUENCE",
        help="single-stranded DNA sequence; repeat once per DNA",
    )
    parser.add_argument(
        "--num-sample-steps",
        type=_positive_int,
        metavar="INTEGER",
        help="positive diffusion sampling-step count",
    )
    parser.add_argument(
        "--use-cuda",
        choices=("true", "false"),
        metavar="true|false",
        help="explicit Click boolean value for the plain CLI",
    )
    parser.add_argument(
        "--output",
        type=_nonempty,
        default="output.cif",
        help="plain CLI output mmCIF path (default: output.cif)",
    )
    parser.add_argument(
        "--cache-dir",
        type=_nonempty,
        default="cache",
        help="app cache root (default: cache)",
    )
    parser.add_argument(
        "--precision",
        type=_nonempty,
        default="float32",
        help="app precision label; current app does not apply it",
    )
    return parser


def _validate_output(path_text: str) -> str:
    try:
        path = Path(path_text).expanduser()
        if path.exists() and path.is_dir():
            raise ValueError(f"output must be a file path, not a directory: {path_text}")
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"cannot inspect output path {path_text!r}: {exc}") from exc
    return path_text


def _validate_cache(path_text: str) -> str:
    try:
        path = Path(path_text).expanduser()
        resolved = path.resolve(strict=False)
        if path.name in {"", ".", ".."} or resolved == Path.cwd():
            raise ValueError(
                "cache directory must be a dedicated child path, not the current directory or root"
            )
        if path.exists() and not path.is_dir():
            raise ValueError(f"cache path is not a directory: {path_text}")
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"invalid cache directory {path_text!r}: {exc}") from exc
    return path_text


def _validate_polymer_sequences(args: argparse.Namespace) -> None:
    # The real CLI forwards these strings to Alphafold3Input. The builder uses
    # the package UI's conservative alphabets for planning, but does not add
    # the UI's four-character minimum to the non-interactive CLI.
    args.protein = [_sequence(value, kind="protein") for value in args.protein]
    args.rna = [_sequence(value, kind="rna") for value in args.rna]
    args.dna = [_sequence(value, kind="dna") for value in args.dna]


def _command(args: argparse.Namespace) -> list[str]:
    if args.entrypoint == "app":
        if args.protein or args.rna or args.dna:
            raise ValueError("polymer entity options are only valid with --entrypoint cli")
        return [
            "alphafold3_pytorch_app",
            "--checkpoint",
            str(args.checkpoint),
            "--cache-dir",
            args.cache_dir,
            "--precision",
            args.precision,
        ]

    if not (args.protein or args.rna or args.dna):
        raise ValueError("plain CLI requires at least one --protein, --rna, or --dna")

    command = ["alphafold3_pytorch", "--checkpoint", str(args.checkpoint)]
    for option, values in (
        ("--protein", args.protein),
        ("--rna", args.rna),
        ("--dna", args.dna),
    ):
        for value in values:
            command.extend((option, value))
    if args.num_sample_steps is not None:
        command.extend(("--num-sample-steps", str(args.num_sample_steps)))
    if args.use_cuda is not None:
        command.extend(("--use-cuda", args.use_cuda))
    command.extend(("--output", _validate_output(args.output)))
    return command


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        _validate_polymer_sequences(args)
        args.cache_dir = _validate_cache(args.cache_dir)
        command = _command(args)
    except ValueError as exc:
        parser.error(str(exc))
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
