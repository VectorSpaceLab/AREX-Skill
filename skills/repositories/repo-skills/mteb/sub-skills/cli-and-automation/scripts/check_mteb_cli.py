#!/usr/bin/env python3
"""Safely validate the installed MTEB CLI command surface.

The script only runs help commands by default. It does not execute benchmarks,
download datasets, launch a leaderboard server, or write result files.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass

DEFAULT_SUBCOMMANDS = (
    "run",
    "available-tasks",
    "available-benchmarks",
    "create-model-results",
    "leaderboard",
)

REQUIRED_MARKERS = {
    "run": ("--model", "--tasks", "--output-folder", "--overwrite-strategy"),
    "available-tasks": ("--task-types", "--languages", "--tasks"),
    "available-benchmarks": ("--benchmarks",),
    "create-model-results": ("--model-name", "--results-folder", "--output-path"),
    "create-meta": ("--model-name", "--results-folder", "--output-path"),
    "leaderboard": ("--cache-path", "--host", "--port"),
}

ALIASES = {
    "create-meta": ("create-meta", "create-model-results"),
    "create-model-results": ("create-model-results", "create-meta"),
}


@dataclass(frozen=True)
class CliCommand:
    display: str
    argv: tuple[str, ...]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate MTEB CLI help output without running evaluations."
    )
    parser.add_argument(
        "--command",
        default="mteb",
        help="CLI executable to call. Defaults to 'mteb'.",
    )
    parser.add_argument(
        "--subcommands",
        nargs="+",
        default=list(DEFAULT_SUBCOMMANDS),
        help="Subcommands whose --help output should be checked.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Report missing subcommands but exit successfully.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print captured help snippets for each checked command.",
    )
    return parser.parse_args(argv)


def resolve_command(command: str) -> CliCommand | None:
    executable = shutil.which(command)
    if executable is not None:
        return CliCommand(display=command, argv=(executable,))
    if command == "mteb":
        return CliCommand(display="python -m mteb", argv=(sys.executable, "-m", "mteb"))
    return None


def run_help(command: CliCommand, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*command.argv, *args, "--help"],
        check=False,
        capture_output=True,
        text=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    command = resolve_command(args.command)
    if command is None:
        print(f"ERROR: CLI executable not found on PATH: {args.command}", file=sys.stderr)
        print("Try 'python -m mteb --help' or activate the environment that installed MTEB.", file=sys.stderr)
        return 2

    top_level = run_help(command, [])
    if top_level.returncode != 0:
        print("ERROR: 'mteb --help' failed.", file=sys.stderr)
        if "ModuleNotFoundError" in top_level.stderr or "ImportError" in top_level.stderr:
            print(
                "The MTEB package or one of its import-time dependencies is not available in this environment.",
                file=sys.stderr,
            )
            print(
                "Verify the active Python environment with: python -c 'import mteb' and python -m pip check",
                file=sys.stderr,
            )
        print((top_level.stderr or top_level.stdout).strip(), file=sys.stderr)
        return top_level.returncode or 1

    top_output = f"{top_level.stdout}\n{top_level.stderr}"
    failures: list[str] = []

    for subcommand in args.subcommands:
        candidates = ALIASES.get(subcommand, (subcommand,))
        actual_subcommand = next((candidate for candidate in candidates if candidate in top_output), None)
        if actual_subcommand is None:
            message = f"missing from top-level help: {subcommand}"
            if args.allow_missing:
                print(f"WARN: {message}")
                continue
            failures.append(message)
            continue

        result = run_help(command, [actual_subcommand])
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0:
            failures.append(
                f"'{actual_subcommand} --help' exited with {result.returncode}"
            )
            continue

        missing_markers = [
            marker for marker in REQUIRED_MARKERS.get(subcommand, ()) if marker not in output
        ]
        if missing_markers:
            failures.append(
                f"'{actual_subcommand} --help' missing expected markers: {', '.join(missing_markers)}"
            )
            continue

        alias_note = f" for requested {subcommand}" if actual_subcommand != subcommand else ""
        print(f"OK: {actual_subcommand}{alias_note}")
        if args.verbose:
            snippet = "\n".join(output.strip().splitlines()[:20])
            print(snippet)

    if failures:
        print("ERROR: MTEB CLI validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"OK: MTEB CLI help surface validated via {command.display} without running benchmarks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
