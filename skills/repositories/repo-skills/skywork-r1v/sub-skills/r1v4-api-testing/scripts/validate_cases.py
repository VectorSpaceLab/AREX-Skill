#!/usr/bin/env python3
"""Validate R1V4 JSONL test cases and optional image paths."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def _normalize_image_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    raise TypeError("image must be a string or an empty string")


def _candidate_image_paths(
    image: str,
    input_file: Optional[str],
    cwd: str,
) -> List[Path]:
    if not image or image.startswith("data:"):
        return []

    image_path = Path(image).expanduser()
    candidates: List[Path] = []

    if image_path.is_absolute():
        candidates.append(image_path)
        return candidates

    if input_file:
        candidates.append(Path(input_file).expanduser().resolve().parent / image_path)
    candidates.append(Path(cwd).expanduser() / image_path)

    deduped: List[Path] = []
    seen = set()
    for candidate in candidates:
        normalized = str(candidate.resolve())
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(candidate)
    return deduped


def validate_record(
    record: Any,
    line_num: int,
    input_file: Optional[str] = None,
    check_images: bool = False,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    cwd = cwd or os.getcwd()
    result: Dict[str, Any] = {
        "line_num": line_num,
        "valid": True,
        "issues": [],
    }

    if not isinstance(record, dict):
        result["valid"] = False
        result["issues"].append("record must be a JSON object")
        result["raw_record"] = record
        return result

    question = record.get("question")
    image_value = record.get("image", "")

    if not isinstance(question, str):
        result["valid"] = False
        result["issues"].append("question must be a string")
    elif not question.strip():
        result["valid"] = False
        result["issues"].append("question must not be empty")

    try:
        image = _normalize_image_field(image_value)
    except TypeError as exc:
        result["valid"] = False
        result["issues"].append(str(exc))
        image = ""

    if "image" in record and image_value is None:
        result["valid"] = False
        result["issues"].append("image must be a string or empty")

    if check_images and image and not image.startswith("data:"):
        candidates = _candidate_image_paths(image, input_file, cwd)
        resolved = None
        for candidate in candidates:
            if candidate.exists():
                resolved = str(candidate)
                break
        if resolved:
            result["resolved_image"] = resolved
        else:
            result["valid"] = False
            result["issues"].append(
                "image not found; tried: "
                + ", ".join(str(candidate) for candidate in candidates)
            )

    result["image"] = image
    result["question"] = question if isinstance(question, str) else None
    return result


def validate_file(
    input_file: str,
    check_images: bool = False,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    cwd = cwd or os.getcwd()
    records: List[Dict[str, Any]] = []
    total = 0
    valid = 0

    with open(input_file, "r", encoding="utf-8") as handle:
        for line_num, line in enumerate(handle, 1):
            if not line.strip():
                continue
            total += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                validation = {
                    "line_num": line_num,
                    "valid": False,
                    "issues": [f"invalid JSON: {exc}"],
                    "raw_line": line.rstrip("\n"),
                }
            else:
                validation = validate_record(
                    record,
                    line_num=line_num,
                    input_file=input_file,
                    check_images=check_images,
                    cwd=cwd,
                )
            if validation["valid"]:
                valid += 1
            records.append(validation)

    return {
        "input_file": input_file,
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "check_images": check_images,
        "records": records,
    }


def _print_human(summary: Dict[str, Any]) -> None:
    print(f"Input file: {summary['input_file']}")
    print(f"Total records: {summary['total']}")
    print(f"Valid records: {summary['valid']}")
    print(f"Invalid records: {summary['invalid']}")
    print(f"Image checks: {'on' if summary['check_images'] else 'off'}")
    for record in summary["records"]:
        if record["valid"]:
            continue
        issues = "; ".join(record["issues"])
        print(f"- line {record['line_num']}: {issues}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate R1V4 JSONL test cases and optional image paths.",
    )
    parser.add_argument("--input", required=True, help="Path to test_cases.jsonl")
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Check that each non-empty image path exists relative to the input file or current directory.",
    )
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Override the current working directory used for relative image lookup.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the validation summary as JSON.",
    )
    args = parser.parse_args()

    summary = validate_file(args.input, check_images=args.check_images, cwd=args.cwd)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_human(summary)

    return 0 if summary["invalid"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
