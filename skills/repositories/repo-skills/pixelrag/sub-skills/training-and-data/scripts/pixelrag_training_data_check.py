#!/usr/bin/env python3
"""Validate a small PixelRAG training/synthetic-data JSONL sample.

This helper checks schema shape only. It does not download datasets, call APIs,
train models, or require PixelRAG imports.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def check_row(row: dict, line_no: int, root: Path | None, check_paths: bool) -> list[str]:
    errors: list[str] = []
    for key in ("query", "answer"):
        if not isinstance(row.get(key), str) or not row.get(key, "").strip():
            errors.append(f"line {line_no}: missing/non-empty string {key}")
    chunk = row.get("chunk_path")
    if chunk is not None:
        if not isinstance(chunk, str) or not chunk:
            errors.append(f"line {line_no}: chunk_path must be a non-empty string")
        elif check_paths and root is not None and not (root / chunk).exists() and not Path(chunk).exists():
            errors.append(f"line {line_no}: chunk_path not found: {chunk}")
    negs = row.get("neg_chunk_paths")
    if negs is not None:
        if not isinstance(negs, list) or not all(isinstance(x, str) for x in negs):
            errors.append(f"line {line_no}: neg_chunk_paths must be a list of strings")
        elif check_paths and root is not None:
            for p in negs[:10]:
                if not (root / p).exists() and not Path(p).exists():
                    errors.append(f"line {line_no}: negative path not found: {p}")
                    break
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--data-root", type=Path, help="root for relative image/chunk paths")
    parser.add_argument("--max-rows", type=int, default=1000)
    parser.add_argument("--no-check-paths", action="store_true", help="only validate field types")
    args = parser.parse_args()

    errors: list[str] = []
    rows = 0
    with args.jsonl.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if rows >= args.max_rows:
                break
            line = line.strip()
            if not line:
                continue
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            if not isinstance(row, dict):
                errors.append(f"line {line_no}: row is not an object")
                continue
            errors.extend(check_row(row, line_no, args.data_root, not args.no_check_paths))
    print(f"checked {rows} row(s)")
    if errors:
        for err in errors[:50]:
            print("ERROR", err)
        if len(errors) > 50:
            print(f"... {len(errors) - 50} more error(s)")
        return 2
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
