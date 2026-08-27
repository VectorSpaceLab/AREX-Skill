#!/usr/bin/env python3
"""Validate the small list-file formats used by VGen workflows."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

DELIM = "|||"


@dataclass
class Problem:
    line_no: int
    message: str
    line: str


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a VGen prompt/data/metric list file.",
        allow_abbrev=False,
    )
    parser.add_argument("list_file", type=Path, help="List file to validate.")
    parser.add_argument(
        "--kind",
        choices=["auto", "prompt", "prompt-or-seed", "path-caption", "metric"],
        default="auto",
        help="Expected row format.",
    )
    parser.add_argument("--root", type=Path, default=Path('.'), help="Base path for optional existence checks.")
    parser.add_argument("--check-exists", action="store_true", help="Verify referenced files/directories exist.")
    parser.add_argument("--allow-blank-lines", action="store_true", help="Permit blank lines.")
    parser.add_argument("--quiet", action="store_true", help="Only print problems.")
    return parser.parse_args(argv)


def detect_kind(line: str) -> str:
    if line.count(DELIM) == 2:
        return "metric"
    if line.count(DELIM) == 1:
        return "path-caption"
    if "|" in line:
        return "prompt-or-seed"
    return "prompt"


def truncate(text: str, limit: int = 140) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def resolve(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else root / path


def validate_line(kind: str, raw_line: str, root: Path, check_exists: bool) -> List[str]:
    problems: List[str] = []
    line = raw_line.strip()
    expected = detect_kind(line) if kind == "auto" else kind

    if expected == "prompt":
        if DELIM in line:
            problems.append("prompt rows must not contain '|||' delimiters")
        if not line:
            problems.append("prompt is empty")
        return problems

    if expected == "prompt-or-seed":
        if DELIM in line:
            problems.append("prompt-or-seed rows must not contain '|||' delimiters")
            return problems
        parts = line.rsplit("|", 1)
        if len(parts) == 2 and parts[1] and not parts[1].isdigit():
            problems.append("manual seed suffix should be an integer when present")
        if not parts[0].strip():
            problems.append("caption is empty")
        return problems

    if expected == "path-caption":
        if line.count(DELIM) != 1:
            problems.append("expected exactly one '|||' delimiter")
            return problems
        path_text, caption = line.split(DELIM)
        if not path_text:
            problems.append("path field is empty")
        if not caption:
            problems.append("caption field is empty")
        if check_exists and path_text:
            candidate = resolve(root, path_text)
            if not candidate.exists():
                problems.append(f"referenced path does not exist: {path_text}")
        return problems

    if expected == "metric":
        if line.count(DELIM) != 2:
            problems.append("expected exactly two '|||' delimiters for video|||reference_dir|||prompt")
            return problems
        video_name, reference_dir, prompt = line.split(DELIM)
        if not video_name:
            problems.append("video filename field is empty")
        if not reference_dir:
            problems.append("reference image directory field is empty")
        if not prompt:
            problems.append("prompt field is empty")
        if check_exists and reference_dir:
            candidate = resolve(root, reference_dir)
            if not candidate.exists():
                problems.append(f"reference directory does not exist: {reference_dir}")
            elif not candidate.is_dir():
                problems.append(f"reference path is not a directory: {reference_dir}")
        return problems

    problems.append(f"unknown kind: {expected}")
    return problems


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    list_file = args.list_file
    if not list_file.is_absolute():
        list_file = root / list_file
    if not list_file.is_file():
        print(f"ERROR: list file not found: {list_file}", file=sys.stderr)
        return 1

    problems: List[Problem] = []
    active = comments = blanks = 0
    detected_kinds = {}

    for line_no, raw_line in enumerate(list_file.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            blanks += 1
            if not args.allow_blank_lines:
                problems.append(Problem(line_no, "blank line", raw_line))
            continue
        if line.startswith("#"):
            comments += 1
            continue
        active += 1
        kind = detect_kind(line) if args.kind == "auto" else args.kind
        detected_kinds[kind] = detected_kinds.get(kind, 0) + 1
        for message in validate_line(args.kind, raw_line, root, args.check_exists):
            problems.append(Problem(line_no, message, raw_line))

    if problems:
        print(f"ERROR: {list_file}", file=sys.stderr)
        for problem in problems:
            print(f"line {problem.line_no}: {problem.message}\n  {truncate(problem.line)}", file=sys.stderr)
        print(f"Summary: active={active} comments={comments} blanks={blanks} kinds={detected_kinds}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"OK: {list_file}")
        print(f"active={active} comments={comments} blanks={blanks} kinds={detected_kinds}")
        if args.check_exists:
            print(f"existence checks resolved relative to: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
