#!/usr/bin/env python3
"""Verify the public `cognee-mcp` surface without starting a listener.

This helper is safe by default:
- it only checks package availability and `--help`
- it never opens a socket
- it never launches the MCP server loop

It is designed to give a clear, user-facing message when the optional `mcp`
package or the `cognee-mcp` entry point is missing.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from typing import Iterable

EXPECTED_TOKENS = [
    "--transport",
    "stdio",
    "sse",
    "http",
    "--host",
    "--port",
    "--path",
    "--log-level",
    "--no-migration",
    "--api-url",
    "--api-token",
    "--serve-url",
    "--serve-api-key",
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


def missing_tokens(text: str, needles: Iterable[str]) -> list[str]:
    return [needle for needle in needles if needle not in text]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check the installed cognee-mcp entry point and its help surface without "
            "starting an MCP listener."
        )
    )
    parser.add_argument(
        "--command",
        default="cognee-mcp",
        help="MCP entry point to inspect (default: cognee-mcp)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only failures and the final summary.",
    )
    args = parser.parse_args()

    failures: list[str] = []

    if importlib.util.find_spec("mcp") is None:
        print("error: missing optional dependency 'mcp'.")
        print("hint: install the MCP server package/extras before checking the surface again.")
        failures.append("mcp package")

    command = args.command
    if shutil.which(command) is None:
        print(f"error: entry point '{command}' was not found on PATH.")
        print("hint: install the MCP server package so the entry point is available.")
        failures.append("entry point")

    if failures:
        print("\nFAILED: MCP surface checks could not run because a required dependency or entry point is missing.")
        for item in failures:
            print(f"- {item}")
        return 1

    result = run_command([command, "--help"])
    output = result.stdout or ""
    if not args.quiet:
        print(output, end="" if output.endswith("\n") else "\n")

    if result.returncode != 0:
        print(f"error: '{command} --help' failed with exit code {result.returncode}.")
        return 1

    missing = missing_tokens(output, EXPECTED_TOKENS)
    if missing:
        print("error: MCP help output is missing expected surface tokens:")
        for token in missing:
            print(f"- {token}")
        return 1

    print("OK: verified MCP package availability and the public `cognee-mcp --help` surface.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
