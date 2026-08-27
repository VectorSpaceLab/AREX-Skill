#!/usr/bin/env python3
"""Probe nano-graphrag's default JSON repair on raw model output.

Safe by default: this script performs local string parsing only. It does not make
network calls, read credentials, download models, mutate project files, or start
services.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Apply nano_graphrag._utils.convert_response_to_json to raw model "
            "output and fail if no non-empty JSON object can be recovered."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--text",
        help="Raw response string to parse. If omitted, use --file or stdin.",
    )
    source.add_argument(
        "--file",
        type=Path,
        help="Read raw response text from this local file.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding used with --file (default: utf-8).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print recovered JSON instead of compact one-line JSON.",
    )
    return parser


def read_response(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        try:
            return args.file.read_text(encoding=args.encoding)
        except OSError as exc:
            parser.exit(2, f"error: failed to read {args.file}: {exc}\n")
        except UnicodeDecodeError as exc:
            parser.exit(2, f"error: failed to decode {args.file}: {exc}\n")
    if sys.stdin.isatty():
        parser.error("provide --text, --file, or pipe response text on stdin")
    return sys.stdin.read()


def is_meaningful_object(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    response = read_response(args, parser)
    if not response.strip():
        print("No input response text was provided.", file=sys.stderr)
        return 2

    try:
        from nano_graphrag._utils import convert_response_to_json
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(
            "Failed to import nano_graphrag._utils.convert_response_to_json "
            "from the active Python environment. Install nano-graphrag and its "
            f"runtime dependencies before running this probe. Original error: {exc}",
            file=sys.stderr,
        )
        return 3

    try:
        recovered = convert_response_to_json(response)
    except Exception as exc:
        print(f"JSON repair raised an exception: {exc}", file=sys.stderr)
        return 4

    if not is_meaningful_object(recovered):
        print("No meaningful JSON object recovered.", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(recovered, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(recovered, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
