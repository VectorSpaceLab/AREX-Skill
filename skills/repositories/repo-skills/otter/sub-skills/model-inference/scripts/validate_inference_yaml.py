#!/usr/bin/env python3
"""Validate an Otter/OtterHD YAML batch inference file without loading models.

The accepted schema is a top-level YAML list. Each item must be a mapping with
at least a non-empty string `question`. `image_path` is optional; blank or
omitted means no-image mode. Optional metadata fields such as `id`, `answer`,
and `expected_answer` are allowed by default for user-side evaluation.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - depends on caller env
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None

ALLOWED_FIELDS = {"id", "question", "image_path", "answer", "expected_answer"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely validate an Otter-style YAML batch inference file. No model or media downloads are performed.",
    )
    parser.add_argument("yaml_file", type=Path, help="YAML file to validate.")
    parser.add_argument(
        "--require-image",
        action="store_true",
        help="Require every row to contain a non-empty image_path instead of allowing no-image prompts.",
    )
    parser.add_argument(
        "--check-local-images",
        action="store_true",
        help="For non-empty local image_path values, verify that the file exists and has an image-like MIME type. URLs are not fetched.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Report fields outside id/question/image_path/answer/expected_answer as errors instead of warnings.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Fail when the YAML contains more than this many rows.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of text.",
    )
    return parser.parse_args()


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def image_like(path_text: str) -> bool:
    mime, _ = mimetypes.guess_type(path_text)
    return bool(mime and mime.startswith("image/"))


def add(report: dict[str, Any], level: str, message: str, row: int | None = None) -> None:
    entry: dict[str, Any] = {"level": level, "message": message}
    if row is not None:
        entry["row"] = row
    report[level + "s"].append(entry)


def validate(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "file": str(args.yaml_file),
        "valid": False,
        "rows": 0,
        "errors": [],
        "warnings": [],
    }

    if yaml is None:
        add(report, "error", f"PyYAML is required to read YAML: {YAML_IMPORT_ERROR}")
        return report

    if not args.yaml_file.exists():
        add(report, "error", "YAML file does not exist")
        return report
    if not args.yaml_file.is_file():
        add(report, "error", "YAML path is not a file")
        return report

    try:
        with args.yaml_file.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        add(report, "error", f"Could not parse YAML: {exc}")
        return report

    if not isinstance(data, list):
        add(report, "error", "Top-level YAML value must be a list of inference rows")
        return report

    report["rows"] = len(data)
    if args.max_items is not None and len(data) > args.max_items:
        add(report, "error", f"YAML contains {len(data)} rows, exceeding --max-items {args.max_items}")

    base_dir = args.yaml_file.resolve().parent
    for idx, item in enumerate(data):
        row = idx
        if not isinstance(item, dict):
            add(report, "error", "Row must be a mapping/object", row)
            continue

        extra = sorted(set(item.keys()) - ALLOWED_FIELDS)
        if extra:
            level = "error" if args.strict else "warning"
            add(report, level, "Unexpected field(s): " + ", ".join(extra), row)

        question = item.get("question")
        if not isinstance(question, str) or not question.strip():
            add(report, "error", "Row requires a non-empty string question", row)

        image_path = item.get("image_path", "")
        if image_path is None:
            image_path = ""
        if not isinstance(image_path, str):
            add(report, "error", "image_path must be a string when provided", row)
            continue

        image_path_stripped = image_path.strip()
        if args.require_image and not image_path_stripped:
            add(report, "error", "image_path is required by --require-image", row)

        if args.check_local_images and image_path_stripped and not is_url(image_path_stripped):
            candidate = Path(image_path_stripped)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            if not candidate.exists():
                add(report, "error", f"Local image_path does not exist: {image_path_stripped}", row)
            elif not candidate.is_file():
                add(report, "error", f"Local image_path is not a file: {image_path_stripped}", row)
            elif not image_like(str(candidate)):
                add(report, "warning", f"Local image_path does not look like an image by extension/MIME: {image_path_stripped}", row)

        for optional_field in ("id", "answer", "expected_answer"):
            if optional_field in item and item[optional_field] is not None and not isinstance(item[optional_field], str):
                add(report, "warning", f"{optional_field} is optional metadata; string values are easiest to serialize", row)

    report["valid"] = not report["errors"]
    return report


def main() -> int:
    args = parse_args()
    report = validate(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        status = "VALID" if report["valid"] else "INVALID"
        print(f"{status}: {report['file']} ({report['rows']} row(s))")
        for level in ("errors", "warnings"):
            for entry in report[level]:
                row = f" row={entry['row']}" if "row" in entry else ""
                print(f"{entry['level'].upper()}{row}: {entry['message']}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
