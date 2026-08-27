#!/usr/bin/env python3
"""Build a safe, shell-quoted aizynthcli command without running it."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell-quoted aizynthcli command. The helper validates "
            "known unsafe combinations but does not run AiZynthFinder."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Configuration YAML file to pass to aizynthcli --config.",
    )
    parser.add_argument(
        "--smiles",
        required=True,
        help="Literal target SMILES or path to a file with one SMILES per line.",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path. Defaults are chosen by aizynthcli when omitted.",
    )
    parser.add_argument(
        "--policy",
        nargs="+",
        default=[],
        metavar="KEY",
        help="Expansion policy key(s) to pass after --policy.",
    )
    parser.add_argument(
        "--filter",
        nargs="+",
        default=[],
        metavar="KEY",
        help="Filter policy key(s) to pass after --filter.",
    )
    parser.add_argument(
        "--stocks",
        nargs="+",
        default=[],
        metavar="KEY",
        help="Stock key(s) to pass after --stocks.",
    )
    parser.add_argument(
        "--nproc",
        type=_positive_int,
        help="Number of worker processes. Requires --smiles to be an existing file.",
    )
    parser.add_argument(
        "--cluster",
        action="store_true",
        help="Include --cluster for automatic route clustering.",
    )
    parser.add_argument(
        "--checkpoint",
        help="Checkpoint file for single-process batch resume.",
    )
    parser.add_argument(
        "--pre_processing",
        help="Pre-processing module name to pass through to aizynthcli.",
    )
    parser.add_argument(
        "--post_processing",
        nargs="+",
        default=[],
        metavar="MODULE",
        help="Post-processing module name(s) to pass through to aizynthcli.",
    )
    parser.add_argument(
        "--log_to_file",
        action="store_true",
        help="Include --log_to_file for detailed file logging.",
    )
    parser.add_argument(
        "--executable",
        default="aizynthcli",
        help="Executable name or path to use as argv[0]. Defaults to aizynthcli.",
    )
    parser.add_argument(
        "--strict-config-exists",
        action="store_true",
        help="Fail if --config does not exist on this machine.",
    )
    return parser


def _extend_multi(command: list[str], flag: str, values: list[str]) -> None:
    if values:
        command.append(flag)
        command.extend(values)


def build_command(args: argparse.Namespace) -> list[str]:
    smiles_is_file = Path(args.smiles).is_file()

    if args.strict_config_exists and not Path(args.config).is_file():
        raise ValueError(f"--config does not exist: {args.config}")

    if args.nproc and not smiles_is_file:
        raise ValueError(
            "--nproc requires --smiles to be an existing file; remove --nproc "
            "for a literal single SMILES or put targets in a file"
        )

    command = [args.executable, "--config", args.config, "--smiles", args.smiles]
    _extend_multi(command, "--policy", args.policy)
    _extend_multi(command, "--filter", args.filter)
    _extend_multi(command, "--stocks", args.stocks)

    if args.output:
        command.extend(["--output", args.output])
    if args.log_to_file:
        command.append("--log_to_file")
    if args.nproc:
        command.extend(["--nproc", str(args.nproc)])
    if args.cluster:
        command.append("--cluster")
    if args.post_processing:
        command.append("--post_processing")
        command.extend(args.post_processing)
    if args.pre_processing:
        command.extend(["--pre_processing", args.pre_processing])
    if args.checkpoint:
        command.extend(["--checkpoint", args.checkpoint])

    return command


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        command = build_command(args)
    except ValueError as exc:
        parser.error(str(exc))

    print(shlex.join(command))
    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main())
