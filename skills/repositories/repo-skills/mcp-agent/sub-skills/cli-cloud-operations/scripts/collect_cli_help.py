#!/usr/bin/env python3
"""Collect safe --help output for mcp-agent CLI commands.

This script never deploys, logs in, installs clients, or mutates Cloud state. It
only runs commands with --help appended unless the command already contains a
help flag. It is intended for CI-safe command-surface inspection.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_COMMANDS = [
    "mcp-agent",
    "mcp-agent init",
    "mcp-agent config",
    "mcp-agent doctor",
    "mcp-agent dev",
    "mcp-agent deploy",
    "mcp-agent login",
    "mcp-agent install",
    "mcp-agent cloud",
    "mcp-agent cloud servers list",
    "mcp-agent cloud logger tail",
    "mcp-agent cloud env",
    "mcp-agent cloud workflows",
    "mcp-cloud",
    "mcpc",
]

SENSITIVE_ENV_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


@dataclass
class HelpResult:
    command: str
    argv: list[str]
    executable_found: bool
    returncode: int | None
    stdout: str
    stderr: str
    error: str | None = None


def command_with_help(command: str, base_command: str | None = None) -> list[str]:
    parts = shlex.split(command)
    if not parts:
        raise ValueError("empty command")
    if base_command and parts[0] != base_command:
        parts = [base_command, *parts]
    if "--help" not in parts and "-h" not in parts:
        parts.append("--help")
    return parts


def safe_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("MCP_AGENT_DISABLE_VERSION_CHECK", "1")
    env.setdefault("NO_COLOR", "1")
    return env


def redacted_env_snapshot(keys: Iterable[str]) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for key in keys:
        if key not in os.environ:
            continue
        if any(marker in key.upper() for marker in SENSITIVE_ENV_MARKERS):
            snapshot[key] = "<set:redacted>"
        else:
            snapshot[key] = os.environ[key]
    return snapshot


def run_help(command: str, timeout: float, base_command: str | None = None) -> HelpResult:
    try:
        argv = command_with_help(command, base_command=base_command)
    except ValueError as exc:
        return HelpResult(command, [], False, None, "", "", str(exc))

    executable = argv[0]
    executable_found = shutil.which(executable) is not None
    if not executable_found:
        return HelpResult(
            command=command,
            argv=argv,
            executable_found=False,
            returncode=None,
            stdout="",
            stderr="",
            error=f"executable not found: {executable}",
        )

    try:
        completed = subprocess.run(
            argv,
            env=safe_env(),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return HelpResult(
            command=command,
            argv=argv,
            executable_found=True,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        return HelpResult(
            command=command,
            argv=argv,
            executable_found=True,
            returncode=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            error=f"timed out after {timeout}s",
        )
    except OSError as exc:
        return HelpResult(
            command=command,
            argv=argv,
            executable_found=True,
            returncode=None,
            stdout="",
            stderr="",
            error=str(exc),
        )


def render_text(results: list[HelpResult]) -> str:
    chunks: list[str] = []
    for result in results:
        chunks.append(f"## {result.command}")
        chunks.append(f"argv: {' '.join(shlex.quote(part) for part in result.argv)}")
        if result.error:
            chunks.append(f"error: {result.error}")
        if result.returncode is not None:
            chunks.append(f"returncode: {result.returncode}")
        if result.stdout:
            chunks.append("stdout:\n" + result.stdout.rstrip())
        if result.stderr:
            chunks.append("stderr:\n" + result.stderr.rstrip())
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commands",
        nargs="+",
        default=DEFAULT_COMMANDS,
        help="Commands to inspect; --help is appended automatically.",
    )
    parser.add_argument(
        "--base-command",
        help=(
            "Optional executable prepended to commands that do not already start with it. "
            "Use this when passing subcommands such as 'init' or when the executable "
            "is an absolute path to an installed mcp-agent script."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Per-command timeout in seconds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of Markdown-like text.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file. Parent directories are created as needed.",
    )
    args = parser.parse_args()

    results = [run_help(command, args.timeout, base_command=args.base_command) for command in args.commands]
    payload = {
        "ok": all(result.error is None and result.returncode == 0 for result in results),
        "environment": redacted_env_snapshot(
            [
                "MCP_AGENT_DISABLE_VERSION_CHECK",
                "MCP_API_BASE_URL",
                "MCP_API_KEY",
                "MCP_APP_SETTINGS_PRELOAD",
                "MCP_APP_SETTINGS_PRELOAD_STRICT",
            ]
        ),
        "results": [asdict(result) for result in results],
    }

    if args.json:
        output = json.dumps(payload, indent=2, sort_keys=True)
    else:
        output = render_text(results)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + ("" if output.endswith("\n") else "\n"), encoding="utf-8")
    else:
        sys.stdout.write(output + ("" if output.endswith("\n") else "\n"))

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
