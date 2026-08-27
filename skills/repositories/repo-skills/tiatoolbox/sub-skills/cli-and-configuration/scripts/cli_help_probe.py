#!/usr/bin/env python3
"""Probe TIAToolbox CLI help safely with timeouts.

This script does not depend on a TIAToolbox source checkout. It runs the
installed `tiatoolbox` console command by default and prints concise status
records for top-level help, optional version output, and selected subcommands.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence

DEFAULT_COMMANDS = (
    "slide-info",
    "semantic-segmentor",
    "visualize",
)

KNOWN_COMMANDS = (
    "deep-feature-extractor",
    "multitask-segmentor",
    "nucleus-detector",
    "nucleus-instance-segment",
    "patch-predictor",
    "read-bounds",
    "save-tiles",
    "semantic-segmentor",
    "show-wsi",
    "slide-info",
    "slide-thumbnail",
    "stain-norm",
    "tissue-mask",
    "visualize",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run timeout-bounded TIAToolbox CLI help probes.",
    )
    parser.add_argument(
        "--executable",
        default="tiatoolbox",
        help="Console executable to probe. Default: tiatoolbox.",
    )
    parser.add_argument(
        "--commands",
        nargs="*",
        default=list(DEFAULT_COMMANDS),
        help=(
            "Subcommands to probe with --help. Use 'all' for the known command "
            "set. Default: slide-info semantic-segmentor visualize."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Timeout in seconds for each probe. Default: 20.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Also run tiatoolbox --version.",
    )
    parser.add_argument(
        "--show-output",
        action="store_true",
        help="Print captured stdout/stderr snippets for each probe.",
    )
    return parser.parse_args(argv)


def command_list(commands: Sequence[str]) -> list[str]:
    if len(commands) == 1 and commands[0].lower() == "all":
        return list(KNOWN_COMMANDS)
    return list(commands)


def run_probe(args: Sequence[str], timeout: float) -> tuple[int | None, str, str, str | None]:
    try:
        completed = subprocess.run(
            list(args),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return None, "", str(exc), "not-found"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return None, stdout, stderr, "timeout"
    return completed.returncode, completed.stdout, completed.stderr, None


def print_result(label: str, args: Sequence[str], result: tuple[int | None, str, str, str | None], show_output: bool) -> bool:
    returncode, stdout, stderr, error = result
    printable = " ".join(args)
    if error is None and returncode == 0:
        status = "ok"
    elif error is None:
        status = f"exit-{returncode}"
    else:
        status = error

    print(f"[{status}] {label}: {printable}")
    if show_output:
        if stdout:
            print("--- stdout ---")
            print(stdout[:4000].rstrip())
        if stderr:
            print("--- stderr ---")
            print(stderr[:4000].rstrip())
    return status == "ok"


def main(argv: Sequence[str] | None = None) -> int:
    options = parse_args(argv)
    executable_path = shutil.which(options.executable)
    if executable_path is None:
        print(f"[not-found] executable: {options.executable}", file=sys.stderr)
        print(
            "Tip: activate the environment that installed TIAToolbox or pass "
            "--executable with the console script path.",
            file=sys.stderr,
        )
        return 127

    probes: list[tuple[str, list[str]]] = [
        ("top-level help", [executable_path, "--help"]),
    ]
    if options.version:
        probes.append(("version", [executable_path, "--version"]))
    for command in command_list(options.commands):
        probes.append((f"{command} help", [executable_path, command, "--help"]))

    all_ok = True
    for label, probe_args in probes:
        result = run_probe(probe_args, options.timeout)
        all_ok = print_result(label, probe_args, result, options.show_output) and all_ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
