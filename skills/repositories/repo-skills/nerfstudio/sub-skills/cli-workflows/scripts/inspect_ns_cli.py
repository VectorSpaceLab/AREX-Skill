#!/usr/bin/env python3
"""Inspect installed Nerfstudio `ns-*` console scripts safely.

Example:
    python inspect_ns_cli.py --commands ns-train ns-process-data --run-help
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from importlib import metadata

DEFAULT_COMMANDS = [
    "ns-install-cli",
    "ns-process-data",
    "ns-download-data",
    "ns-train",
    "ns-viewer",
    "ns-eval",
    "ns-render",
    "ns-export",
]


def console_entry_points() -> dict[str, str]:
    eps = metadata.entry_points()
    if hasattr(eps, "select"):
        selected = eps.select(group="console_scripts")
    else:
        selected = eps.get("console_scripts", [])
    return {ep.name: ep.value for ep in selected if ep.name.startswith("ns-")}


def main() -> int:
    parser = argparse.ArgumentParser(description="List and optionally --help-check Nerfstudio console scripts.")
    parser.add_argument("--commands", nargs="*", default=DEFAULT_COMMANDS, help="Commands to inspect.")
    parser.add_argument("--run-help", action="store_true", help="Run COMMAND --help for each command.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds per --help check.")
    args = parser.parse_args()

    try:
        version = metadata.version("nerfstudio")
        print(f"nerfstudio distribution: {version}")
    except Exception as exc:
        print(f"nerfstudio distribution metadata not found: {exc}", file=sys.stderr)
        return 1

    entry_points = console_entry_points()
    failures = []
    for command in args.commands:
        value = entry_points.get(command, "not registered")
        path = shutil.which(command)
        print(f"{command}: entry_point={value}; path={path or 'not on PATH'}")
        if value == "not registered" or path is None:
            failures.append(f"{command} is not fully installed")
            continue
        if args.run_help:
            try:
                proc = subprocess.run([path, "--help"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                failures.append(f"{command} --help timed out")
                continue
            first = proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "help printed"
            print(f"  help exit={proc.returncode}; first line: {first}")
            if proc.returncode != 0:
                failures.append(f"{command} --help exited {proc.returncode}")

    if failures:
        print("Failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
