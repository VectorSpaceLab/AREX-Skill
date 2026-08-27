#!/usr/bin/env python3
"""Print a compact summary of installed Accelerate CLI help availability."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass

COMMANDS = [
    ("accelerate", []),
    ("accelerate config", ["config"]),
    ("accelerate config default", ["config", "default"]),
    ("accelerate config update", ["config", "update"]),
    ("accelerate env", ["env"]),
    ("accelerate launch", ["launch"]),
    ("accelerate test", ["test"]),
    ("accelerate estimate-memory", ["estimate-memory"]),
    ("accelerate merge-weights", ["merge-weights"]),
    ("accelerate to-fsdp2", ["to-fsdp2"]),
]


@dataclass
class HelpResult:
    name: str
    available: bool
    returncode: int | None
    summary: str


def summarize_help(text: str, max_lines: int) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith(("usage:", "options:", "optional arguments:", "positional arguments:")):
            lines.append(line)
        elif line.startswith("--") or line.startswith("-"):
            lines.append(line)
        if len(lines) >= max_lines:
            break
    return " | ".join(lines) if lines else "help produced no concise usage lines"


def run_help(executable: str, args: list[str], timeout: float, max_lines: int) -> HelpResult:
    command = [executable, *args, "--help"]
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return HelpResult(" ".join([executable, *args]).strip(), False, None, "executable not found")
    except subprocess.TimeoutExpired:
        return HelpResult(" ".join([executable, *args]).strip(), False, None, f"timed out after {timeout:g}s")
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    return HelpResult(
        " ".join([executable, *args]).strip(),
        completed.returncode == 0,
        completed.returncode,
        summarize_help(output, max_lines),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Invoke installed `accelerate --help` subcommands and print a safe availability summary."
    )
    parser.add_argument("--accelerate-bin", default="accelerate", help="Accelerate executable name or path.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds allowed per help command.")
    parser.add_argument("--max-lines", type=int, default=5, help="Maximum usage/option lines to keep per command.")
    parser.add_argument("--include-missing", action="store_true", help="Also print commands whose help exits non-zero.")
    args = parser.parse_args()

    executable = shutil.which(args.accelerate_bin) or args.accelerate_bin
    any_available = False
    any_missing = False

    print(f"Accelerate CLI help summary for: {executable}")
    for display_name, subcommand in COMMANDS:
        result = run_help(executable, subcommand, args.timeout, args.max_lines)
        if result.available:
            any_available = True
            status = "available"
        else:
            any_missing = True
            status = f"unavailable rc={result.returncode}" if result.returncode is not None else "unavailable"
        if result.available or args.include_missing:
            print(f"\n[{status}] {display_name}")
            print(f"  {result.summary}")

    if not any_available:
        print("\nNo Accelerate CLI help commands succeeded.", file=sys.stderr)
        return 1
    if any_missing:
        print("\nSome optional subcommands may be unavailable or changed in this installation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
