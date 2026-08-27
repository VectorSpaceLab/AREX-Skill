#!/usr/bin/env python3
"""Inspect the installed Jina CLI parser without modifying source files."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    from jina.parsers import get_main_parser

    main_parser = get_main_parser()
    subparsers = main_parser._actions[-1]
    commands = {}
    for name, subparser in sorted(subparsers.choices.items()):
        commands[name] = {
            "help": subparser.description or subparser.prog,
            "options": [opt for action in subparser._actions for opt in action.option_strings if opt.startswith("--")],
        }

    if args.format == "json":
        print(json.dumps({"commands": commands}, indent=2, sort_keys=True))
    else:
        print("| Command | Help | Selected options |")
        print("|---|---|---|")
        for name, info in commands.items():
            options = ", ".join(info["options"][:12])
            print(f"| `jina {name}` | {info['help']} | {options} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
