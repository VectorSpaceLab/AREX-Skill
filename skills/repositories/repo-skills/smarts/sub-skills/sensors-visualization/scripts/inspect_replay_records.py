#!/usr/bin/env python3
"""Read-only summary and JSON validation for SMARTS/Envision JSONL records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def _files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from sorted(path.rglob("*.jsonl"))


def _shape(value) -> str:
    if isinstance(value, list):
        return f"list[{len(value)}]"
    if isinstance(value, dict):
        return f"object[{len(value)}]"
    return type(value).__name__


def inspect_file(path: Path, max_lines: int) -> bool:
    lines = 0
    valid = 0
    malformed = 0
    first_shape = "<empty>"
    first_kind = "<empty>"
    last_frame_time = None
    with path.open("r", encoding="utf-8") as stream:
        for raw in stream:
            if lines >= max_lines:
                break
            lines += 1
            text = raw.rstrip("\n")
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                malformed += 1
                print(f"  malformed line {lines}: {exc.msg}")
                continue
            valid += 1
            if valid == 1:
                first_shape = _shape(value)
                if isinstance(value, list) and value:
                    first_kind = "numeric-frame" if isinstance(value[0], (int, float)) else "preamble-or-state"
                    if isinstance(value[0], (int, float)):
                        last_frame_time = value[0]
                else:
                    first_kind = "json-value"
            elif isinstance(value, list) and value and isinstance(value[0], (int, float)):
                last_frame_time = value[0]
    truncated = " (limited)" if lines >= max_lines else ""
    print(
        f"{path}: bytes={path.stat().st_size} lines={lines}{truncated} "
        f"valid={valid} malformed={malformed} first={first_shape} kind={first_kind} "
        f"last_numeric_frame_time={last_frame_time}"
    )
    return lines > 0 and malformed == 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize Envision JSONL without sending or editing records."
    )
    parser.add_argument("path", type=Path, help="a JSONL file or directory to scan")
    parser.add_argument(
        "--max-lines",
        type=int,
        default=1000,
        help="maximum lines read per file (default: 1000)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_lines < 1:
        raise SystemExit("--max-lines must be positive")
    if not args.path.exists():
        raise SystemExit(f"path does not exist: {args.path}")
    paths = list(_files(args.path))
    if not paths:
        print("No .jsonl files found")
        return 1
    results = [inspect_file(path, args.max_lines) for path in paths]
    print(f"RESULT={'pass' if all(results) else 'incomplete'} files={len(paths)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
