#!/usr/bin/env python3
"""Validate LLaVA-style VQA question and answer JSONL files.

The script checks row shape, duplicate ids, required keys, and optional image
folder existence without running any benchmark model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"line {line_no}: cannot parse JSONL: {exc}") from exc
    return rows


def check_rows(rows: Iterable[dict], mode: str, image_folder: Path | None) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str | int] = set()
    required = {
        "question": {"question_id", "text"},
        "answer": {"question_id", "text"},
        "answer-with-prompt": {"question_id", "prompt", "text"},
    }[mode]
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row {idx}: not an object")
            continue
        missing = required.difference(row)
        if missing:
            errors.append(f"row {idx}: missing {sorted(missing)}")
        qid = row.get("question_id")
        if qid in seen_ids:
            errors.append(f"row {idx}: duplicate question_id {qid!r}")
        seen_ids.add(qid)
        if image_folder is not None and "image" in row:
            image_path = image_folder / str(row["image"])
            if not image_path.exists():
                errors.append(f"row {idx}: missing image {image_path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LLaVA-style VQA JSONL files.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--mode", choices=["question", "answer", "answer-with-prompt"], default="question")
    parser.add_argument("--image-folder", type=Path)
    args = parser.parse_args()

    try:
        rows = load_jsonl(args.path)
    except Exception as exc:  # noqa: BLE001
        print(f"INVALID: {exc}")
        return 1

    errors = check_rows(rows, args.mode, args.image_folder)
    if errors:
        print("INVALID")
        for err in errors:
            print(err)
        return 1

    print(f"VALID: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
