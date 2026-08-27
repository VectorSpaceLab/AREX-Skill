#!/usr/bin/env python3
"""Validate Tencent ML-Images URL lists, image lists, and dictionaries.

This helper is safe by default: it reads text files and optionally checks local
image path existence. It does not download, decode, train, or write TFRecords.

Examples:
  python validate_ml_images_lists.py --url-list train_urls_tiny.txt --num-classes 11166
  python validate_ml_images_lists.py --image-list train_im_list_tiny.txt --images-root images
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

LABEL_RE = re.compile(r"^(?P<class_id>\d+)(?::(?P<confidence>[+-]?(?:\d+(?:\.\d*)?|\.\d+)))?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url-list", type=Path, help="Rows of URL plus label tokens.")
    parser.add_argument("--image-list", type=Path, help="Rows of local image path plus label tokens.")
    parser.add_argument("--dictionary", type=Path, help="Class dictionary or semantic hierarchy file to sanity-check.")
    parser.add_argument("--num-classes", type=int, default=11166, help="Exclusive upper bound for zero-based class ids.")
    parser.add_argument("--images-root", type=Path, help="Optional root used to verify image-list files exist.")
    parser.add_argument("--allow-missing-images", action="store_true", help="Report missing image files as warnings instead of errors.")
    parser.add_argument("--max-rows", type=int, default=0, help="Maximum rows to inspect per list file; 0 means all rows.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary only.")
    return parser.parse_args()


def iter_rows(path: Path, max_rows: int) -> Iterable[Tuple[int, str]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for idx, raw in enumerate(handle, start=1):
            if max_rows and idx > max_rows:
                break
            line = raw.rstrip("\n")
            if line.strip():
                yield idx, line


def split_row(line: str) -> List[str]:
    if "\t" in line:
        return [part for part in line.split("\t") if part != ""]
    return line.split()


def check_label(token: str, num_classes: int) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    match = LABEL_RE.match(token)
    if not match:
        return [f"invalid label token {token!r}; expected id or id:confidence"], warnings
    class_id = int(match.group("class_id"))
    if class_id >= num_classes:
        errors.append(f"class id {class_id} out of range for num_classes={num_classes}")
    if match.group("confidence") is not None:
        confidence = float(match.group("confidence"))
        if not (0.0 <= confidence <= 1.0):
            warnings.append(f"confidence {confidence} outside [0, 1] in token {token!r}")
    return errors, warnings


def check_list(path: Path, kind: str, args: argparse.Namespace) -> dict:
    result = {"path": str(path), "kind": kind, "rows": 0, "errors": [], "warnings": [], "first_fields": []}
    seen = Counter()
    if not path.exists():
        result["errors"].append(f"file does not exist: {path}")
        return result
    for lineno, line in iter_rows(path, args.max_rows):
        result["rows"] += 1
        parts = split_row(line)
        if len(parts) < 2:
            result["errors"].append(f"line {lineno}: expected first field plus at least one label token")
            continue
        first = parts[0]
        result["first_fields"].append(first)
        seen[first] += 1
        if kind == "url" and not re.match(r"^https?://", first):
            result["warnings"].append(f"line {lineno}: first field does not look like http(s) URL: {first}")
        if kind == "image" and args.images_root:
            image_path = args.images_root / first
            if not image_path.exists():
                msg = f"line {lineno}: missing image file {image_path}"
                (result["warnings"] if args.allow_missing_images else result["errors"]).append(msg)
        for token in parts[1:]:
            errs, warns = check_label(token, args.num_classes)
            result["errors"].extend(f"line {lineno}: {msg}" for msg in errs)
            result["warnings"].extend(f"line {lineno}: {msg}" for msg in warns)
    duplicates = [name for name, count in seen.items() if count > 1]
    if duplicates:
        result["warnings"].append(f"duplicate first fields: {duplicates[:10]}{' ...' if len(duplicates) > 10 else ''}")
    result["unique_first_fields"] = len(seen)
    result.pop("first_fields", None)
    return result


def check_dictionary(path: Path, num_classes: int) -> dict:
    result = {"path": str(path), "kind": "dictionary", "rows": 0, "errors": [], "warnings": []}
    if not path.exists():
        result["errors"].append(f"file does not exist: {path}")
        return result
    ids = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            # Allow semantic hierarchy header.
            if lineno == 1 and parts[0] in {"category_index", "index"}:
                continue
            try:
                ids.append(int(parts[0]))
            except ValueError:
                result["warnings"].append(f"line {lineno}: first field is not an integer id: {parts[0]!r}")
                continue
            result["rows"] += 1
            if len(parts) < 2:
                result["warnings"].append(f"line {lineno}: dictionary row has fewer than two tab-separated fields")
    if ids:
        if min(ids) != 0:
            result["warnings"].append(f"minimum id is {min(ids)}, expected zero-based ids")
        if max(ids) >= num_classes:
            result["errors"].append(f"maximum id {max(ids)} out of range for num_classes={num_classes}")
        if len(set(ids)) != len(ids):
            result["warnings"].append("duplicate dictionary ids detected")
    if result["rows"] and result["rows"] < num_classes:
        result["warnings"].append(f"dictionary has {result['rows']} rows, fewer than num_classes={num_classes}")
    return result


def main() -> int:
    args = parse_args()
    reports = []
    if args.url_list:
        reports.append(check_list(args.url_list, "url", args))
    if args.image_list:
        reports.append(check_list(args.image_list, "image", args))
    if args.dictionary:
        reports.append(check_dictionary(args.dictionary, args.num_classes))
    if not reports:
        print("No input files supplied; pass --url-list, --image-list, or --dictionary.", file=sys.stderr)
        return 2
    totals = {
        "files": len(reports),
        "rows": sum(r.get("rows", 0) for r in reports),
        "errors": sum(len(r.get("errors", [])) for r in reports),
        "warnings": sum(len(r.get("warnings", [])) for r in reports),
        "reports": reports,
    }
    if args.json:
        print(json.dumps(totals, indent=2, sort_keys=True))
    else:
        print(json.dumps({k: v for k, v in totals.items() if k != "reports"}, indent=2, sort_keys=True))
        for report in reports:
            print(f"\n[{report['kind']}] {report['path']} rows={report.get('rows', 0)}")
            for msg in report.get("warnings", [])[:20]:
                print(f"  WARNING: {msg}")
            for msg in report.get("errors", [])[:20]:
                print(f"  ERROR: {msg}")
    return 1 if totals["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
