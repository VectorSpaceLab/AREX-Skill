#!/usr/bin/env python3
"""Scan public text for local machine identity patterns.

The scanner intentionally reports only a generic blocked message for matches.
It does not print file names, matched text, line numbers, usernames, hostnames,
or paths.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

BLOCKED = "Blocked: local machine identity was found in public text."
OK = "No local machine identity patterns found."

PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(?:^|[\s'\"(=])/(?:home|users|root)/[^\s'\")<>]+"),
    re.compile(r"(?i)(?:^|[\s'\"(=])[a-z]:[\\/]+users[\\/]+[^\s'\")<>]+"),
    re.compile(r"(?i)(?:^|[\s'\"(=])/(?:tmp|var/tmp|private/var/folders)(?:/[^\s'\")<>]*)?"),
    re.compile(r"(?i)(?:^|[\s'\"(=])~/(?:\.cache|\.conda|\.local|\.venv|\.virtualenvs|tmp|temp)(?:/[^\s'\")<>]*)?"),
    re.compile(r"(?i)[\\/](?:appdata[\\/]local[\\/]temp|pip[\\/]cache|cache[\\/]pip)[\\/][^\s'\")<>]+"),
    re.compile(r"(?im)^\s*(?:co-authored-by|reviewed-by|signed-off-by|acked-by|thanks-to)\s*:\s*.+$"),
    re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9._-]+:(?:~|/|[a-z]:[\\/])"),
    re.compile(r"(?im)^\s*[a-z0-9._-]+@[a-z0-9._-]+\s+[^\r\n]+$"),
)

TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
}


def has_private_identity(text: str) -> bool:
    return any(pattern.search(text) for pattern in PATTERNS)


def iter_file_text(paths: Iterable[str], recursive: bool) -> Iterable[str]:
    for raw_path in paths:
        if raw_path == "-":
            yield sys.stdin.read()
            continue
        path = Path(raw_path)
        candidates: list[Path]
        if path.is_dir():
            if not recursive:
                continue
            candidates = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES]
        else:
            candidates = [path]
        for candidate in candidates:
            try:
                yield candidate.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                yield ""


def scan(paths: list[str], recursive: bool) -> bool:
    return any(has_private_identity(text) for text in iter_file_text(paths, recursive))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Block public text containing local absolute paths, home usernames, temp/cache paths, host prompts, or attribution trailers.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Text files to scan. Use '-' or omit paths to read stdin. Directories are scanned only with --recursive.",
    )
    parser.add_argument("--recursive", action="store_true", help="Recursively scan text-like files under directory inputs.")
    parser.add_argument("--json", action="store_true", help="Emit only a generic JSON result; never includes match details.")
    parser.add_argument("--quiet", action="store_true", help="Print nothing when no issue is found.")
    args = parser.parse_args(argv)

    paths = args.paths or ["-"]
    blocked = scan(paths, args.recursive)
    if args.json:
        print(json.dumps({"ok": not blocked, "message": BLOCKED if blocked else OK}, sort_keys=True))
    elif blocked:
        print(BLOCKED)
    elif not args.quiet:
        print(OK)
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
