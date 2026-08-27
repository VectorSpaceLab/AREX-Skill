#!/usr/bin/env python3
"""Safely inspect Argilla server CLI availability without starting services.

The helper imports package metadata and renders Typer help through
`python -m argilla_server ... --help`. By default it points ARGILLA_HOME_PATH
at a temporary directory so import-time server-id files do not touch a real
Argilla home. It never runs `start`, migrations, workers, reindexing, Docker,
or network operations.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from importlib import import_module, metadata
from typing import Iterable

HELP_GROUPS: dict[str, list[str]] = {
    "root": ["--help"],
    "start": ["start", "--help"],
    "database": ["database", "--help"],
    "database-users": ["database", "users", "--help"],
    "search-engine": ["search-engine", "--help"],
    "worker": ["worker", "--help"],
}


def distribution_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def check_import() -> None:
    module = import_module("argilla_server")
    module_version = getattr(module, "__version__", "unknown")
    print("argilla_server import: ok")
    print(f"argilla_server module version: {module_version}")
    print(f"argilla-server distribution: {distribution_version('argilla-server')}")
    print(f"click distribution: {distribution_version('click')}")
    print(f"typer distribution: {distribution_version('typer')}")


def render_help(args: list[str]) -> int:
    env = os.environ.copy()
    env.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    env.setdefault("HF_HUB_OFFLINE", "1")
    command = [sys.executable, "-m", "argilla_server", *args]
    display_command = ["python", "-m", "argilla_server", *args]
    print("\n$ " + " ".join(display_command))
    completed = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(completed.stdout.rstrip())
    return completed.returncode


def selected_groups(name: str) -> Iterable[tuple[str, list[str]]]:
    if name == "all":
        return HELP_GROUPS.items()
    return [(name, HELP_GROUPS[name])]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Argilla server import and render safe CLI help.")
    parser.add_argument(
        "--group",
        choices=["all", *HELP_GROUPS.keys()],
        default="all",
        help="Which help group to render. Default: all.",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Only render CLI help; do not import argilla_server first.",
    )
    parser.add_argument(
        "--use-current-home",
        action="store_true",
        help="Do not override ARGILLA_HOME_PATH with a temporary directory. Use only when intentionally inspecting a real server home.",
    )
    ns = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="argilla-cli-check-") as temp_home:
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        if not ns.use_current_home:
            os.environ["ARGILLA_HOME_PATH"] = temp_home

        if not ns.skip_import:
            check_import()

        exit_code = 0
        for label, args in selected_groups(ns.group):
            code = render_help(args)
            if code != 0:
                print(f"help group {label!r} failed with exit code {code}", file=sys.stderr)
                exit_code = code if exit_code == 0 else exit_code
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
