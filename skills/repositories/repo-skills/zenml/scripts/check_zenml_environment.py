#!/usr/bin/env python3
"""Safely inspect the active Python environment for ZenML.

The script performs import, distribution metadata, and CLI entry-point checks.
It does not start a ZenML server, connect to a remote server, read secrets,
run pipelines, build Docker images, or mutate configuration.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class CheckResult:
    """Environment check result."""

    ok: bool
    python: str
    zenml_import: str | None
    zenml_version: str | None
    distribution_version: str | None
    cli_entry_point: str | None
    cli_executable: str | None
    cli_help_ok: bool
    messages: list[str]


def get_distribution_version(messages: list[str]) -> str | None:
    """Return installed distribution version if available."""

    try:
        return metadata.version("zenml")
    except metadata.PackageNotFoundError:
        messages.append("Distribution metadata for `zenml` was not found.")
        return None


def get_cli_entry_point(messages: list[str]) -> str | None:
    """Return the `zenml` console script target if installed."""

    try:
        dist = metadata.distribution("zenml")
    except metadata.PackageNotFoundError:
        return None

    for entry_point in dist.entry_points:
        if entry_point.group == "console_scripts" and entry_point.name == "zenml":
            return entry_point.value

    messages.append("Console script entry point `zenml` was not found.")
    return None


def check_import(messages: list[str]) -> tuple[str | None, str | None]:
    """Import ZenML and return module origin plus runtime version."""

    try:
        module = importlib.import_module("zenml")
    except ModuleNotFoundError as exc:
        messages.append(f"Could not import `zenml`: missing module {exc.name!r}.")
        return None, None
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        messages.append(f"Importing `zenml` raised {type(exc).__name__}: {exc}")
        return None, None

    origin = getattr(module, "__file__", None)
    runtime_version = getattr(module, "__version__", None)
    return origin, runtime_version


def check_cli_help(messages: list[str]) -> tuple[str | None, bool]:
    """Run `zenml --help` when the executable is on PATH."""

    executable = shutil.which("zenml")
    if executable is None:
        messages.append("`zenml` executable is not on PATH.")
        return None, False

    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        messages.append("`zenml --help` timed out after 20 seconds.")
        return executable, False

    if completed.returncode != 0:
        stderr = completed.stderr.strip().splitlines()[:3]
        messages.append("`zenml --help` failed: " + " | ".join(stderr))
        return executable, False

    return executable, True


def run_checks() -> CheckResult:
    """Run all safe checks."""

    messages: list[str] = []
    zenml_import, zenml_version = check_import(messages)
    distribution_version = get_distribution_version(messages)
    cli_entry_point = get_cli_entry_point(messages)
    cli_executable, cli_help_ok = check_cli_help(messages)

    ok = bool(zenml_import and distribution_version and cli_entry_point)
    if cli_executable is not None:
        ok = ok and cli_help_ok

    return CheckResult(
        ok=ok,
        python=sys.executable,
        zenml_import=zenml_import,
        zenml_version=zenml_version,
        distribution_version=distribution_version,
        cli_entry_point=cli_entry_point,
        cli_executable=cli_executable,
        cli_help_ok=cli_help_ok,
        messages=messages,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build command-line parser."""

    parser = argparse.ArgumentParser(
        description="Safely inspect ZenML import, metadata, and CLI availability."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON result instead of a human-readable summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point."""

    args = build_parser().parse_args(argv)
    result = run_checks()
    payload: dict[str, Any] = asdict(result)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "OK" if result.ok else "NOT READY"
        print(f"ZenML environment: {status}")
        print(f"Python: {result.python}")
        print(f"Import: {result.zenml_import or 'unavailable'}")
        print(f"Runtime version: {result.zenml_version or 'unknown'}")
        print(f"Distribution version: {result.distribution_version or 'unknown'}")
        print(f"CLI entry point: {result.cli_entry_point or 'missing'}")
        print(f"CLI executable: {result.cli_executable or 'not on PATH'}")
        print(f"CLI help: {'ok' if result.cli_help_ok else 'not verified'}")
        for message in result.messages:
            print(f"- {message}")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
