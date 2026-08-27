#!/usr/bin/env python3
"""Validate planned SimpleDirectoryReader inputs without reading file contents."""

from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path
from typing import Iterable


def normalize_ext(value: str) -> str:
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("extension cannot be empty")
    return value if value.startswith(".") else f".{value}"


def is_hidden(path: Path) -> bool:
    return any(part.startswith(".") and part not in {".", ".."} for part in path.parts)


def matches_any(path: Path, root: Path, patterns: Iterable[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path.name, pattern) for pattern in patterns)


def iter_files(root: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        for current, _, files in os.walk(root):
            for filename in files:
                yield Path(current) / filename
    else:
        for child in root.iterdir():
            if child.is_file():
                yield child


def reader_arg_lines(args: argparse.Namespace, matched: list[Path]) -> list[str]:
    lines = ["SimpleDirectoryReader("]
    if args.input_file:
        files = ", ".join(repr(str(Path(p))) for p in args.input_file)
        lines.append(f"    input_files=[{files}],")
    else:
        lines.append(f"    input_dir={str(args.path)!r},")
        if args.recursive:
            lines.append("    recursive=True,")
        if args.exclude:
            lines.append(f"    exclude={args.exclude!r},")
        if args.include_hidden:
            lines.append("    exclude_hidden=False,")
        if args.exclude_empty:
            lines.append("    exclude_empty=True,")
        if args.required_ext:
            lines.append(f"    required_exts={args.required_ext!r},")
    if args.filename_as_id:
        lines.append("    filename_as_id=True,")
    if args.raise_on_error:
        lines.append("    raise_on_error=True,")
    if args.encoding != "utf-8":
        lines.append(f"    encoding={args.encoding!r},")
    if args.errors != "ignore":
        lines.append(f"    errors={args.errors!r},")
    lines.append(").load_data()")
    if not matched:
        lines.append("# Warning: this configuration matched no files.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a local directory or file list and print likely SimpleDirectoryReader arguments. Does not import LlamaIndex or read file contents.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Directory to inspect when --input-file is not used.")
    parser.add_argument("--input-file", action="append", help="Explicit file path to include. May be repeated; bypasses directory filtering like SimpleDirectoryReader input_files.")
    parser.add_argument("--required-ext", action="append", type=normalize_ext, help="Required extension such as .md or pdf. May be repeated.")
    parser.add_argument("--exclude", action="append", default=[], help="Glob pattern to exclude during directory discovery. May be repeated.")
    parser.add_argument("--recursive", action="store_true", help="Walk subdirectories.")
    parser.add_argument("--include-hidden", action="store_true", help="Include dotfiles and files under dot-directories.")
    parser.add_argument("--exclude-empty", action="store_true", help="Skip zero-byte files.")
    parser.add_argument("--filename-as-id", action="store_true", help="Suggest filename_as_id=True.")
    parser.add_argument("--encoding", default="utf-8", help="Suggested text encoding. Default: utf-8.")
    parser.add_argument("--errors", default="ignore", help="Suggested decode error policy. Default: ignore.")
    parser.add_argument("--raise-on-error", action="store_true", help="Suggest raise_on_error=True.")
    args = parser.parse_args()

    skipped = {"hidden": [], "empty": [], "extension": [], "excluded": [], "missing": []}
    matched: list[Path] = []

    if args.input_file:
        for raw in args.input_file:
            path = Path(raw)
            if path.is_file():
                matched.append(path)
            else:
                skipped["missing"].append(path)
    else:
        root = Path(args.path)
        if not root.is_dir():
            print(f"ERROR: directory does not exist: {root}")
            return 2
        for path in iter_files(root, args.recursive):
            if not args.include_hidden and is_hidden(path.relative_to(root)):
                skipped["hidden"].append(path)
                continue
            if args.exclude_empty and path.stat().st_size == 0:
                skipped["empty"].append(path)
                continue
            if args.required_ext and path.suffix not in args.required_ext:
                skipped["extension"].append(path)
                continue
            if args.exclude and matches_any(path, root, args.exclude):
                skipped["excluded"].append(path)
                continue
            matched.append(path)

    print("Matched files:", len(matched))
    for reason, paths in skipped.items():
        if paths:
            print(f"Skipped {reason}:", len(paths))
    if matched[:10]:
        print("\nFirst matches:")
        for path in matched[:10]:
            print(f"- {path}")
        if len(matched) > 10:
            print(f"- ... {len(matched) - 10} more")

    print("\nSuggested reader call:")
    for line in reader_arg_lines(args, matched):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
