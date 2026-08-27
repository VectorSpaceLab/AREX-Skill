#!/usr/bin/env python3
"""List Django management commands or print one command's help safely.

This wrapper intentionally has no mode that calls a management command without
``--help``. It is suitable for parser/discovery inspection, not command
execution or service readiness checks.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


_COMMAND_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_ENTRYPOINT_NAMES = {"manage.py", "django-admin", "django-admin.py", "django-admin.exe"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List Django management commands or show one command's help; "
            "never run a command without --help."
        )
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--project-root",
        type=Path,
        help="Project directory containing manage.py.",
    )
    target.add_argument(
        "--entrypoint",
        help="Installed manage.py/django-admin executable or explicit path.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--list-commands",
        action="store_true",
        help="Print the entrypoint's command listing/help.",
    )
    mode.add_argument(
        "--command-help",
        metavar="COMMAND",
        help="Print help for exactly one management command.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Maximum seconds to wait for parser output (default: 30).",
    )
    return parser


def _validate_command(command: str) -> str:
    if not _COMMAND_RE.fullmatch(command) or command.startswith("-"):
        raise ValueError("COMMAND must be one management-command name, not an option")
    return command


def _resolve_target(args: argparse.Namespace) -> tuple[list[str], Path]:
    if args.timeout <= 0:
        raise ValueError("--timeout must be greater than zero")

    if args.project_root is not None:
        root = args.project_root.expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"project root is not a directory: {root}")
        manage_py = root / "manage.py"
        if not manage_py.is_file():
            raise ValueError(f"project root does not contain manage.py: {root}")
        command = [sys.executable, str(manage_py)]
        return command, root

    entrypoint = os.path.expanduser(args.entrypoint)
    candidate = Path(entrypoint)
    is_explicit_path = candidate.is_absolute() or os.path.sep in entrypoint
    if is_explicit_path:
        resolved = candidate.resolve()
        if resolved.name not in _ENTRYPOINT_NAMES:
            raise ValueError(
                "explicit entrypoint must be manage.py or django-admin"
            )
        if not resolved.is_file():
            raise ValueError(f"entrypoint is not a file: {resolved}")
        if resolved.suffix == ".py":
            return [sys.executable, str(resolved)], resolved.parent
        return [str(resolved)], resolved.parent

    if Path(entrypoint).name not in _ENTRYPOINT_NAMES:
        raise ValueError("installed entrypoint must be manage.py or django-admin")
    installed = shutil.which(entrypoint)
    if installed is None:
        raise ValueError(f"installed entrypoint was not found: {entrypoint}")
    resolved = Path(installed).resolve()
    return [installed], resolved.parent


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        base_command, cwd = _resolve_target(args)
        command = [*base_command]
        if args.list_commands:
            command.append("--help")
        else:
            command.extend([_validate_command(args.command_help), "--help"])
    except ValueError as exc:
        _parser().error(str(exc))

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            check=False,
            text=True,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print(
            "Parser/help inspection timed out; no management command was run.",
            file=sys.stderr,
        )
        return 124
    except OSError as exc:
        print(f"Could not start the help entrypoint: {exc}", file=sys.stderr)
        return os.EX_OSERR if hasattr(os, "EX_OSERR") else 71

    # Preserve the entrypoint's help output and exit status for CI/static use.
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
