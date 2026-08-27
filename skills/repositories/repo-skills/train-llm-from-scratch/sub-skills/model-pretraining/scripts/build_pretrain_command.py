#!/usr/bin/env python3
"""Print a safe modern or legacy pretraining command without executing it.

The emitted command is repo-relative and intended to be reviewed or copied by a
human/agent after data paths, device, and budget are confirmed. This helper never
imports torch and never starts training.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable


def _split_extra(values: Iterable[str]) -> list[str]:
    """Split repeated --extra fragments into command tokens."""
    tokens: list[str] = []
    for value in values:
        value = value.strip()
        if not value:
            continue
        tokens.extend(shlex.split(value))
    return tokens


def _shell_join(tokens: list[str]) -> str:
    """Return a shell-escaped command line."""
    return shlex.join(tokens)


def build_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    """Build command tokens and warning strings from parsed arguments."""
    warnings: list[str] = []
    if args.nproc < 1:
        raise ValueError("--nproc must be >= 1")

    command: list[str] = ["PYTHONPATH=."]

    if args.mode == "modern":
        config = args.config or ("configs/smoke/pretrain.json" if args.smoke else "configs/pretrain.json")
        if args.nproc > 1:
            command.extend([
                args.torchrun,
                "--standalone",
                f"--nproc_per_node={args.nproc}",
                "scripts/pretrain_base.py",
                "--config",
                config,
            ])
        else:
            command.extend([args.python, "scripts/pretrain_base.py", "--config", config])
    else:
        if args.nproc != 1:
            warnings.append("legacy mode is single-process; ignoring --nproc > 1")
        if args.config:
            warnings.append("legacy mode reads config/config.py; --config is accepted by this builder but not emitted")
        if args.smoke:
            warnings.append("legacy mode has no JSON smoke config; use smoke_transformer.py or edit the legacy config to tiny dimensions/data")
        command.extend([args.python, "scripts/train_transformer.py"])

    command.extend(_split_extra(args.extra or []))
    return command, warnings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print one dry-run pretraining command for the modern or legacy trainer."
    )
    parser.add_argument("--mode", choices=["modern", "legacy"], default="modern", help="Trainer family to target.")
    parser.add_argument("--config", help="Stage JSON config for modern mode. Legacy mode accepts but does not emit it.")
    parser.add_argument("--nproc", type=int, default=1, help="Number of torchrun processes for modern DDP commands.")
    parser.add_argument("--smoke", action="store_true", help="Use the modern smoke pretrain config when --config is not supplied.")
    parser.add_argument("--python", default="python", help="Python executable token to place in emitted single-process commands.")
    parser.add_argument("--torchrun", default="torchrun", help="torchrun executable token for modern multi-process commands.")
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        help=(
            "Additional flag fragment appended to the emitted command. Repeat as needed. "
            "Use --extra=--print-config or --extra='--batch_size 8'."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        command, warnings = build_command(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(_shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
