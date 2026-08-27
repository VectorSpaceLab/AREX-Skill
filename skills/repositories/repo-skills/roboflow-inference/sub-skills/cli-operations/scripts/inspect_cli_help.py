#!/usr/bin/env python3
"""Smoke the Roboflow Inference CLI help tree.

This helper only runs `inference --version` and `inference ... --help`
commands. It does not start containers or execute model work.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Command:
    label: str
    argv: Sequence[str]


COMMANDS: tuple[Command, ...] = (
    Command("top-level help", ["--help"]),
    Command("version", ["--version"]),
    Command("server help", ["server", "--help"]),
    Command("infer help", ["infer", "--help"]),
    Command("benchmark help", ["benchmark", "--help"]),
    Command("benchmark api-speed help", ["benchmark", "api-speed", "--help"]),
    Command(
        "benchmark python-package-speed help",
        ["benchmark", "python-package-speed", "--help"],
    ),
    Command("cloud help", ["cloud", "--help"]),
    Command("rf-cloud help", ["rf-cloud", "--help"]),
    Command("rf-cloud data-staging help", ["rf-cloud", "data-staging", "--help"]),
    Command(
        "rf-cloud batch-processing help",
        ["rf-cloud", "batch-processing", "--help"],
    ),
    Command("enterprise help", ["enterprise", "--help"]),
    Command(
        "enterprise inference-compiler help",
        ["enterprise", "inference-compiler", "--help"],
    ),
    Command(
        "enterprise compile-model help",
        ["enterprise", "inference-compiler", "compile-model", "--help"],
    ),
    Command("workflows help", ["workflows", "--help"]),
)


def run_command(label: str, argv: Sequence[str]) -> int:
    cmd = [sys.executable, "-m", "inference_cli.main", *argv]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    print(f"\n== {label} ==")
    print(f"command={' '.join(['inference', *argv]) if argv else 'inference'}")
    print(f"exit_code={completed.returncode}")
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print("stderr:")
        print(completed.stderr.rstrip())
    return completed.returncode


def main() -> int:
    exit_code = 0
    for command in COMMANDS:
        exit_code = max(exit_code, run_command(command.label, command.argv))
    if exit_code:
        print("\nOne or more CLI help commands failed.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
