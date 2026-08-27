#!/usr/bin/env python3
"""Inspect Khoj CLI parser behavior without importing khoj.main.

The installed console script resolves khoj.main:run before parsing arguments, and
that import initializes Django, migrations, and static collection. This helper
imports only khoj.utils.cli.cli so it can be used for parser-only diagnostics.
"""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from typing import Any


def _load_cli():
    try:
        from khoj.utils.cli import cli
    except ModuleNotFoundError as error:
        if error.name == "khoj":
            payload = {
                "error": "Khoj package is not importable in this Python environment.",
                "safety": "Did not import khoj.main, start Django, run migrations, collect static files, or start a server.",
                "next_steps": [
                    "Run this helper with the Python environment where the khoj package is installed.",
                    "Install Khoj into the current environment before using parser inspection.",
                ],
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            raise SystemExit(2) from error
        raise
    return cli


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Khoj CLI parser defaults or supplied flags without importing khoj.main."
    )
    parser.add_argument(
        "--args",
        action="store_true",
        help="Treat all remaining tokens as Khoj CLI arguments. Use --args -- before Khoj flags.",
    )
    parsed, remaining_args = parser.parse_known_args()

    if remaining_args and not parsed.args:
        parser.error("Khoj CLI arguments must follow --args --")

    supplied_args = list(remaining_args) if parsed.args else []
    if supplied_args[:1] == ["--"]:
        supplied_args = supplied_args[1:]

    cli = _load_cli()
    try:
        namespace = cli(supplied_args)
    except PackageNotFoundError as error:
        payload = {
            "error": "Khoj package metadata is not installed in this Python environment.",
            "package": str(error),
            "supplied_args": supplied_args,
            "safety": "Imported khoj.utils.cli.cli only; did not import khoj.main, start Django, run migrations, collect static files, or start a server.",
            "next_steps": [
                "Run this helper with the Python environment where the khoj distribution is installed.",
                "Install Khoj into the current environment before using parser inspection.",
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    payload = {
        "supplied_args": supplied_args,
        "parsed": vars(namespace),
        "safety": "Imported khoj.utils.cli.cli only; did not import khoj.main, start Django, run migrations, collect static files, or start a server.",
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
