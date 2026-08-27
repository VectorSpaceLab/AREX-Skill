#!/usr/bin/env python3
"""Check whether the ZenML Alembic revision graph has diverging branches."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run 'alembic branches' and fail when diverging migration heads "
            "are reported. The check is read-only and does not connect to or "
            "mutate any database."
        )
    )
    parser.add_argument(
        "--alembic",
        default="alembic",
        help="Alembic executable to run (default: alembic).",
    )
    parser.add_argument(
        "--config",
        default="alembic.ini",
        help="Alembic config file to use when it exists (default: alembic.ini).",
    )
    return parser.parse_args()


def build_command(args: argparse.Namespace) -> list[str]:
    command = [args.alembic]
    config_path = Path(args.config)
    if config_path.is_file():
        command.extend(["-c", str(config_path)])
    command.append("branches")
    return command


def main() -> int:
    args = parse_args()

    if shutil.which(args.alembic) is None:
        print(
            f"Alembic executable not found: {args.alembic}. "
            "Install ZenML with local/server development dependencies or pass "
            "--alembic PATH.",
            file=sys.stderr,
        )
        return 2

    command = build_command(args)
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        print(f"Failed to run Alembic: {error}", file=sys.stderr)
        return 2

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        print("Alembic branch check could not complete.", file=sys.stderr)
        return result.returncode

    if stdout:
        print(stdout)
        print("Warning: diverging Alembic branches detected.", file=sys.stderr)
        return 1

    if stderr:
        print(stderr, file=sys.stderr)
    print("No diverging Alembic branches detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
