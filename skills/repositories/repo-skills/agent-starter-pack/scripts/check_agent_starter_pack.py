#!/usr/bin/env python3
"""Read-only sanity checks for an installed agent-starter-pack package.

This helper is safe to run from a generated skill checkout or an installed
inspection environment. It does not create projects, contact Google Cloud, or
modify any files.
"""

from __future__ import annotations

import argparse
import inspect
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from importlib.metadata import PackageNotFoundError, version as distribution_version
from typing import Any

DISTRIBUTION_NAME = "agent-starter-pack"
MODULE_NAME = "agent_starter_pack.cli.main"


@dataclass
class CheckSummary:
    distribution: str = DISTRIBUTION_NAME
    version: str | None = None
    module: str = MODULE_NAME
    module_file: str | None = None
    cli_signature: str | None = None
    command_names: list[str] = field(default_factory=list)
    pip_check_ran: bool = False
    pip_check_exit_code: int | None = None


def collect_summary(check_pip: bool = False) -> CheckSummary:
    """Collect version, import, and command metadata."""
    summary = CheckSummary()

    try:
        summary.version = distribution_version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        summary.version = None

    import agent_starter_pack.cli.main as cli_main

    summary.module_file = getattr(cli_main, "__file__", None)
    summary.cli_signature = str(inspect.signature(cli_main.cli))
    summary.command_names = sorted(cli_main.cli.commands.keys())

    if check_pip:
        summary.pip_check_ran = True
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            check=True,
            capture_output=True,
            text=True,
        )
        summary.pip_check_exit_code = completed.returncode

    return summary


def main(argv: list[str] | None = None) -> int:
    """Entry point for the checker."""
    parser = argparse.ArgumentParser(
        description="Read-only sanity checks for agent-starter-pack installation."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON summary.",
    )
    parser.add_argument(
        "--check-pip",
        action="store_true",
        help="Also run 'python -m pip check' from the current interpreter.",
    )
    args = parser.parse_args(argv)

    try:
        summary = collect_summary(check_pip=args.check_pip)
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload: dict[str, Any] = asdict(summary)
    payload["python"] = sys.version.split()[0]
    payload["executable"] = sys.executable

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"distribution: {payload['distribution']}")
        print(f"version: {payload['version']}")
        print(f"module: {payload['module']}")
        print(f"module_file: {payload['module_file']}")
        print(f"cli_signature: {payload['cli_signature']}")
        print(f"commands: {', '.join(payload['command_names'])}")
        print(f"python: {payload['python']}")
        print(f"executable: {payload['executable']}")
        if args.check_pip:
            print(f"pip_check_exit_code: {payload['pip_check_exit_code']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
