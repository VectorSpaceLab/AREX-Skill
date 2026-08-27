#!/usr/bin/env python3
"""Build shell-safe lm_eval --model_args strings from key=value pairs."""

from __future__ import annotations

import argparse
import json
import shlex
import sys


_TRUE_FALSE_NULL = {
    "true": "True",
    "false": "False",
    "none": "None",
    "null": "None",
}


def split_assignment(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"Expected key=value, got {raw!r}")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"Empty key in {raw!r}")
    if any(ch in key for ch in ",= \t\n"):
        raise argparse.ArgumentTypeError(
            f"Key {key!r} contains whitespace, comma, or equals sign"
        )
    return key, value.strip()


def normalize_value(value: str, literal_mode: bool) -> str:
    if not literal_mode:
        return value
    lowered = value.lower()
    if lowered in _TRUE_FALSE_NULL:
        return _TRUE_FALSE_NULL[lowered]
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    if isinstance(parsed, bool):
        return "True" if parsed else "False"
    if parsed is None:
        return "None"
    if isinstance(parsed, (int, float)):
        return str(parsed)
    return value


def validate_value(key: str, value: str) -> None:
    if "," in value:
        raise ValueError(
            f"Value for {key!r} contains a comma. The lm_eval string parser splits "
            "model_args on every comma, so use a configuration file with model_args "
            "as a mapping for this value."
        )
    if "\n" in value or "\r" in value:
        raise ValueError(f"Value for {key!r} contains a newline")


def build_model_args(assignments: list[tuple[str, str]], literal_mode: bool) -> str:
    seen: set[str] = set()
    parts: list[str] = []
    for key, raw_value in assignments:
        if key in seen:
            raise ValueError(f"Duplicate key: {key}")
        seen.add(key)
        value = normalize_value(raw_value, literal_mode)
        validate_value(key, value)
        parts.append(f"{key}={value}")
    return ",".join(parts)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a comma-separated lm_eval --model_args string safely."
    )
    parser.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Model argument assignment. May be passed multiple times.",
    )
    parser.add_argument(
        "--literal",
        action="store_true",
        help="Normalize JSON booleans/null to Python-style True/False/None for lm_eval literal parsing.",
    )
    parser.add_argument(
        "--shell-quote",
        action="store_true",
        help="Print a shell-quoted version suitable for copy/paste after --model_args.",
    )
    parser.add_argument(
        "--as-json",
        action="store_true",
        help="Print both raw and shell-quoted forms as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.sets:
        print("Provide at least one --set KEY=VALUE assignment.", file=sys.stderr)
        return 2
    assignments = [split_assignment(item) for item in args.sets]
    try:
        raw = build_model_args(assignments, args.literal)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    quoted = shlex.quote(raw)
    if args.as_json:
        print(json.dumps({"model_args": raw, "shell_quoted": quoted}, indent=2))
    elif args.shell_quote:
        print(quoted)
    else:
        print(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
