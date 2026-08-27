#!/usr/bin/env python3
"""Inspect Snakemake jobscript properties headers.

Snakemake jobscripts commonly contain a line like:

    # properties = {"rule": "example", "threads": 1, ...}

This helper extracts that mapping without importing Snakemake. It is intended for
checking generated jobscripts and custom jobscript templates used by executor
submit wrappers.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

PROPERTIES_RE = re.compile(r"^\s*#\s*properties\s*=\s*(?P<payload>.+?)\s*$")


def parse_properties_line(text: str) -> tuple[dict[str, Any], int]:
    """Return the first properties mapping and its one-based line number."""

    for line_number, line in enumerate(text.splitlines(), start=1):
        match = PROPERTIES_RE.match(line)
        if not match:
            continue
        payload = match.group("payload")
        try:
            value = json.loads(payload)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(payload)
            except (SyntaxError, ValueError) as error:
                raise ValueError(
                    f"properties line {line_number} is not valid JSON or Python literal data"
                ) from error
        if not isinstance(value, dict):
            raise ValueError(f"properties line {line_number} did not contain a mapping")
        return value, line_number
    raise ValueError("no '# properties = ...' line found")


def summarize(properties: dict[str, Any]) -> dict[str, Any]:
    """Return a compact summary of commonly used Snakemake job properties."""

    summary_keys = [
        "rule",
        "jobid",
        "threads",
        "resources",
        "input",
        "output",
        "params",
        "wildcards",
        "conda_env",
        "container_img",
        "env_modules",
    ]
    return {key: properties[key] for key in summary_keys if key in properties}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract and print the '# properties = ...' mapping from a Snakemake jobscript.",
    )
    parser.add_argument(
        "jobscript",
        type=Path,
        help="Path to a generated Snakemake jobscript, not the unrendered template.",
    )
    parser.add_argument(
        "--key",
        help="Print only one top-level property key as JSON. Exits nonzero if missing.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only commonly inspected fields such as rule, resources, input, and output.",
    )
    parser.add_argument(
        "--line-number",
        action="store_true",
        help="Include the one-based line number where the properties header was found.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = args.jobscript.read_text(encoding="utf-8")
    except OSError as error:
        parser.exit(2, f"error: cannot read {args.jobscript}: {error}\n")

    try:
        properties, line_number = parse_properties_line(text)
    except ValueError as error:
        parser.exit(1, f"error: {error}\n")

    if args.key is not None:
        if args.key not in properties:
            parser.exit(1, f"error: key not found: {args.key}\n")
        output: Any = properties[args.key]
    elif args.summary:
        output = summarize(properties)
    else:
        output = properties

    if args.line_number:
        output = {"line_number": line_number, "properties": output}

    json.dump(output, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
