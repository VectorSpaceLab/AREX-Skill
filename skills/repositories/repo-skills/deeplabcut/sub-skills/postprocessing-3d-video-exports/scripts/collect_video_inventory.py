#!/usr/bin/env python3
"""Safely inventory candidate video files without modifying anything.

The script scans the supplied files or directories, applies optional extension and
exclusion filters, and prints a JSON report to stdout.

Directory scans are one level deep, mirroring the package's safe video-collection
style. No files are created, renamed, copied, or deleted.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

SUPPORTED_VIDEO_EXTENSIONS = (".avi", ".mp4", ".mov", ".mpeg", ".mpg", ".mpv", ".mkv", ".flv", ".qt", ".yuv")
DEFAULT_EXCLUDE_PATTERNS = ("*_labeled.*", "*_full.*")


def normalize_extensions(raw_extensions: list[str] | None) -> set[str] | None:
    if raw_extensions is None:
        return None

    normalized: set[str] = set()
    for item in raw_extensions:
        for chunk in str(item).split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            normalized.add("." + chunk.lstrip(".").lower())

    return normalized or None


def parse_patterns(values: list[str] | None) -> list[str]:
    if values is None:
        return list(DEFAULT_EXCLUDE_PATTERNS)

    patterns: list[str] = []
    for item in values:
        for chunk in str(item).split(","):
            chunk = chunk.strip()
            if chunk:
                patterns.append(chunk)
    return patterns


def matches_any(path: Path, patterns: Iterable[str]) -> str | None:
    target = path.as_posix()
    for pattern in patterns:
        if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(target, pattern):
            return pattern
    return None


def iter_directory_candidates(folder: Path) -> Iterable[Path]:
    for child in sorted(folder.iterdir()):
        if child.is_file():
            yield child


def inventory(paths: list[str], extensions: list[str] | None, exclude_patterns: list[str] | None, no_excludes: bool) -> dict:
    explicit_suffixes = normalize_extensions(extensions)
    exclude_patterns = [] if no_excludes else parse_patterns(exclude_patterns)
    implicit_suffixes = {suffix.lower() for suffix in SUPPORTED_VIDEO_EXTENSIONS}

    matched: list[str] = []
    excluded: list[dict[str, object]] = []
    missing: list[str] = []
    scanned_directories: list[str] = []
    input_records: list[dict[str, object]] = []
    seen: set[str] = set()
    duplicate_hits = 0

    for raw in paths:
        source = Path(raw).expanduser()
        if not source.exists():
            missing.append(str(source))
            input_records.append({"path": str(source), "kind": "missing"})
            continue

        if source.is_dir():
            scanned_directories.append(str(source))
            input_records.append({"path": str(source), "kind": "directory"})
            allowed = explicit_suffixes if explicit_suffixes is not None else implicit_suffixes
            for candidate in iter_directory_candidates(source):
                if candidate.suffix.lower() not in allowed:
                    excluded.append(
                        {
                            "path": str(candidate),
                            "reason": "extension",
                            "allowed_extensions": sorted(allowed),
                        }
                    )
                    continue
                pattern = matches_any(candidate, exclude_patterns)
                if pattern is not None:
                    excluded.append({"path": str(candidate), "reason": "pattern", "pattern": pattern})
                    continue
                resolved = str(candidate.resolve())
                if resolved not in seen:
                    matched.append(resolved)
                    seen.add(resolved)
                else:
                    duplicate_hits += 1
        else:
            input_records.append({"path": str(source), "kind": "file"})
            if explicit_suffixes is not None and source.suffix.lower() not in explicit_suffixes:
                excluded.append(
                    {
                        "path": str(source),
                        "reason": "extension",
                        "allowed_extensions": sorted(explicit_suffixes),
                    }
                )
                continue
            pattern = matches_any(source, exclude_patterns)
            if pattern is not None:
                excluded.append({"path": str(source), "reason": "pattern", "pattern": pattern})
                continue
            resolved = str(source.resolve())
            if resolved not in seen:
                matched.append(resolved)
                seen.add(resolved)
            else:
                duplicate_hits += 1

    matched.sort()

    by_extension = Counter()
    suffixless = 0
    for item in matched:
        suffix = Path(item).suffix.lower()
        if suffix:
            by_extension[suffix.lstrip(".")] += 1
        else:
            suffixless += 1

    summary = {
        "inputs": len(paths),
        "missing": len(missing),
        "directories_scanned": len(scanned_directories),
        "matched": len(matched),
        "excluded": len(excluded),
        "suffixless_matched": suffixless,
        "duplicates_removed": duplicate_hits,
    }

    return {
        "inputs": input_records,
        "extensions": sorted(explicit_suffixes) if explicit_suffixes is not None else None,
        "exclude_patterns": exclude_patterns,
        "supported_extensions": [suffix.lstrip(".") for suffix in SUPPORTED_VIDEO_EXTENSIONS],
        "summary": summary,
        "matched_files": matched,
        "excluded": excluded,
        "missing_paths": missing,
        "directories_scanned": scanned_directories,
        "by_extension": dict(sorted(by_extension.items())),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory candidate video files and report extension/exclusion decisions as JSON.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Files or directories to inventory.",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        help="Optional extension filter, e.g. mp4 avi. Omit to keep directory defaults.",
    )
    parser.add_argument(
        "--exclude-patterns",
        nargs="+",
        default=None,
        help="Optional glob patterns to exclude, e.g. '*_labeled.*' '*_full.*'.",
    )
    parser.add_argument(
        "--no-excludes",
        action="store_true",
        help="Disable all exclusion patterns.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level. Defaults to 2.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    report = inventory(args.paths, args.extensions, args.exclude_patterns, args.no_excludes)
    json.dump(report, fp=sys.stdout, indent=args.indent, sort_keys=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
