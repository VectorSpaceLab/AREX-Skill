#!/usr/bin/env python3
"""Lightweight RST list-pattern checker."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


BULLET_RE = re.compile(r"^(\s*)[-*+]\s+")
NUMBERED_RE = re.compile(r"^(\s*)(?:\d+\.|[a-zA-Z]\.|\#\.)\s+")
DIRECTIVE_RE = re.compile(r"^\s*\.\.\s+")
LIST_TABLE_RE = re.compile(r"^\s*\.\.\s+list-table::")
HEADING_UNDERLINE_RE = re.compile(r"^\s*[=\-~^'\"`#*+<>]{3,}\s*$")


@dataclass(frozen=True)
class Issue:
    path: str
    line: int
    kind: str
    message: str
    context: str


def iter_rst_files(paths: Iterable[str]) -> list[Path]:
    rst_files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            rst_files.extend(
                sorted(candidate for candidate in path.rglob("*.rst") if "_build" not in candidate.parts)
            )
        elif path.suffix.lower() == ".rst":
            rst_files.append(path)
    return rst_files


def check_file(file_path: Path) -> list[Issue]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    issues: list[Issue] = []

    last_list_line = -1
    last_indent_level = -1
    in_list = False
    in_list_table = False
    in_code_block = False
    code_block_indent = 0

    for index, line in enumerate(lines):
        if re.match(r"^\s*\.\.\s+code-block::", line) or line.rstrip().endswith("::"):
            in_code_block = True
            code_block_indent = len(line) - len(line.lstrip())
            continue

        if in_code_block and line.strip():
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= code_block_indent:
                in_code_block = False

        if in_code_block:
            continue

        if LIST_TABLE_RE.match(line):
            in_list_table = True
            continue

        if in_list_table and line.strip() and not line.startswith(" "):
            in_list_table = False

        if in_list_table:
            continue

        if not line.strip():
            continue

        bullet_match = BULLET_RE.match(line)
        numbered_match = NUMBERED_RE.match(line)
        match = bullet_match or numbered_match
        if match:
            indent_level = len(match.group(1))
            if last_list_line >= 0 and indent_level > last_indent_level:
                if index > 0 and lines[index - 1].strip():
                    previous_line = lines[index - 1]
                    if BULLET_RE.match(previous_line) or NUMBERED_RE.match(previous_line):
                        context = "\n".join((lines[last_list_line], previous_line, line))
                        issues.append(
                            Issue(
                                path=file_path.as_posix(),
                                line=index + 1,
                                kind="nested-list",
                                message="nested list starts without a blank line",
                                context=context,
                            )
                        )
            else:
                prev_non_empty_idx = index - 1
                while prev_non_empty_idx >= 0 and not lines[prev_non_empty_idx].strip():
                    prev_non_empty_idx -= 1
                if prev_non_empty_idx >= 0:
                    prev_non_empty = lines[prev_non_empty_idx]
                    has_blank_line_before = prev_non_empty_idx < index - 1
                    prev_is_list_item = bool(BULLET_RE.match(prev_non_empty) or NUMBERED_RE.match(prev_non_empty))
                    prev_is_directive = bool(DIRECTIVE_RE.match(prev_non_empty))
                    prev_is_heading_underline = bool(HEADING_UNDERLINE_RE.match(prev_non_empty))
                    if (
                        not has_blank_line_before
                        and not prev_is_list_item
                        and not prev_is_directive
                        and not prev_is_heading_underline
                    ):
                        context = f"{prev_non_empty}\n{line}"
                        issues.append(
                            Issue(
                                path=file_path.as_posix(),
                                line=index + 1,
                                kind="missing-blank-line",
                                message="list starts without a blank line before it",
                                context=context,
                            )
                        )

            last_list_line = index
            last_indent_level = indent_level
            in_list = True
        else:
            if not line.startswith(" ") or not in_list:
                in_list = False

    return issues


def render_text(issues: list[Issue], file_count: int) -> str:
    if not issues:
        return f"✓ No RST pattern issues found in {file_count} files."

    lines = [f"Found {len(issues)} issue(s) across {file_count} file(s):"]
    for issue in issues:
        lines.append(f"- {issue.path}:{issue.line}: {issue.message}")
        lines.append(f"  kind: {issue.kind}")
        lines.append("  context:")
        for context_line in issue.context.splitlines():
            lines.append(f"    {context_line}")
    return "\n".join(lines)


def render_json(issues: list[Issue], file_count: int) -> str:
    payload = {
        "file_count": file_count,
        "issue_count": len(issues),
        "issues": [
            {
                "path": issue.path,
                "line": issue.line,
                "kind": issue.kind,
                "message": issue.message,
                "context": issue.context,
            }
            for issue in issues
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="RST files or directories to scan (default: docs)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.paths or ["docs"]
    rst_files = iter_rst_files(paths)
    issues: list[Issue] = []
    for file_path in rst_files:
        issues.extend(check_file(file_path))

    output = render_json(issues, len(rst_files)) if args.format == "json" else render_text(issues, len(rst_files))
    print(output)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
