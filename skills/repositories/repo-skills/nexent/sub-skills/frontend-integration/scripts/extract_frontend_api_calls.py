#!/usr/bin/env python3
"""Extract Nexent frontend API endpoint call sites.

This helper performs a deterministic, static scan of frontend TypeScript files
and reports every `API_ENDPOINTS.*` reference it can find. It is intentionally
read-only and does not require a running backend or Node.js runtime.

Typical usage:
  python scripts/extract_frontend_api_calls.py --repo-root .
  python scripts/extract_frontend_api_calls.py --repo-root . --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

SCAN_ROOTS = (
    "frontend/services",
    "frontend/app/[locale]/chat",
    "frontend/app/[locale]/newchat",
    "frontend/features",
    "frontend/hooks",
    "frontend/lib/chat",
    "frontend/components",
)

VALID_SUFFIXES = {".ts", ".tsx"}
EXCLUDED_PARTS = {"node_modules", ".next", "dist", "coverage", "public"}
ENDPOINT_RE = re.compile(
    r"API_ENDPOINTS\.([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static frontend service endpoint extractor for Nexent.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the Nexent repository root (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary.",
    )
    return parser.parse_args(argv)


def path_has_excluded_part(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def iter_source_files(repo_root: Path) -> Iterable[Path]:
    for relative_root in SCAN_ROOTS:
        root = repo_root / relative_root
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in VALID_SUFFIXES:
                continue
            if path_has_excluded_part(path):
                continue
            yield path


def collect_matches(path: Path, repo_root: Path) -> list[dict[str, object]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [
            {
                "file": str(path.relative_to(repo_root)),
                "line": 0,
                "reference": f"<read-error: {exc}>",
                "family": "<read-error>",
                "subpath": "",
            }
        ]

    matches: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in ENDPOINT_RE.finditer(line):
            reference = match.group(1)
            family, *rest = reference.split(".")
            matches.append(
                {
                    "file": str(path.relative_to(repo_root)),
                    "line": line_no,
                    "reference": f"API_ENDPOINTS.{reference}",
                    "family": family,
                    "subpath": ".".join(rest),
                }
            )
    return matches


def summarize(matches: list[dict[str, object]]) -> dict[str, object]:
    by_family: dict[str, set[str]] = defaultdict(set)
    by_file: dict[str, set[str]] = defaultdict(set)

    for match in matches:
        family = str(match["family"])
        file_name = str(match["file"])
        reference = str(match["reference"])
        if family.startswith("<read-error>"):
            continue
        by_family[family].add(reference)
        by_file[file_name].add(reference)

    family_summary = {
        family: {
            "count": len(refs),
            "references": sorted(refs),
        }
        for family, refs in sorted(by_family.items())
    }
    file_summary = {
        file_name: {
            "count": len(refs),
            "references": sorted(refs),
        }
        for file_name, refs in sorted(by_file.items())
    }
    return {
        "family_summary": family_summary,
        "file_summary": file_summary,
    }


def print_text_report(repo_root: Path, files: list[Path], matches: list[dict[str, object]]) -> None:
    summary = summarize(matches)
    family_summary = summary["family_summary"]
    file_summary = summary["file_summary"]

    print(f"Repo root: {repo_root}")
    print(f"Files scanned: {len(files)}")
    print(f"Endpoint references found: {len(matches)}")
    print(f"Endpoint families found: {len(family_summary)}")
    print()
    print("By family:")
    for family, info in family_summary.items():
        print(f"- {family}: {info['count']} references")
        for ref in info["references"]:
            print(f"  - {ref}")
    print()
    print("By file:")
    for file_name, info in file_summary.items():
        print(f"- {file_name}: {info['count']} references")
        for ref in info["references"]:
            print(f"  - {ref}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    frontend_root = repo_root / "frontend"

    if not repo_root.exists():
        print(f"error: repo root does not exist: {repo_root}", file=sys.stderr)
        return 2
    if not frontend_root.exists():
        print(f"error: frontend directory not found under {repo_root}", file=sys.stderr)
        return 2

    files = sorted({path for path in iter_source_files(repo_root)})
    matches: list[dict[str, object]] = []
    for path in files:
        matches.extend(collect_matches(path, repo_root))

    # Stable sort for reproducible output.
    matches.sort(
        key=lambda item: (
            str(item["file"]),
            int(item["line"]),
            str(item["reference"]),
        )
    )

    if args.json:
        payload = {
            "schema": "disco.nexent.frontend_api_calls.v1",
            "repo_root": str(repo_root),
            "frontend_root": str(frontend_root),
            "scan_roots": list(SCAN_ROOTS),
            "files_scanned": len(files),
            "endpoint_references": matches,
            **summarize(matches),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text_report(repo_root, files, matches)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
