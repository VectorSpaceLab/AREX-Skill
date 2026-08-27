#!/usr/bin/env python3
"""Validate GraphRAG prompt-tune output files.

This script performs static checks only. It does not import GraphRAG, read project
configuration, call LLMs, or access storage.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPECTED_FILES = {
    "extract_graph.txt": {"input_text", "tuple_delimiter", "record_delimiter", "completion_delimiter"},
    "summarize_descriptions.txt": {"entity_name", "description_list"},
    "community_report_graph.txt": {"input_text"},
}

OPTIONAL_PLACEHOLDERS = {
    "extract_graph.txt": {"entity_types"},
}

PLACEHOLDER_RE = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a GraphRAG prompt-tune output directory contains the live expected prompt files.",
    )
    parser.add_argument(
        "prompt_dir",
        type=Path,
        help="Directory containing prompt-tune outputs.",
    )
    parser.add_argument(
        "--check-placeholders",
        action="store_true",
        help="Also validate expected template placeholders and suspicious unmatched braces.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow empty prompt files. By default, empty files fail validation.",
    )
    return parser.parse_args()


def brace_balance_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if char == "{" and next_char == "{":
            index += 2
            continue
        if char == "}" and next_char == "}":
            index += 2
            continue
        if char == "{":
            end = text.find("}", index + 1)
            if end == -1:
                warnings.append(f"unmatched '{{' at offset {index}")
                index += 1
                continue
            candidate = text[index + 1 : end]
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
                warnings.append(f"suspicious single-brace text at offset {index}: {{{candidate[:40]}}}")
            index = end + 1
            continue
        if char == "}":
            warnings.append(f"unmatched '}}' at offset {index}")
        index += 1
    return warnings


def validate_file(path: Path, required: set[str], optional: set[str], check_placeholders: bool, allow_empty: bool) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing required file: {path.name}"]
    if not path.is_file():
        return [f"expected a file, got non-file path: {path.name}"]

    text = path.read_text(encoding="utf-8")
    if not allow_empty and not text.strip():
        errors.append(f"empty prompt file: {path.name}")

    if check_placeholders:
        found = set(PLACEHOLDER_RE.findall(text))
        missing = sorted(required - found)
        if missing:
            errors.append(f"{path.name} missing placeholders: {', '.join(missing)}")
        known = required | optional
        unknown = sorted(found - known)
        if unknown:
            errors.append(f"{path.name} has unexpected single-brace placeholders: {', '.join(unknown)}")
        for warning in brace_balance_warnings(text):
            errors.append(f"{path.name}: {warning}")

    return errors


def main() -> int:
    args = parse_args()
    prompt_dir = args.prompt_dir
    errors: list[str] = []

    if not prompt_dir.exists():
        print(f"ERROR: prompt directory does not exist: {prompt_dir}", file=sys.stderr)
        return 2
    if not prompt_dir.is_dir():
        print(f"ERROR: prompt path is not a directory: {prompt_dir}", file=sys.stderr)
        return 2

    for filename, required_placeholders in EXPECTED_FILES.items():
        errors.extend(
            validate_file(
                prompt_dir / filename,
                required_placeholders,
                OPTIONAL_PLACEHOLDERS.get(filename, set()),
                args.check_placeholders,
                args.allow_empty,
            )
        )

    stale_name = prompt_dir / "community_report.txt"
    if stale_name.exists() and not (prompt_dir / "community_report_graph.txt").exists():
        errors.append("found stale community_report.txt but missing live community_report_graph.txt")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: found {len(EXPECTED_FILES)} GraphRAG prompt-tune files in {prompt_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
