#!/usr/bin/env python3
"""Safe helper for MemMachine CLI command construction and parser checks.

By default this script prints examples and can run `--help`; it never contacts a
MemMachine server or mutates memories.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from typing import Iterable

EXAMPLES = {
    "health": 'mem-cli --base-url "http://localhost:8080" health',
    "project": 'mem-cli --base-url "http://localhost:8080" projects get-or-create --org-id "my-org" --project-id "my-project"',
    "add": 'mem-cli --base-url "http://localhost:8080" memory add "Alice prefers aisle seats." --org-id "my-org" --project-id "my-project" --metadata user_id=alice --metadata agent_id=assistant',
    "search": 'mem-cli --base-url "http://localhost:8080" memory search "What seating does Alice prefer?" --org-id "my-org" --project-id "my-project" --limit 5',
}


def run_help(command: str, timeout: float) -> int:
    exe = shutil.which(command)
    if not exe:
        print(f"{command}: not found on PATH")
        return 1
    proc = subprocess.run(
        [exe, "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    print(proc.stdout)
    return proc.returncode


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MemMachine CLI availability and print safe command examples.")
    parser.add_argument("--command", default="mem-cli", help="CLI command name to inspect, usually mem-cli or memmachine.")
    parser.add_argument("--check-help", action="store_true", help="Run <command> --help without contacting a server.")
    parser.add_argument("--show-example", choices=sorted(EXAMPLES), help="Print one safe example command.")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args(argv)

    rc = 0
    if args.check_help:
        rc = run_help(args.command, args.timeout)
    if args.show_example:
        print(EXAMPLES[args.show_example])
    if not args.check_help and not args.show_example:
        print("CLI command found:" if shutil.which(args.command) else "CLI command not found:", args.command)
        for key, command in EXAMPLES.items():
            print(f"[{key}] {command}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
