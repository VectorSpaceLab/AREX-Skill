#!/usr/bin/env python3
"""Validate whitespace-delimited agricultural label files.

The expected line format is:

    <term> <label>

where <label> is an integer from 0 to 16.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


VALID_LABELS = set(range(17))


def parse_label_lines(lines: Iterable[str]) -> dict:
    total = 0
    blank = 0
    counts = Counter()
    terms = set()
    duplicates = []
    errors = []

    for lineno, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            blank += 1
            errors.append({"line": lineno, "error": "blank line"})
            continue
        total += 1
        parts = line.split()
        if len(parts) != 2:
            errors.append({"line": lineno, "error": "expected exactly 2 whitespace-separated fields", "value": line})
            continue
        term, label_text = parts
        try:
            label = int(label_text)
        except ValueError:
            errors.append({"line": lineno, "error": "label is not an integer", "value": line})
            continue
        if label not in VALID_LABELS:
            errors.append({"line": lineno, "error": "label out of range 0-16", "value": line})
            continue
        counts[label] += 1
        if term in terms:
            duplicates.append(term)
        else:
            terms.add(term)

    return {
        "ok": not errors,
        "total_lines": total,
        "blank_lines": blank,
        "label_counts": dict(sorted(counts.items())),
        "duplicate_terms": sorted(set(duplicates)),
        "errors": errors,
    }


def parse_label_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return parse_label_lines(fh)


def build_demo_lines() -> List[str]:
    return [
        "苹果 6\n",
        "北京 2\n",
        "葡萄蔓枯病 10\n",
        "收割机 14\n",
    ]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate whitespace-delimited label files with integer labels 0-16.",
    )
    parser.add_argument("paths", nargs="*", help="Label files to validate.")
    parser.add_argument("--demo", action="store_true", help="Validate a tiny built-in fixture instead of files.")
    parser.add_argument(
        "--fail-on-duplicate",
        action="store_true",
        help="Treat duplicate terms as an error.",
    )
    args = parser.parse_args(argv)

    if args.demo and args.paths:
        parser.error("--demo cannot be combined with file paths")

    if args.demo or not args.paths:
        result = parse_label_lines(build_demo_lines())
        if args.fail_on_duplicate and result["duplicate_terms"]:
            result["ok"] = False
            result["errors"].append({"error": "duplicate terms found", "value": result["duplicate_terms"]})
        print(json.dumps({"mode": "demo", **result}, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if result["ok"] else 1

    overall_ok = True
    summary = []
    for raw_path in args.paths:
        path = Path(raw_path)
        result = parse_label_file(path)
        if args.fail_on_duplicate and result["duplicate_terms"]:
            result["ok"] = False
            result["errors"].append({"error": "duplicate terms found", "value": result["duplicate_terms"]})
        result["path"] = str(path)
        summary.append(result)
        overall_ok = overall_ok and result["ok"]

    print(json.dumps({"mode": "files", "results": summary}, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
