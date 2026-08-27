#!/usr/bin/env python3
"""Inspect the installed google-agents-cli Click command tree.

Run this from any environment where `google-agents-cli` is installed:

    python scripts/inspect_cli_tree.py --depth 3
    python scripts/inspect_cli_tree.py --json --depth 4

The script uses public installed-package imports and does not require the source
repository checkout.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import click
from google.agents.cli.main import main as cli


def _summary(cmd: click.Command) -> str:
    text = cmd.help or cmd.short_help or ""
    return text.strip().splitlines()[0] if text else ""


def command_node(cmd: click.Command, name: str, depth: int, max_depth: int) -> dict[str, Any]:
    node: dict[str, Any] = {"name": name, "help": _summary(cmd)}
    if isinstance(cmd, click.Group) and depth < max_depth:
        ctx = click.Context(cmd, info_name=name)
        children: list[dict[str, Any]] = []
        for child_name in cmd.list_commands(ctx):
            try:
                child = cmd.get_command(ctx, child_name)
            except Exception as exc:  # Keep inspection useful if an optional import fails.
                children.append({"name": child_name, "help": "", "import_error": repr(exc)})
                continue
            if child is None:
                children.append({"name": child_name, "help": "", "import_error": "not found"})
                continue
            children.append(command_node(child, child_name, depth + 1, max_depth))
        node["commands"] = children
    return node


def print_tree(node: dict[str, Any], indent: int = 0) -> None:
    prefix = "  " * indent
    help_text = f" — {node['help']}" if node.get("help") else ""
    print(f"{prefix}{node['name']}{help_text}")
    for child in node.get("commands", []):
        print_tree(child, indent + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect installed agents-cli command tree")
    parser.add_argument("--depth", type=int, default=3, help="Maximum command nesting depth to print")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text tree")
    args = parser.parse_args()

    tree = command_node(cli, "agents-cli", 0, max(args.depth, 0))
    if args.json:
        print(json.dumps(tree, indent=2, sort_keys=True))
    else:
        print_tree(tree)


if __name__ == "__main__":
    main()
