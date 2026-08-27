#!/usr/bin/env python3
"""Scan a directory for configurable TODO comments and emit JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SUPPORTED_SUFFIXES = {".py", ".ts", ".java", ".rs"}


def scan_file_for_todos(file_path: Path, identifier: str) -> list[dict[str, object]]:
    if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        return []
    file_str = str(file_path)
    if (
        "/tests/" in file_str
        or "/test" in file_str
        or "test_" in file_path.name
        or "examples/03_github_workflows/03_todo_management/" in file_str
    ):
        return []
    pattern = re.compile(rf"{re.escape(identifier)}(?::\s*(.*))?", re.IGNORECASE)
    todos: list[dict[str, object]] = []
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    for line_num, line in enumerate(lines, 1):
        match = pattern.search(line)
        if match:
            todos.append(
                {
                    "file": str(file_path),
                    "line": line_num,
                    "description": (match.group(1) or "").strip(),
                }
            )
    return todos


def scan_directory(directory: Path, identifier: str) -> list[dict[str, object]]:
    todos: list[dict[str, object]] = []
    for path in directory.rglob("*"):
        if path.is_file() and not any(part.startswith(".") for part in path.parts):
            todos.extend(scan_file_for_todos(path, identifier))
    return todos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--identifier", "-i", default="TODO(openhands)")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()

    path = Path(args.directory)
    if not path.exists():
        print(f"Path does not exist: {path}", file=sys.stderr)
        return 1
    todos = (
        scan_file_for_todos(path, args.identifier)
        if path.is_file()
        else scan_directory(path, args.identifier)
    )
    payload = json.dumps(todos, indent=2)
    if args.output:
        Path(args.output).write_text(payload)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
