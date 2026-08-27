#!/usr/bin/env python3
"""Conservative static checklist for Galaxy datatype sniffer implementations."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Iterable

RISKY_REGEXES = [
    (re.compile(r"\.read\s*\(\s*\)"), "unbounded .read() call"),
    (re.compile(r"readlines\s*\(\s*\)"), "unbounded readlines() call"),
    (re.compile(r"list\s*\(\s*open\s*\("), "materializes open() iterator"),
    (re.compile(r"\.decode\s*\(.*\)\s*\.splitlines\s*\("), "may split a full decoded buffer"),
]

SAFE_HINT_REGEXES = [
    (re.compile(r"\.read\s*\(\s*\d+\s*\)"), "bounded byte read"),
    (re.compile(r"get_headers\s*\("), "Galaxy get_headers helper"),
    (re.compile(r"iter_headers\s*\("), "Galaxy header iterator helper"),
    (re.compile(r"FilePrefix\s*\("), "Galaxy FilePrefix helper"),
    (re.compile(r"is_binary\s*\("), "Galaxy binary check helper"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a Python datatype snippet or file for obvious unbounded read anti-patterns "
            "and print a Galaxy datatype sniffer safety checklist."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Python file/snippet to scan. Use '-' or omit to read from stdin.",
    )
    parser.add_argument(
        "--show-lines",
        action="store_true",
        help="Print matching source lines for each warning/hint.",
    )
    return parser.parse_args()


def load_source(path_arg: str | None) -> tuple[str, str]:
    if not path_arg or path_arg == "-":
        return "<stdin>", sys.stdin.read()
    path = Path(path_arg)
    return str(path), path.read_text(encoding="utf-8")


def iter_matches(source: str, patterns: Iterable[tuple[re.Pattern[str], str]]):
    lines = source.splitlines()
    for line_number, line in enumerate(lines, start=1):
        for pattern, message in patterns:
            if pattern.search(line):
                yield line_number, message, line.strip()


def sniff_function_names(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {"sniff", "set_meta", "set_peek"}:
            names.append(node.name)
    return names


def main() -> int:
    args = parse_args()
    label, source = load_source(args.path)
    warnings = list(iter_matches(source, RISKY_REGEXES))
    hints = list(iter_matches(source, SAFE_HINT_REGEXES))
    methods = sniff_function_names(source)

    print(f"Galaxy datatype sniffer checklist for {label}")
    print("=" * 72)
    if methods:
        print(f"Detected methods: {', '.join(sorted(set(methods)))}")
    else:
        print("Detected methods: none named sniff, set_meta, or set_peek")

    print("\nStatic scan:")
    if warnings:
        print(f"  WARN: found {len(warnings)} obvious risky pattern(s).")
        for line_number, message, line in warnings:
            detail = f" line {line_number}: {message}"
            if args.show_lines:
                detail += f" -> {line}"
            print(f"  -{detail}")
    else:
        print("  OK: no obvious unbounded read/readlines patterns found.")

    if hints:
        print(f"  HINT: found {len(hints)} bounded/helper pattern(s).")
        for line_number, message, line in hints:
            detail = f" line {line_number}: {message}"
            if args.show_lines:
                detail += f" -> {line}"
            print(f"  -{detail}")

    print("\nManual review checklist:")
    checklist = [
        "sniff() must not read or iterate through the entire file",
        "sniff() should use a fixed byte/line bound or Galaxy header/prefix helpers",
        "sniffer order should place rigid formats before broad text/tabular fallbacks",
        "set_meta()/set_peek() should stream or justify any whole-file pass",
        "metadata elements should be consumed by tools, not replace viewers/parsers",
        "tests should include positive, negative, truncated, empty, and large non-match samples",
    ]
    for item in checklist:
        print(f"  - {item}")

    print("\nResult: review required" if warnings else "\nResult: no obvious static blocker; review still required")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
