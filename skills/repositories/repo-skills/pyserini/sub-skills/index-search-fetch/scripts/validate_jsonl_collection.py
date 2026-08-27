#!/usr/bin/env python3
"""Validate Pyserini JsonCollection-style JSON/JSONL documents without running Java."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


TEXT_SUFFIXES = {".json", ".jsonl", ".txt"}


def iter_paths(paths: list[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and (child.suffix.lower() in TEXT_SUFFIXES or not child.suffix):
                    yield child
        else:
            yield path


def load_documents(path: Path, fmt: str) -> Iterable[tuple[int | None, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        if fmt == "jsonl":
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    yield line_number, json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        elif fmt == "json":
            try:
                data = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: invalid JSON: {exc.msg}") from exc
            if isinstance(data, list):
                for index, item in enumerate(data, start=1):
                    yield index, item
            else:
                yield None, data
        else:
            raise ValueError(f"unsupported format: {fmt}")


def infer_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if path.suffix.lower() == ".jsonl":
        return "jsonl"
    return "json"


def validate_doc(doc: Any, location: str, allow_empty_contents: bool) -> tuple[str, list[str]]:
    errors: list[str] = []
    if not isinstance(doc, dict):
        return "", [f"{location}: document must be a JSON object"]

    docid = doc.get("id")
    contents = doc.get("contents")

    if not isinstance(docid, str) or not docid:
        errors.append(f"{location}: field 'id' must be a non-empty string")
    if not isinstance(contents, str):
        errors.append(f"{location}: field 'contents' must be a string")
    elif not allow_empty_contents and not contents.strip():
        errors.append(f"{location}: field 'contents' must not be empty")

    return docid if isinstance(docid, str) else "", errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Pyserini JsonCollection JSON/JSONL files for id/contents shape."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="JSON/JSONL files or directories to validate. Directories are scanned recursively.",
    )
    parser.add_argument(
        "--format",
        choices=["auto", "jsonl", "json"],
        default="auto",
        help="Input format. auto treats .jsonl as JSONL and other files as JSON.",
    )
    parser.add_argument(
        "--require-unique-ids",
        action="store_true",
        help="Fail if the same document id appears more than once.",
    )
    parser.add_argument(
        "--allow-empty-contents",
        action="store_true",
        help="Allow documents whose contents field is an empty string.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Maximum number of validation errors to print before stopping early.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    seen: dict[str, str] = {}
    documents = 0
    files = 0

    for path in iter_paths(args.paths):
        files += 1
        if not path.exists():
            errors.append(f"{path}: path does not exist")
            continue
        fmt = infer_format(path, args.format)
        try:
            for line_number, doc in load_documents(path, fmt):
                documents += 1
                location = f"{path}:{line_number}" if line_number is not None else str(path)
                docid, doc_errors = validate_doc(doc, location, args.allow_empty_contents)
                errors.extend(doc_errors)
                if args.require_unique_ids and docid:
                    if docid in seen:
                        errors.append(f"{location}: duplicate id {docid!r}; first seen at {seen[docid]}")
                    else:
                        seen[docid] = location
                if len(errors) >= args.max_errors:
                    raise RuntimeError("too many validation errors")
        except (OSError, ValueError, RuntimeError) as exc:
            if str(exc) != "too many validation errors":
                errors.append(str(exc))
            if len(errors) >= args.max_errors:
                break

    if documents == 0 and not errors:
        errors.append("no documents found")

    if errors:
        print(f"Validation failed: {len(errors)} error(s)", file=sys.stderr)
        for error in errors[: args.max_errors]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > args.max_errors:
            print(f"- ... {len(errors) - args.max_errors} more", file=sys.stderr)
        return 1

    unique_suffix = f", {len(seen)} unique ids" if args.require_unique_ids else ""
    print(f"OK: {documents} document(s) across {files} file(s){unique_suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
