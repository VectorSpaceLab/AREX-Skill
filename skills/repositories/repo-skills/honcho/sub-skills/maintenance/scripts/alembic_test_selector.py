#!/usr/bin/env python3
"""Select Honcho Alembic pipeline tests for changed files.

This helper mirrors the repo maintenance rule: migration revision changes and
matching revision-test changes run the target revision pipeline with -k;
Alembic infrastructure changes run the full pipeline. By default it prints the
command. Pass --run to execute it.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def extract_revision_id(filepath: Path) -> str | None:
    """Extract a 12-hex Alembic revision id from a migration/test filename."""
    name = filepath.name
    if not name.endswith(".py"):
        return None
    stem = name[:-3]
    if stem.startswith("test_"):
        stem = stem[5:]
    match = re.match(r"^([a-f0-9]{12})_", stem)
    return match.group(1) if match else None


def _resolve_changed_file(root: Path, raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def select_command(root: Path, changed_files: list[str]) -> tuple[list[str] | None, list[str]]:
    """Return selected command and explanatory notes."""
    notes: list[str] = []
    if not changed_files:
        notes.append("No files supplied; no Alembic tests selected.")
        return None, notes

    root = root.resolve()
    migrations_dir = (root / "migrations" / "versions").resolve()
    tests_dir = (root / "tests" / "alembic" / "revisions").resolve()
    alembic_tests_dir = (root / "tests" / "alembic").resolve()

    revision_ids: set[str] = set()
    run_full_suite = False

    for raw in changed_files:
        filepath = _resolve_changed_file(root, raw)
        try:
            rel = filepath.relative_to(root)
        except ValueError:
            rel = filepath

        parent = filepath.parent
        is_under_alembic_tests = parent == alembic_tests_dir or alembic_tests_dir in parent.parents
        is_revision_test = parent == tests_dir and filepath.name.startswith("test_")

        if is_under_alembic_tests and not is_revision_test:
            run_full_suite = True
            notes.append(f"Alembic infrastructure changed: {rel} -> full pipeline")
            continue

        if is_revision_test:
            revision_id = extract_revision_id(filepath)
            if revision_id:
                revision_ids.add(revision_id)
                notes.append(f"Revision test changed: {rel} -> {revision_id}")
            else:
                notes.append(f"Revision test name has no 12-hex id: {rel}")
            continue

        if parent == migrations_dir:
            revision_id = extract_revision_id(filepath)
            if revision_id:
                revision_ids.add(revision_id)
                notes.append(f"Migration changed: {rel} -> {revision_id}")
            else:
                notes.append(f"Migration name has no 12-hex id: {rel}")

    if run_full_suite:
        return ["uv", "run", "pytest", "tests/alembic/test_pipeline.py", "-n0"], notes

    if revision_ids:
        expression = " or ".join(sorted(revision_ids))
        return [
            "uv",
            "run",
            "pytest",
            "tests/alembic/test_pipeline.py",
            "-n0",
            "-k",
            expression,
        ], notes

    notes.append("No Alembic migration/test pipeline files selected.")
    return None, notes


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "changed_files",
        nargs="*",
        help="Changed file paths, relative to the Honcho checkout root or absolute.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Honcho checkout root (default: current directory).",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the selected command instead of only printing it.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root).resolve()
    command, notes = select_command(root, args.changed_files)

    print(f"Honcho checkout root: {root}")
    for note in notes:
        print(f"- {note}")

    if command is None:
        return 0

    printable = " ".join(shlex.quote(part) for part in command)
    print(f"Selected command: {printable}")

    if args.run:
        result = subprocess.run(command, cwd=root)
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
