#!/usr/bin/env python3
"""Build, print, and never execute a BindCraft direct or SLURM command."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Sequence


def safe_text(value: str) -> str:
    """Reject control characters that make a printed shell command ambiguous."""
    if "\x00" in value or "\n" in value or "\r" in value:
        raise argparse.ArgumentTypeError("values must not contain NUL or newlines")
    return value


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Print a shell-safe BindCraft command for direct Python or SLURM "
            "launch. This helper never executes or submits the command."
        )
    )
    ap.add_argument("--mode", choices=("direct", "slurm"), required=True)
    ap.add_argument(
        "--settings",
        type=safe_text,
        required=True,
        help="Required target-settings JSON passed as BindCraft --settings.",
    )
    ap.add_argument(
        "--filters",
        type=safe_text,
        help="Optional filter JSON passed as BindCraft --filters.",
    )
    ap.add_argument(
        "--advanced",
        type=safe_text,
        help="Optional advanced JSON passed as BindCraft --advanced.",
    )
    ap.add_argument(
        "--bindcraft-dir",
        type=safe_text,
        default=".",
        help="BindCraft installation directory (default: current directory).",
    )
    ap.add_argument(
        "--python",
        dest="python_command",
        type=safe_text,
        default="python",
        help="Python command for direct mode (default: python).",
    )
    ap.add_argument(
        "--sbatch",
        dest="sbatch_command",
        type=safe_text,
        default="sbatch",
        help="SLURM submission command for slurm mode (default: sbatch).",
    )
    ap.add_argument(
        "--slurm-script",
        type=safe_text,
        help="SLURM wrapper path (default: <bindcraft-dir>/bindcraft.slurm).",
    )

    resources = ap.add_argument_group("SLURM resource overrides")
    resources.add_argument("--partition", type=safe_text)
    resources.add_argument("--qos", type=safe_text)
    resources.add_argument("--account", type=safe_text)
    resources.add_argument("--gres", type=safe_text, help="For example gpu:1.")
    resources.add_argument("--nodes", type=positive_int)
    resources.add_argument("--ntasks", type=positive_int)
    resources.add_argument("--cpus-per-task", type=positive_int)
    resources.add_argument("--mem", type=safe_text, help="For example 40G.")
    resources.add_argument("--time", type=safe_text, help="For example 72:00:00.")
    resources.add_argument("--job-name", type=safe_text)
    resources.add_argument("--output", type=safe_text, help="SLURM log pattern.")

    ap.add_argument(
        "--check-paths",
        action="store_true",
        help="Require settings/preset/entry-point paths to exist before printing.",
    )
    ap.add_argument(
        "--format",
        choices=("shell", "json"),
        default="shell",
        help="Output format (default: shell).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly label intent; execution is disabled with or without this flag.",
    )
    return ap


def bindcraft_arguments(args: argparse.Namespace) -> list[str]:
    values = ["--settings", args.settings]
    if args.filters:
        values.extend(("--filters", args.filters))
    if args.advanced:
        values.extend(("--advanced", args.advanced))
    return values


def slurm_resources(args: argparse.Namespace) -> list[str]:
    mapping = (
        ("partition", "--partition"),
        ("qos", "--qos"),
        ("account", "--account"),
        ("gres", "--gres"),
        ("nodes", "--nodes"),
        ("ntasks", "--ntasks"),
        ("cpus_per_task", "--cpus-per-task"),
        ("mem", "--mem"),
        ("time", "--time"),
        ("job_name", "--job-name"),
        ("output", "--output"),
    )
    result: list[str] = []
    for attribute, option in mapping:
        value = getattr(args, attribute)
        if value is not None:
            result.append(f"{option}={value}")
    return result


def build_argv(args: argparse.Namespace) -> tuple[list[str], list[Path]]:
    install = Path(args.bindcraft_dir).expanduser()
    config_paths = [Path(args.settings).expanduser()]
    config_paths.extend(
        Path(value).expanduser()
        for value in (args.filters, args.advanced)
        if value is not None
    )

    if args.mode == "direct":
        entry_point = install / "bindcraft.py"
        argv = [args.python_command, "-u", str(entry_point)]
    else:
        entry_point = (
            Path(args.slurm_script).expanduser()
            if args.slurm_script
            else install / "bindcraft.slurm"
        )
        argv = [args.sbatch_command, *slurm_resources(args), str(entry_point)]

    argv.extend(bindcraft_arguments(args))
    return argv, [entry_point, *config_paths]


def check_paths(paths: Sequence[Path]) -> list[str]:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        joined = "\n  - ".join(missing)
        raise ValueError(f"required file path(s) do not exist:\n  - {joined}")
    return [str(path.resolve()) for path in paths]


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    command_argv, paths = build_argv(args)

    checked_paths: list[str] = []
    if args.check_paths:
        try:
            checked_paths = check_paths(paths)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    command = shlex.join(command_argv)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "mode": args.mode,
                    "argv": command_argv,
                    "command": command,
                    "dry_run": True,
                    "executes": False,
                    "checked_paths": checked_paths,
                },
                indent=2,
            )
        )
    else:
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
