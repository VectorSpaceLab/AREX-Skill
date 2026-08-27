#!/usr/bin/env python3
"""Smoke-check Marker's server CLI without starting a server."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_executable(command: str) -> str | None:
    executable = shutil.which(command)
    if executable:
        return executable
    sibling = Path(sys.executable).resolve().parent / command
    if sibling.exists() and sibling.is_file():
        return str(sibling)
    return None


def run_help(command: str, timeout: float) -> dict[str, Any]:
    executable = find_executable(command)
    if executable is None:
        return {
            "ok": False,
            "check": "cli-help",
            "command": command,
            "error": f"{command!r} was not found on PATH or next to the active Python",
        }

    try:
        completed = subprocess.run(
            [executable, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "check": "cli-help",
            "command": command,
            "error": f"{command} --help timed out after {timeout:g}s",
        }

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    has_expected_flags = "--port" in stdout and "--host" in stdout
    return {
        "ok": completed.returncode == 0 and has_expected_flags,
        "check": "cli-help",
        "command": command,
        "returncode": completed.returncode,
        "has_host_flag": "--host" in stdout,
        "has_port_flag": "--port" in stdout,
        "stderr_tail": stderr[-800:],
    }


def run_import_check() -> dict[str, Any]:
    try:
        module = importlib.import_module("marker.scripts.server")
    except Exception as exc:  # noqa: BLE001 - smoke tool should report any import failure.
        return {
            "ok": False,
            "check": "import",
            "module": "marker.scripts.server",
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "ok": hasattr(module, "app") and hasattr(module, "server_cli"),
        "check": "import",
        "module": "marker.scripts.server",
        "has_app": hasattr(module, "app"),
        "has_server_cli": hasattr(module, "server_cli"),
    }


def print_human(results: list[dict[str, Any]]) -> None:
    for result in results:
        status = "ok" if result.get("ok") else "failed"
        check = result.get("check", "check")
        print(f"{check}: {status}")
        if result.get("error"):
            print(f"  error: {result['error']}")
        if result.get("stderr_tail"):
            print("  stderr tail:")
            print(result["stderr_tail"].rstrip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify Marker server CLI help and, optionally, marker.scripts.server "
            "imports without starting uvicorn."
        )
    )
    parser.add_argument(
        "--command",
        default="marker_server",
        help="Server console script to inspect; default: marker_server.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for the help command; default: 20.",
    )
    parser.add_argument(
        "--check-import",
        action="store_true",
        help="Also import marker.scripts.server and check app/server_cli attributes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of human text.",
    )
    args = parser.parse_args(argv)

    results = [run_help(args.command, args.timeout)]
    if args.check_import:
        results.append(run_import_check())

    if args.json:
        print(json.dumps({"ok": all(item.get("ok") for item in results), "results": results}, indent=2))
    else:
        print_human(results)

    return 0 if all(item.get("ok") for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
