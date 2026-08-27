#!/usr/bin/env python3
"""Capture ZenML Click help without invoking server-backed commands."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import sys
from typing import Any, Sequence


def _load_cli() -> Any:
    os.environ.setdefault("ZENML_ANALYTICS_OPT_IN", "false")
    os.environ.setdefault("MLSTACKS_ANALYTICS_OPT_OUT", "true")
    os.environ.setdefault("AUTO_OPEN_DASHBOARD", "false")

    try:
        zenml_cli = importlib.import_module("zenml_cli")
        importlib.import_module("zenml.cli")
    except Exception as exc:
        raise RuntimeError(
            "Could not import zenml_cli. Install ZenML with its base "
            "dependencies before taking a CLI help snapshot. If help fails "
            "because an optional integration package is missing, check for "
            "module-level optional imports in CLI or integration code."
        ) from exc

    return zenml_cli.cli


def _resolve_command(cli: Any, command_path: Sequence[str]) -> Any:
    command = cli
    context = None
    for part in command_path:
        if not hasattr(command, "get_command"):
            raise ValueError(
                f"Command path {' '.join(command_path)!r} descends through "
                f"non-group command {part!r}."
            )
        context = command.make_context(command.name or "zenml", [], resilient_parsing=True)
        next_command = command.get_command(context, part)
        if next_command is None:
            available = ", ".join(command.list_commands(context))
            raise ValueError(
                f"Unknown command path segment {part!r}. Available here: "
                f"{available or '<none>'}."
            )
        command = next_command
    return command


def _render_help(command: Any, command_path: Sequence[str]) -> str:
    prog_name = " ".join(["zenml", *command_path]).strip()
    with command.make_context(prog_name, [], resilient_parsing=True) as context:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            help_text = command.get_help(context)
        rich_output = buffer.getvalue()
        if help_text:
            return help_text
        return rich_output


def _iter_subcommands(command: Any) -> list[str]:
    if not hasattr(command, "list_commands"):
        return []
    with command.make_context(command.name or "zenml", [], resilient_parsing=True) as context:
        return list(command.list_commands(context))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture ZenML Click help for the root command or one command path."
    )
    parser.add_argument(
        "--command",
        help="Command path below zenml, for example 'pipeline runs' or 'trigger schedule'.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON with command metadata and help text instead of plain help.",
    )
    args = parser.parse_args(argv)

    try:
        cli = _load_cli()
        command_path = args.command.split() if args.command else []
        command = _resolve_command(cli, command_path)
        help_text = _render_help(command, command_path)
        subcommands = _iter_subcommands(command)
    except Exception as exc:
        print(f"zenml_cli_help_snapshot error: {exc}", file=sys.stderr)
        if exc.__cause__ is not None:
            print(f"cause: {exc.__cause__}", file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "command": " ".join(["zenml", *command_path]),
            "subcommands": subcommands,
            "help": help_text,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(help_text.rstrip())
        if subcommands:
            print("\nSubcommands:")
            for subcommand in subcommands:
                print(f"- {subcommand}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
