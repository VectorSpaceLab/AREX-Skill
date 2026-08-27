#!/usr/bin/env python3
"""Validate a RAGs builder data-source selection without loading data.

RAGs accepts exactly one source kind for a build: one or more local files, one
local directory, or one or more URLs. This helper performs structural checks and
prints a JSON summary. It never downloads URLs or calls external LLM services.

Examples:
  python validate_source_selection.py --file notes.md --file paper.txt
  python validate_source_selection.py --directory ./docs
  python validate_source_selection.py --url https://example.com/page
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def _flatten(values: list[list[str]] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for group in values:
        out.extend(group)
    return out


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that a RAGs build uses exactly one data-source kind: "
            "files, a directory, or URLs."
        )
    )
    parser.add_argument(
        "--file",
        dest="files",
        nargs="+",
        action="append",
        metavar="PATH",
        help="Local file path(s). Repeat --file or pass multiple paths after it.",
    )
    parser.add_argument(
        "--directory",
        metavar="PATH",
        help="One local directory to load.",
    )
    parser.add_argument(
        "--url",
        dest="urls",
        nargs="+",
        action="append",
        metavar="URL",
        help="HTTP(S) URL(s). The helper validates syntax only and does not fetch.",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for the JSON summary. Use 0 for compact output.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    files = _flatten(args.files)
    urls = _flatten(args.urls)
    source_kinds = [bool(files), bool(args.directory), bool(urls)]

    if sum(source_kinds) == 0:
        parser.error("specify exactly one of --file, --directory, or --url")
    if sum(source_kinds) > 1:
        parser.error("RAGs load_data accepts only one source kind per build")

    summary: dict[str, object] = {"status": "ok"}

    if files:
        checked = []
        for value in files:
            path = Path(value).expanduser()
            if not path.exists():
                parser.error(f"file does not exist: {value}")
            if not path.is_file():
                parser.error(f"not a file: {value}")
            checked.append({"path": value, "size_bytes": path.stat().st_size})
        summary.update({"source_kind": "file_names", "files": checked})
    elif args.directory:
        path = Path(args.directory).expanduser()
        if not path.exists():
            parser.error(f"directory does not exist: {args.directory}")
        if not path.is_dir():
            parser.error(f"not a directory: {args.directory}")
        summary.update({"source_kind": "directory", "directory": args.directory})
    else:
        invalid = [url for url in urls if not _valid_url(url)]
        if invalid:
            parser.error("invalid URL(s): " + ", ".join(invalid))
        summary.update(
            {
                "source_kind": "urls",
                "urls": urls,
                "network_not_checked": True,
            }
        )

    indent = None if args.json_indent == 0 else args.json_indent
    print(json.dumps(summary, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
