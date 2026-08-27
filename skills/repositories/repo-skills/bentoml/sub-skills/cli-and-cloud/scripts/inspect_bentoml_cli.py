#!/usr/bin/env python3
"""Inspect BentoML Click help locally without contacting BentoCloud."""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Iterable

from click.testing import CliRunner

DEFAULT_COMMANDS = [
    "cloud",
    "deploy",
    "deployment",
    "secret",
    "api-token",
    "code",
    "push",
    "pull",
    "env",
]


def _load_cli():
    try:
        module = importlib.import_module("bentoml_cli.cli")
    except ModuleNotFoundError as exc:
        if exc.name in {"bentoml_cli", "bentoml_cli.cli"}:
            message = (
                "Could not import bentoml_cli.cli. Run this helper in an environment where BentoML is installed, "
                "or set PYTHONPATH to a BentoML checkout's src directory for local inspection."
            )
        else:
            message = (
                f"Could not import a BentoML CLI dependency: {exc.name}. "
                "Run this helper in the verified BentoML package environment."
            )
        raise RuntimeError(message) from exc
    return getattr(module, "cli")


def _invoke_help(cli, command: str) -> tuple[int, str]:
    args = command.split() + ["--help"] if command else ["--help"]
    result = CliRunner().invoke(cli, args)
    output = result.output
    stderr = getattr(result, "stderr", "")
    if stderr:
        output += stderr
    return result.exit_code, output


def inspect(commands: Iterable[str]) -> int:
    try:
        cli = _load_cli()
    except RuntimeError as exc:
        print(f"[inspect_bentoml_cli] {exc}", file=sys.stderr)
        return 2
    failures = 0
    for command in commands:
        exit_code, output = _invoke_help(cli, command)
        title = f"bentoml {command}" if command else "bentoml"
        print(f"\n## {title} --help\n")
        print(output.rstrip())
        if exit_code != 0:
            failures += 1
            print(f"[inspect_bentoml_cli] help command failed with exit code {exit_code}", file=sys.stderr)
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commands",
        nargs="*",
        default=DEFAULT_COMMANDS,
        help="Command paths to inspect, for example: cloud deployment 'deployment get'. Use an empty string for root help.",
    )
    args = parser.parse_args(argv)
    return inspect(args.commands)


if __name__ == "__main__":
    raise SystemExit(main())
