#!/usr/bin/env python3
"""Check that the SwanLab CLI entry point and core command groups are available.

Run this in any environment where `swanlab` is installed:
    python check_swanlab_cli.py

It invokes help commands only; it does not login, upload, sync, or contact a
SwanLab service.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


ROOT_COMMANDS = {
    "api",
    "convert",
    "disabled",
    "local",
    "login",
    "logout",
    "offline",
    "online",
    "ping",
    "sync",
    "verify",
    "watch",
}
API_COMMANDS = {"project", "run", "self-hosted", "user", "workspace"}


def run_help(args: list[str]) -> str:
    cmd = [sys.executable, "-m", "swanlab", *args, "--help"]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout}")
    return proc.stdout


def require_words(output: str, words: set[str], label: str) -> None:
    missing = sorted(word for word in words if word not in output)
    if missing:
        raise AssertionError(f"{label} help is missing expected command(s): {', '.join(missing)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check SwanLab CLI help surfaces without side effects.")
    parser.add_argument("--skip-api", action="store_true", help="Only check root CLI help.")
    args = parser.parse_args(argv)

    try:
        root_help = run_help([])
        require_words(root_help, ROOT_COMMANDS, "root")
        if not args.skip_api:
            api_help = run_help(["api"])
            require_words(api_help, API_COMMANDS, "api")
    except Exception as exc:  # pragma: no cover - diagnostic user interface
        print(f"ERROR: SwanLab CLI help check failed: {exc}", file=sys.stderr)
        return 1

    print("swanlab cli help ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
