#!/usr/bin/env python3
"""Validate a DeepDanbooru newline-separated tags.txt file without editing it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SYSTEM_TAGS = (
    "rating:general",
    "rating:sensitive",
    "rating:questionable",
    "rating:explicit",
)


def validate(path: Path, require_system_tags: bool, strict_whitespace: bool) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: dict[str, int] = {}
    effective: list[str] = []
    problems: list[str] = []
    warnings: list[str] = []
    blank_lines: list[int] = []

    for line_number, raw in enumerate(lines, start=1):
        tag = raw.strip()
        if not tag:
            blank_lines.append(line_number)
            continue
        if raw != tag:
            message = f"line {line_number}: surrounding whitespace is stripped by the loader"
            (problems if strict_whitespace else warnings).append(message)
        if any(character.isspace() for character in tag):
            problems.append(f"line {line_number}: tag contains whitespace: {tag!r}")
        if tag in seen:
            problems.append(
                f"line {line_number}: duplicate tag {tag!r} (first at line {seen[tag]})"
            )
        else:
            seen[tag] = line_number
        effective.append(tag)

    if not effective:
        problems.append("no effective tags after blank-line removal")
    if blank_lines:
        warnings.append(
            "blank lines are ignored by the loader: " + ", ".join(map(str, blank_lines[:20]))
        )
    if require_system_tags:
        missing = [tag for tag in SYSTEM_TAGS if tag not in seen]
        if missing:
            problems.append("missing required system tags: " + ", ".join(missing))

    return {
        "path": str(path),
        "line_count": len(lines),
        "effective_tag_count": len(effective),
        "unique_tag_count": len(seen),
        "require_system_tags": require_system_tags,
        "problems": problems,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate UTF-8, one-tag-per-line DeepDanbooru tags.txt syntax."
    )
    parser.add_argument("tags_path", type=Path, help="tags.txt file to inspect.")
    parser.add_argument(
        "--require-system-tags",
        action="store_true",
        help="Require all four rating:* tags emitted by download/conversion workflows.",
    )
    parser.add_argument(
        "--strict-whitespace",
        action="store_true",
        help="Treat surrounding whitespace as a failure instead of a warning.",
    )
    parser.add_argument("--json", action="store_true", help="Emit one JSON report.")
    args = parser.parse_args(argv)

    path = args.tags_path.expanduser().resolve()
    try:
        if not path.is_file():
            raise FileNotFoundError(f"tags file does not exist: {path}")
        report = validate(path, args.require_system_tags, args.strict_whitespace)
    except (OSError, UnicodeError) as exc:
        if args.json:
            print(json.dumps({"path": str(path), "error": str(exc)}, indent=2))
        else:
            print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    failed = bool(report["problems"])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"{'FAIL' if failed else 'PASS'}: {path} "
            f"(effective={report['effective_tag_count']}, unique={report['unique_tag_count']})"
        )
        for problem in report["problems"]:
            print(f"  problem: {problem}")
        for warning in report["warnings"]:
            print(f"  warning: {warning}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
