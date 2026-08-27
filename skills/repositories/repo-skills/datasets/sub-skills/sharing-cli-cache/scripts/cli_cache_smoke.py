#!/usr/bin/env python3
"""Safe Datasets CLI/cache diagnostic helper.

Default mode is local and non-mutating: it prints Python executable metadata,
cache-related environment variables, and whether `datasets-cli` is available.
Use explicit flags to run safe help/env commands.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence

CACHE_ENV_VARS = (
    "HF_HOME",
    "HF_DATASETS_CACHE",
    "HF_HUB_CACHE",
    "HF_HUB_OFFLINE",
    "HF_DATASETS_IN_MEMORY_MAX_SIZE",
    "HF_DATASETS_OFFLINE",
)


def redact(value: str | None) -> str:
    if value is None:
        return "<unset>"
    if not value:
        return "<empty>"
    lowered = value.lower()
    if "token" in lowered or value.startswith("hf_"):
        return "<redacted>"
    return value


def run_command(command: Sequence[str]) -> int:
    print(f"\n$ {' '.join(command)}")
    completed = subprocess.run(command, check=False, text=True)
    return completed.returncode


def print_env_summary() -> None:
    print("Python")
    print(f"  executable: {sys.executable}")
    print(f"  version: {sys.version.split()[0]}")
    print("\nCache/offline environment")
    for name in CACHE_ENV_VARS:
        print(f"  {name}: {redact(os.environ.get(name))}")

    cli_path = shutil.which("datasets-cli")
    print("\nCLI availability")
    print(f"  datasets-cli: {cli_path or '<not found on PATH>'}")

    try:
        import datasets

        print(f"  datasets import: ok ({datasets.__version__})")
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(f"  datasets import: failed ({type(exc).__name__}: {exc})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print safe local Datasets CLI/cache diagnostics and optionally run non-mutating CLI checks.",
    )
    parser.add_argument(
        "--run-cli-help",
        action="store_true",
        help="Run `datasets-cli --help` if the command is available.",
    )
    parser.add_argument(
        "--run-cli-env",
        action="store_true",
        help="Run `datasets-cli env`. Review output before sharing because it includes platform versions.",
    )
    parser.add_argument(
        "--show-delete-help",
        action="store_true",
        help="Run `datasets-cli delete_from_hub --help` only; does not delete anything.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    print_env_summary()

    cli_path = shutil.which("datasets-cli")
    if not cli_path and (args.run_cli_help or args.run_cli_env or args.show_delete_help):
        print("\nRequested CLI command cannot run because datasets-cli is not on PATH.")
        return 2

    exit_code = 0
    if args.run_cli_help:
        exit_code = max(exit_code, run_command([cli_path, "--help"]))
    if args.run_cli_env:
        exit_code = max(exit_code, run_command([cli_path, "env"]))
    if args.show_delete_help:
        exit_code = max(exit_code, run_command([cli_path, "delete_from_hub", "--help"]))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
