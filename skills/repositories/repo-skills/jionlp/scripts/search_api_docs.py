#!/usr/bin/env python3
"""Noninteractive keyword search across JioNLP docstrings."""

from __future__ import annotations

import argparse
import sys

import jionlp as jio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search public JioNLP docstrings by keyword.")
    parser.add_argument(
        "keywords",
        nargs="+",
        help="One or more keywords to search for in public docstrings.")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of matches to print.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    helper = jio.help
    if helper.function_dict is None:
        helper._prepare()

    query = " ".join(args.keywords)
    matches = list(helper.search(helper.command_parser(query)) or [])
    if not matches:
        print(f"No matches for: {query}")
        return 1

    for name in matches[: args.limit]:
        doc = helper.function_dict[name].strip().splitlines()[0]
        print(f"jio.{name}\n  {doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
