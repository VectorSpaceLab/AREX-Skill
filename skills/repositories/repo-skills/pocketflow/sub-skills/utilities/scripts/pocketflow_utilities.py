#!/usr/bin/env python3
"""Safe PocketFlow utility helpers.

This script uses only the standard library and optionally PocketFlow for the
Mermaid demo import path. It never calls external APIs.
"""

from __future__ import annotations

import argparse
import os
import sys
from textwrap import dedent


MERMAID_DEMO = dedent(
    """
    graph LR
        start[Load Input] --> chunk[Chunk Text]
        chunk --> embed[Embed Chunks]
        embed --> retrieve[Retrieve Context]
        retrieve --> answer[Generate Answer]
    """
).strip()


def chunk_text(text: str, size: int) -> list[str]:
    if size <= 0:
        raise ValueError("size must be positive")
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


def print_mermaid_demo() -> None:
    try:
        import pocketflow  # noqa: F401
        available = True
    except Exception:
        available = False
    print(MERMAID_DEMO)
    print(f"pocketflow_import={'yes' if available else 'no'}")


def validate_env(keys: list[str]) -> int:
    missing = [key for key in keys if not os.environ.get(key)]
    if missing:
        print("missing:" + ",".join(missing))
        return 1
    print("env_ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PocketFlow utility helper")
    sub = parser.add_subparsers(dest="command", required=True)

    chunk = sub.add_parser("chunk-text", help="Chunk text locally")
    chunk.add_argument("text", help="Text to chunk")
    chunk.add_argument("--size", type=int, default=80, help="Chunk size")

    sub.add_parser("print-mermaid-demo", help="Print a tiny Mermaid graph demo")

    validate = sub.add_parser("validate-env", help="Check that env vars are present")
    validate.add_argument("keys", nargs="+", help="Environment variable names")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "chunk-text":
        for i, chunk in enumerate(chunk_text(args.text, args.size), start=1):
            print(f"[{i}] {chunk}")
        return 0

    if args.command == "print-mermaid-demo":
        print_mermaid_demo()
        return 0

    if args.command == "validate-env":
        return validate_env(args.keys)

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
