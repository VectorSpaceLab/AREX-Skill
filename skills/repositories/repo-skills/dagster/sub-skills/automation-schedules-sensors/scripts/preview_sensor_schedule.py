#!/usr/bin/env python3
"""Print safe Dagster CLI commands for inspecting sensors and schedules.

This helper intentionally does not import user code or execute Dagster. It only
validates arguments and prints the command a future agent can run after choosing
an appropriate repository or workspace selector. Sensor preview evaluates one
sensor tick; schedule preview previews reconciliation changes for schedule state.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from collections.abc import Sequence


SELECTOR_HELP = (
    "Additional repository/workspace selector flags as one shell string, for example: "
    "--repository my_repo --attribute defs. Prefer the explicit selector options when possible."
)


def _selector_parts(args: argparse.Namespace) -> list[str]:
    selector: list[str] = []
    for workspace in args.workspace:
        selector.extend(["--workspace", workspace])
    for python_file in args.python_file:
        selector.extend(["--python-file", python_file])
    for module_name in args.module_name:
        selector.extend(["--module-name", module_name])
    for package_name in args.package_name:
        selector.extend(["--package-name", package_name])
    if args.attribute is not None:
        selector.extend(["--attribute", args.attribute])
    if args.working_directory is not None:
        selector.extend(["--working-directory", args.working_directory])
    if args.repository is not None:
        selector.extend(["--repository", args.repository])
    selector.extend(_split_selector(args.selector))
    return selector


def _split_selector(raw_selector: str | None) -> list[str]:
    if raw_selector is None:
        return []
    return shlex.split(raw_selector)


def _format_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def _sensor_command(args: argparse.Namespace) -> list[str]:
    command = ["dagster", "sensor"]
    selector = _selector_parts(args)
    if args.list:
        return [*command, "list", *selector]
    if args.name is None:
        raise ValueError("sensor preview requires --name unless --list is set")

    preview_command = [*command, "preview", args.name, *selector]
    if args.since is not None:
        preview_command.extend(["--since", str(args.since)])
    return preview_command


def _schedule_command(args: argparse.Namespace) -> list[str]:
    selector = _selector_parts(args)
    if args.list:
        return ["dagster", "schedule", "list", *selector]
    return ["dagster", "schedule", "preview", *selector]


def _add_selector_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", action="append", default=[], help="Path to a workspace YAML file.")
    parser.add_argument("--python-file", action="append", default=[], help="Python file target.")
    parser.add_argument("--module-name", action="append", default=[], help="Python module target.")
    parser.add_argument("--package-name", action="append", default=[], help="Python package target.")
    parser.add_argument("--attribute", help="Definitions or repository attribute in the target.")
    parser.add_argument("--working-directory", help="Working directory for file/module/package targets.")
    parser.add_argument("--repository", help="Repository name when the target exposes multiple repositories.")
    parser.add_argument("--selector", help=SELECTOR_HELP)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print parser-validated Dagster CLI commands for sensor preview/list "
            "or schedule preview/list. Schedule preview is state reconciliation, "
            "not a single schedule tick evaluation. No user code is imported."
        )
    )
    subparsers = parser.add_subparsers(dest="kind", required=True)

    sensor_parser = subparsers.add_parser("sensor", help="Print a dagster sensor command.")
    sensor_parser.add_argument("--name", help="Sensor name for dagster sensor preview.")
    _add_selector_options(sensor_parser)
    sensor_parser.add_argument(
        "--since",
        type=float,
        help="Optional timestamp value passed to dagster sensor preview --since.",
    )
    sensor_parser.add_argument(
        "--list",
        action="store_true",
        help="Print dagster sensor list instead of dagster sensor preview.",
    )
    sensor_parser.set_defaults(command_builder=_sensor_command)

    schedule_parser = subparsers.add_parser("schedule", help="Print a dagster schedule command.")
    _add_selector_options(schedule_parser)
    schedule_parser.add_argument(
        "--list",
        action="store_true",
        help="Print dagster schedule list instead of dagster schedule preview.",
    )
    schedule_parser.set_defaults(command_builder=_schedule_command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        command = args.command_builder(args)
    except ValueError as error:
        parser.error(str(error))
    sys.stdout.write(f"{_format_command(command)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
