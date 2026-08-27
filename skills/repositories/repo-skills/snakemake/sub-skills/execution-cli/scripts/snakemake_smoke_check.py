#!/usr/bin/env python3
"""Run a self-contained Snakemake CLI dry-run smoke check.

The script creates a temporary tiny workflow, runs a dry-run with the selected
Snakemake executable, validates expected dry-run signals, and deletes the
temporary directory when finished. It does not require the Snakemake source
repository, network access, optional plugins, or user workflow files.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


SNAKEFILE = """\
rule all:
    input:
        "result.txt"

rule make_result:
    output:
        "result.txt"
    shell:
        "printf 'ok\\n' > {output}"
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a temporary tiny Snakefile and run a Snakemake "
            "dry-run with --cores 1 and --printshellcmds."
        )
    )
    parser.add_argument(
        "--snakemake",
        default="snakemake",
        help=(
            "Snakemake command to run, for example 'snakemake' or "
            "'python -m snakemake'. Shell-style quoting is supported."
        ),
    )
    parser.add_argument(
        "--cores",
        default="1",
        help="Value passed to --cores for the dry-run smoke check. Default: 1.",
    )
    parser.add_argument(
        "--show-output",
        action="store_true",
        help="Print captured stdout and stderr from the Snakemake process.",
    )
    parser.add_argument(
        "--keep-tempdir",
        action="store_true",
        help="Keep the temporary workflow directory and print its path.",
    )
    return parser.parse_args()


def command_parts(command: str) -> list[str]:
    try:
        parts = shlex.split(command)
    except ValueError as error:
        raise SystemExit(f"Invalid --snakemake command: {error}") from error
    if not parts:
        raise SystemExit("Invalid --snakemake command: empty command")
    return parts


def build_command(args: argparse.Namespace, snakefile: Path, workdir: Path) -> list[str]:
    return command_parts(args.snakemake) + [
        "--snakefile",
        str(snakefile),
        "--directory",
        str(workdir),
        "--cores",
        str(args.cores),
        "--dry-run",
        "--printshellcmds",
    ]


def run_check(args: argparse.Namespace, workdir: Path) -> subprocess.CompletedProcess[str]:
    snakefile = workdir / "Snakefile"
    snakefile.write_text(SNAKEFILE, encoding="utf-8")
    cmd = build_command(args, snakefile, workdir)
    try:
        return subprocess.run(
            cmd,
            cwd=str(workdir),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        missing = error.filename or cmd[0]
        raise SystemExit(
            f"Could not execute {missing!r}. Check --snakemake or use "
            "--snakemake 'python -m snakemake'."
        ) from error


def print_process_output(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        print("--- stdout ---")
        print(result.stdout.rstrip())
    if result.stderr:
        print("--- stderr ---", file=sys.stderr)
        print(result.stderr.rstrip(), file=sys.stderr)


def validate_output(result: subprocess.CompletedProcess[str]) -> list[str]:
    combined_output = f"{result.stdout}\n{result.stderr}"
    failures: list[str] = []
    if "make_result" not in combined_output:
        failures.append("dry-run output did not mention rule 'make_result'")
    if "result.txt" not in combined_output:
        failures.append("dry-run output did not mention target 'result.txt'")
    if "printf 'ok" not in combined_output and 'printf "ok' not in combined_output:
        failures.append("dry-run output did not include the expected shell command")
    return failures


def run_in_tempdir(args: argparse.Namespace) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    if args.keep_tempdir:
        workdir = Path(tempfile.mkdtemp(prefix="snakemake-smoke-"))
        result = run_check(args, workdir)
        print(f"Temporary workflow directory: {workdir}")
        return result, validate_output(result) if result.returncode == 0 else []

    with tempfile.TemporaryDirectory(prefix="snakemake-smoke-") as tmpdir:
        result = run_check(args, Path(tmpdir))
        return result, validate_output(result) if result.returncode == 0 else []


def main() -> int:
    args = parse_args()
    result, validation_failures = run_in_tempdir(args)

    if args.show_output or result.returncode != 0 or validation_failures:
        print_process_output(result)

    if result.returncode != 0:
        print(
            f"Snakemake smoke check failed with exit code {result.returncode}.",
            file=sys.stderr,
        )
        return result.returncode

    if validation_failures:
        for failure in validation_failures:
            print(f"Snakemake smoke check validation failed: {failure}.", file=sys.stderr)
        return 1

    print("Snakemake smoke check passed: tiny workflow dry-run succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
