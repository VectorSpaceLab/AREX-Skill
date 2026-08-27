#!/usr/bin/env python3
"""Validate I2VGen-XL image-plus-caption list files.

The observed VGen inference entry point expects each active line to look like:

    image/path.jpg|||A caption for the image

Comment lines start with '#'. Blank lines are not ignored by the source loader,
so this checker treats them as errors by default.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

DELIM = "|||"


@dataclass
class Problem:
    line_no: int
    message: str
    line: str


def _truncate(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _format_problem(problem: Problem) -> str:
    line = _truncate(problem.line)
    return f"line {problem.line_no}: {problem.message}\n  {line}"


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an I2VGen-XL image|||caption list file.",
    )
    parser.add_argument("list_path", type=Path, help="Path to the list file.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Base directory used to resolve relative image paths.",
    )
    parser.add_argument(
        "--check-exists",
        action="store_true",
        help="Verify that each referenced image file exists under --root.",
    )
    parser.add_argument(
        "--allow-empty-caption",
        action="store_true",
        help="Allow active lines whose caption field is empty.",
    )
    parser.add_argument(
        "--allow-blank-lines",
        action="store_true",
        help="Allow blank lines instead of treating them as malformed.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the success summary and only report problems.",
    )
    return parser.parse_args(argv)


def validate_list(
    list_path: Path,
    root: Path,
    *,
    check_exists: bool = False,
    allow_empty_caption: bool = False,
    allow_blank_lines: bool = False,
) -> tuple[int, int, int, List[Problem]]:
    problems: List[Problem] = []
    active_count = 0
    comment_count = 0
    blank_count = 0

    try:
        lines = list_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        problems.append(Problem(0, f"unable to read list file: {exc}", str(list_path)))
        return active_count, comment_count, blank_count, problems

    for line_no, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        if not stripped:
            blank_count += 1
            if not allow_blank_lines:
                problems.append(
                    Problem(
                        line_no,
                        "blank lines are not ignored by the source loader; remove the line or comment it out",
                        raw_line,
                    )
                )
            continue

        if stripped.startswith("#"):
            comment_count += 1
            continue

        active_count += 1
        if stripped.count(DELIM) != 1:
            problems.append(
                Problem(
                    line_no,
                    f"expected exactly one {DELIM!r} delimiter separating image path and caption",
                    raw_line,
                )
            )
            continue

        image_path, caption = stripped.split(DELIM)

        if image_path != image_path.strip() or caption != caption.strip():
            problems.append(
                Problem(
                    line_no,
                    "do not pad whitespace around the delimiter; the loader uses the fields as-is",
                    raw_line,
                )
            )
            continue

        if not image_path:
            problems.append(Problem(line_no, "image path is empty", raw_line))
            continue

        if not caption and not allow_empty_caption:
            problems.append(
                Problem(
                    line_no,
                    "caption is empty; the source inference loop skips empty captions",
                    raw_line,
                )
            )
            continue

        if check_exists:
            image_file = Path(image_path)
            if not image_file.is_absolute():
                image_file = root / image_file
            try:
                exists = image_file.exists()
            except OSError as exc:
                problems.append(
                    Problem(
                        line_no,
                        f"unable to check image path {image_file}: {exc}",
                        raw_line,
                    )
                )
                continue
            if not exists:
                problems.append(
                    Problem(
                        line_no,
                        f"image file does not exist: {image_path}",
                        raw_line,
                    )
                )
                continue
            if not image_file.is_file():
                problems.append(
                    Problem(
                        line_no,
                        f"image path is not a regular file: {image_path}",
                        raw_line,
                    )
                )

    return active_count, comment_count, blank_count, problems


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    list_path = args.list_path

    active_count, comment_count, blank_count, problems = validate_list(
        list_path,
        root,
        check_exists=args.check_exists,
        allow_empty_caption=args.allow_empty_caption,
        allow_blank_lines=args.allow_blank_lines,
    )

    if problems:
        print(f"ERROR: {list_path}", file=sys.stderr)
        for problem in problems:
            print(_format_problem(problem), file=sys.stderr)
        print(
            f"Summary: {active_count} active, {comment_count} comment, {blank_count} blank line(s)",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"OK: {list_path} — {active_count} active, {comment_count} comment, {blank_count} blank line(s)",
        )
        if args.check_exists:
            print(f"Image existence checked under: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
