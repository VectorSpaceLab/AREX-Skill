#!/usr/bin/env python3
"""Validate JSON or regex structure without invoking a model or network."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


def parse_json(raw: str, label: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc.msg}") from exc


def validate_json(schema_raw: str, data_raw: str) -> int:
    schema = parse_json(schema_raw, "--schema")
    data = parse_json(data_raw, "--data")
    try:
        from jsonschema import Draft202012Validator

        errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    except ImportError as exc:  # pragma: no cover - base Outlines installs jsonschema
        print(f"error: jsonschema is required for JSON validation: {exc}", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            path = ".".join(str(part) for part in error.path) or "<root>"
            print(f"invalid: {path}: {error.message}", file=sys.stderr)
        return 1

    print("valid: JSON data matches schema")
    return 0


def validate_regex(pattern: str, text: str) -> int:
    try:
        matched = re.fullmatch(pattern, text)
    except re.error as exc:
        print(f"error: invalid regex: {exc}", file=sys.stderr)
        return 2
    if matched is None:
        print("invalid: text does not fully match regex", file=sys.stderr)
        return 1
    print("valid: text fully matches regex")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a JSON sample against a JSON Schema or text against a regex."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    json_parser = subparsers.add_parser("json", help="validate JSON data against a JSON Schema")
    json_parser.add_argument("--schema", required=True, help="JSON Schema object")
    json_parser.add_argument("--data", required=True, help="JSON data to validate")

    regex_parser = subparsers.add_parser("regex", help="validate text with a regular expression")
    regex_parser.add_argument("--pattern", required=True, help="Python regular-expression pattern")
    regex_parser.add_argument("--text", required=True, help="text that must match fully")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "json":
            return validate_json(args.schema, args.data)
        return validate_regex(args.pattern, args.text)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
