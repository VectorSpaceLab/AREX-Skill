#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Inspect installed Apache Airflow and airflowctl argparse command groups."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from argparse import _SubParsersAction
from importlib.metadata import PackageNotFoundError, version
from typing import Any

DISTRIBUTIONS = (
    "apache-airflow",
    "apache-airflow-core",
    "apache-airflow-task-sdk",
    "apache-airflow-ctl",
    "apache-airflow-providers-standard",
)

PARSER_MODULES = {
    "airflow": "airflow.cli.cli_parser",
    "airflowctl": "airflowctl.ctl.cli_parser",
}


def get_distribution_versions() -> dict[str, str | None]:
    """Return installed distribution versions when import metadata is available."""
    versions: dict[str, str | None] = {}
    for distribution in DISTRIBUTIONS:
        try:
            versions[distribution] = version(distribution)
        except PackageNotFoundError:
            versions[distribution] = None
    return versions


def get_parser_for(command: str) -> argparse.ArgumentParser:
    """Import a CLI parser module and build its top-level parser."""
    module = importlib.import_module(PARSER_MODULES[command])
    return module.get_parser()


def iter_subparser_actions(parser: argparse.ArgumentParser) -> list[_SubParsersAction]:
    """Return argparse subparser actions attached to a parser."""
    return [action for action in parser._actions if isinstance(action, _SubParsersAction)]


def get_option_dests(parser: argparse.ArgumentParser) -> list[str]:
    """Return stable destination names for optional arguments on a parser."""
    return sorted(
        action.dest
        for action in parser._actions
        if action.option_strings and action.dest != argparse.SUPPRESS
    )


def inspect_parser(command: str) -> dict[str, Any]:
    """Inspect one installed CLI parser and return command groups as JSON-safe data."""
    parser = get_parser_for(command)
    commands: dict[str, dict[str, Any]] = {}
    for subparser_action in iter_subparser_actions(parser):
        for command_name, subparser in sorted(subparser_action.choices.items()):
            child_groups: dict[str, list[str]] = {}
            for child_action in iter_subparser_actions(subparser):
                for child_name, child_parser in sorted(child_action.choices.items()):
                    child_groups[child_name] = get_option_dests(child_parser)
            commands[command_name] = {
                "options": get_option_dests(subparser),
                "subcommands": child_groups,
            }
    return {
        "prog": parser.prog,
        "commands": commands,
        "top_level_options": get_option_dests(parser),
    }


def check_imports(selected: list[str]) -> dict[str, dict[str, str | bool]]:
    """Import parser modules and report success without printing tracebacks."""
    results: dict[str, dict[str, str | bool]] = {}
    for command in selected:
        module_name = PARSER_MODULES[command]
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report import failure without hiding the exception class.
            results[command] = {
                "ok": False,
                "module": module_name,
                "error": f"{type(exc).__name__}: {exc}",
            }
        else:
            results[command] = {"ok": True, "module": module_name, "error": ""}
    return results


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--which",
        choices=("airflow", "airflowctl", "both"),
        default="both",
        help="Which installed CLI parser to inspect.",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Report parser-module import status before parser inspection.",
    )
    return parser.parse_args()


def main() -> int:
    """Run parser inspection."""
    args = parse_args()
    selected = ["airflow", "airflowctl"] if args.which == "both" else [args.which]

    output: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "distributions": get_distribution_versions(),
    }
    if args.check_imports:
        output["imports"] = check_imports(selected)

    inspections: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for command in selected:
        try:
            inspections[command] = inspect_parser(command)
        except Exception as exc:  # noqa: BLE001 - keep this diagnostic helper resilient.
            errors[command] = f"{type(exc).__name__}: {exc}"

    output["cli"] = inspections
    if errors:
        output["errors"] = errors

    json.dump(output, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
