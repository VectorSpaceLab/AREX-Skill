#!/usr/bin/env python3
"""Normalize a Langflow flow JSON file for stable, git-safe diffs.

This helper wraps langflow_sdk.serialization.normalize_flow_file and
flow_to_json. By default it strips server/UI volatile fields, clears secrets,
sorts keys, and writes normalized JSON to stdout unless --output is provided.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn


def _fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def _load_sdk():
    try:
        from langflow_sdk.serialization import flow_to_json, normalize_flow_file
    except ImportError as exc:
        _fail(
            "could not import langflow_sdk.serialization. Install the SDK with "
            "`python -m pip install langflow-sdk` in the environment running this helper. "
            f"Original import error: {exc}"
        )
    return flow_to_json, normalize_flow_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize a Langflow flow JSON file for deterministic, git-safe output.",
    )
    parser.add_argument("flow_file", type=Path, help="Input Langflow flow JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write normalized JSON to this path. Defaults to stdout.",
    )
    secret_group = parser.add_mutually_exclusive_group()
    secret_group.add_argument(
        "--strip-secrets",
        dest="strip_secrets",
        action="store_true",
        help="Clear template values marked password/load_from_db. This is the safe default.",
    )
    secret_group.add_argument(
        "--no-strip-secrets",
        dest="strip_secrets",
        action="store_false",
        help="Keep template values marked password/load_from_db. Unsafe for committed output.",
    )
    parser.add_argument(
        "--keep-volatile",
        dest="strip_volatile",
        action="store_false",
        help="Keep top-level server-specific fields such as updated_at, user_id, folder_id, access_type, and gradient.",
    )
    parser.add_argument(
        "--keep-node-volatile",
        dest="strip_node_volatile",
        action="store_false",
        help="Keep node UI state such as positionAbsolute, dragging, and selected.",
    )
    parser.add_argument(
        "--no-sort-keys",
        dest="sort_keys",
        action="store_false",
        help="Preserve dictionary insertion order instead of recursively sorting keys.",
    )
    parser.add_argument(
        "--code-as-lines",
        action="store_true",
        help="Convert template fields with type='code' from strings to lists of lines for clearer diffs.",
    )
    parser.set_defaults(strip_secrets=True, strip_volatile=True, strip_node_volatile=True, sort_keys=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    flow_path = args.flow_file
    if not flow_path.exists():
        _fail(f"input file does not exist: {flow_path}")
    if not flow_path.is_file():
        _fail(f"input path is not a file: {flow_path}")

    flow_to_json, normalize_flow_file = _load_sdk()

    try:
        normalized = normalize_flow_file(
            flow_path,
            strip_volatile=args.strip_volatile,
            strip_secrets=args.strip_secrets,
            sort_keys=args.sort_keys,
            code_as_lines=args.code_as_lines,
            strip_node_volatile=args.strip_node_volatile,
        )
        output_text = flow_to_json(normalized)
    except json.JSONDecodeError as exc:
        _fail(f"invalid JSON in {flow_path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    except OSError as exc:
        _fail(f"could not read {flow_path}: {exc}")
    except Exception as exc:  # noqa: BLE001 - provide a clear CLI failure for SDK validation surprises.
        _fail(f"failed to normalize {flow_path}: {exc}")

    if args.output is None:
        print(output_text, end="")
        return 0

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")
    except OSError as exc:
        _fail(f"could not write {args.output}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
