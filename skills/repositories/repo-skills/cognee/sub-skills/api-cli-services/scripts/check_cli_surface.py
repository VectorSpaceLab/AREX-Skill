#!/usr/bin/env python3
"""Verify the public `cognee-cli` help surface without starting services.

This helper is safe by default:
- it only calls `--help` / `--version`
- it never ingests data
- it never starts the API, MCP, or UI servers

Run it from any working directory as long as `cognee-cli` is on PATH.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from typing import Iterable

DEFAULT_SUBCOMMANDS = [
    "add",
    "remember",
    "cognify",
    "search",
    "recall",
    "memify",
    "improve",
    "forget",
    "delete",
    "datasets",
    "agents",
    "sessions",
    "feedback",
    "config",
    "serve",
    "push",
    "eval",
    "upgrade",
    "downgrade",
    "history",
    "current",
    "stamp",
]

TOP_LEVEL_TOKENS = [
    "--api-url",
    "--api-key",
    "--api-token",
    "--user-id",
    "--debug",
    "-ui",
    "--version",
    "Available commands",
]


def run_command(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and capture combined output."""
    return subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def assert_contains(label: str, text: str, needles: Iterable[str]) -> list[str]:
    """Return the missing needles for a help or version output."""
    missing = [needle for needle in needles if needle not in text]
    if missing:
        print(f"[{label}] missing: {', '.join(missing)}")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check the installed cognee-cli entry point and its service-oriented help output. "
            "This script does not start any long-running process."
        )
    )
    parser.add_argument(
        "--command",
        default="cognee-cli",
        help="CLI entry point to inspect (default: cognee-cli)",
    )
    parser.add_argument(
        "--subcommand",
        action="append",
        dest="subcommands",
        help=(
            "Extra subcommands to verify with --help. "
            "May be repeated; defaults to a curated service surface list."
        ),
    )
    parser.add_argument(
        "--skip-version",
        action="store_true",
        help="Skip the `--version` probe.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only failures and the final summary.",
    )
    args = parser.parse_args()

    command = args.command
    if shutil.which(command) is None:
        print(f"error: entry point '{command}' was not found on PATH.")
        print("hint: install the Cognee package or activate the environment that provides cognee-cli.")
        return 1

    subcommands = args.subcommands or DEFAULT_SUBCOMMANDS
    failures: list[str] = []

    help_result = run_command([command, "--help"])
    help_output = help_result.stdout or ""
    if not args.quiet:
        print(help_output, end="" if help_output.endswith("\n") else "\n")
    if help_result.returncode != 0:
        print(f"error: '{command} --help' failed with exit code {help_result.returncode}.")
        failures.append("top-level help")
    else:
        failures.extend(assert_contains("top-level help", help_output, TOP_LEVEL_TOKENS))

    if not args.skip_version:
        version_result = run_command([command, "--version"])
        version_output = version_result.stdout or ""
        if not args.quiet:
            print(version_output, end="" if version_output.endswith("\n") else "\n")
        if version_result.returncode != 0:
            print(f"error: '{command} --version' failed with exit code {version_result.returncode}.")
            failures.append("version")
        elif "cognee" not in version_output.lower():
            print("error: version output did not mention cognee.")
            failures.append("version text")

    for subcommand in subcommands:
        result = run_command([command, subcommand, "--help"])
        output = result.stdout or ""
        if not args.quiet:
            print(f"\n--- {command} {subcommand} --help ---")
            print(output, end="" if output.endswith("\n") else "\n")
        if result.returncode != 0:
            print(f"error: '{command} {subcommand} --help' failed with exit code {result.returncode}.")
            failures.append(f"{subcommand} help")
            continue
        if "usage:" not in output.lower():
            print(f"error: '{command} {subcommand} --help' did not print usage text.")
            failures.append(f"{subcommand} usage")

    if failures:
        print("\nFAILED: cognee-cli surface checks did not match expectations.")
        print("missing or failing checks:")
        for item in failures:
            print(f"- {item}")
        return 1

    print(
        f"OK: verified {command} top-level help, version, and {len(subcommands)} subcommand help probes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
