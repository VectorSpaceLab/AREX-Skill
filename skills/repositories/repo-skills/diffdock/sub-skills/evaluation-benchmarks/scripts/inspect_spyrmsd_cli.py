#!/usr/bin/env python3
"""Inspect DiffDock's vendored spyrmsd CLI without running RMSD by default."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from typing import Iterable


def sanitize(text: str) -> str:
    replacements = []
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    if cwd:
        replacements.append((cwd, "<cwd>"))
    if home and home != cwd:
        replacements.append((home, "<home>"))
    sanitized = text
    for old, new in replacements:
        sanitized = sanitized.replace(old, new)
    return sanitized


def build_spyrmsd_command(args: argparse.Namespace) -> list[str] | None:
    if not args.reference and not args.molecules:
        return None
    if not args.reference or not args.molecules:
        raise ValueError("constructing a command requires --reference and at least one --molecule")

    command = ["python", "-m", "spyrmsd", args.reference]
    command.extend(args.molecules)
    if args.minimize:
        command.append("--minimize")
    if args.center:
        command.append("--center")
    if args.hydrogens:
        command.append("--hydrogens")
    if args.no_symmetry:
        command.append("--nosymm")
    return command


def run_help(timeout: float) -> tuple[int | None, str, str]:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "spyrmsd", "--help"],
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return None, exc.stdout or "", f"timed out after {timeout:g} seconds"
    except OSError as exc:
        return None, "", str(exc)
    return completed.returncode, completed.stdout, completed.stderr


def first_lines(text: str, limit: int) -> str:
    lines = sanitize(text).splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    shown = "\n".join(lines[:limit])
    return f"{shown}\n... ({len(lines) - limit} more lines omitted)"


def existing_path_warnings(paths: Iterable[str]) -> list[str]:
    warnings = []
    for path in paths:
        if path and not os.path.exists(path):
            warnings.append(f"path does not exist from current working directory: {path}")
    return warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report spyrmsd CLI help availability and optionally print a reference command. This helper does not compute RMSD unless --run-command is passed.",
    )
    parser.add_argument("--reference", help="Reference molecule file for command construction.")
    parser.add_argument("--molecule", dest="molecules", action="append", default=[], help="Molecule file to compare; may be repeated.")
    parser.add_argument("--minimize", action="store_true", help="Add --minimize to the constructed command.")
    parser.add_argument("--center", action="store_true", help="Add --center to the constructed command.")
    parser.add_argument("--hydrogens", action="store_true", help="Add --hydrogens to the constructed command.")
    parser.add_argument("--no-symmetry", dest="no_symmetry", action="store_true", help="Add --nosymm to the constructed command.")
    parser.add_argument("--skip-help", action="store_true", help="Do not run python -m spyrmsd --help.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds for help or optional command execution.")
    parser.add_argument("--check-paths", action="store_true", help="Warn if --reference or --molecule paths do not exist.")
    parser.add_argument("--run-command", action="store_true", help="Actually run the constructed spyrmsd command. By default the command is printed only.")
    parser.add_argument("--max-output-lines", type=int, default=40, help="Maximum stdout/stderr lines to print per section.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        constructed = build_spyrmsd_command(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.check_paths:
        paths = []
        if args.reference:
            paths.append(args.reference)
        paths.extend(args.molecules)
        for warning in existing_path_warnings(paths):
            print(f"warning: {warning}", file=sys.stderr)

    if not args.skip_help:
        return_code, stdout, stderr = run_help(args.timeout)
        if return_code == 0:
            print("spyrmsd_help_status: available")
            if stdout.strip():
                print("spyrmsd_help_stdout:")
                print(first_lines(stdout, args.max_output_lines))
        else:
            print("spyrmsd_help_status: unavailable")
            if return_code is not None:
                print(f"spyrmsd_help_return_code: {return_code}")
            if stderr.strip():
                print("spyrmsd_help_stderr:")
                print(first_lines(stderr, args.max_output_lines))
            elif stdout.strip():
                print("spyrmsd_help_stdout:")
                print(first_lines(stdout, args.max_output_lines))

    if constructed is not None:
        print("spyrmsd_command:")
        print(shlex.join(constructed))

        if args.run_command:
            run_command = [sys.executable if part == "python" else part for part in constructed]
            try:
                completed = subprocess.run(
                    run_command,
                    check=False,
                    text=True,
                    capture_output=True,
                    timeout=args.timeout,
                )
            except subprocess.TimeoutExpired as exc:
                print(f"spyrmsd_run_status: timed out after {args.timeout:g} seconds")
                if exc.stdout:
                    print("spyrmsd_run_stdout:")
                    print(first_lines(exc.stdout, args.max_output_lines))
                return 1
            print(f"spyrmsd_run_return_code: {completed.returncode}")
            if completed.stdout.strip():
                print("spyrmsd_run_stdout:")
                print(first_lines(completed.stdout, args.max_output_lines))
            if completed.stderr.strip():
                print("spyrmsd_run_stderr:")
                print(first_lines(completed.stderr, args.max_output_lines))
            return completed.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
