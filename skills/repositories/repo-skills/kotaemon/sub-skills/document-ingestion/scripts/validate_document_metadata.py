#!/usr/bin/env python3
"""Validate small Kotaemon document-like JSON fixtures before indexing.

The script intentionally has no Kotaemon imports. It accepts either one JSON
object or a list of objects with text/content-like fields and metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import PurePath
from typing import Any

TEXT_KEYS = ("text", "content", "page_content")
KNOWN_TYPES = {"text", "table", "image", "thumbnail"}
IMPORTANT_METADATA_KEYS = {
    "source",
    "type",
    "table_origin",
    "page_label",
    "page_number",
    "file_name",
    "file_path",
    "sheet_name",
    "title",
    "image_origin",
    "window",
    "original_text",
}


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def as_records(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise TypeError("top-level JSON must be an object or a list of objects")


def text_value(record: dict[str, Any]) -> Any:
    for key in TEXT_KEYS:
        if key in record:
            return record[key]
    return None


def has_text(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(str(value).strip())


def looks_like_absolute_path(value: str) -> bool:
    if value.startswith(('/', '\\')):
        return True
    if len(value) > 2 and value[1] == ':' and value[2] in ('/', '\\'):
        return True
    parts = PurePath(value).parts
    return len(parts) > 3 and parts[0] in {"home", "Users", "root", "tmp"}


def validate_metadata(index: int, metadata: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    doc_type = metadata.get("type")
    if doc_type is not None and doc_type not in KNOWN_TYPES:
        warnings.append(
            f"record {index}: metadata.type={doc_type!r} is not one of {sorted(KNOWN_TYPES)}"
        )

    if "table_origin" in metadata:
        table_origin = metadata.get("table_origin")
        if not isinstance(table_origin, str) or not table_origin.strip():
            errors.append(f"record {index}: metadata.table_origin must be a non-empty string")
        if doc_type != "table":
            warnings.append(
                f"record {index}: table_origin is present but metadata.type is not 'table'"
            )

    if doc_type == "table" and not metadata.get("table_origin"):
        errors.append(f"record {index}: table document is missing metadata.table_origin")

    if doc_type in {"table", "image", "thumbnail"} and "page_label" not in metadata:
        warnings.append(
            f"record {index}: {doc_type} document has no metadata.page_label for citation/debugging"
        )

    page_label = metadata.get("page_label")
    if page_label is not None and not isinstance(page_label, (str, int)):
        errors.append(f"record {index}: metadata.page_label must be a string or integer")

    page_number = metadata.get("page_number")
    if page_number is not None and not isinstance(page_number, int):
        warnings.append(f"record {index}: metadata.page_number is usually an integer")

    for key in ("source", "file_name", "file_path", "sheet_name", "title"):
        value = metadata.get(key)
        if value is not None and not isinstance(value, str):
            errors.append(f"record {index}: metadata.{key} must be a string when present")

    for key in ("source", "file_path"):
        value = metadata.get(key)
        if isinstance(value, str) and looks_like_absolute_path(value):
            warnings.append(
                f"record {index}: metadata.{key} looks like a machine-local absolute path"
            )

    image_origin = metadata.get("image_origin")
    if image_origin is not None and not isinstance(image_origin, str):
        errors.append(f"record {index}: metadata.image_origin must be a string when present")

    unknown = sorted(set(metadata) - IMPORTANT_METADATA_KEYS)
    if unknown:
        warnings.append(
            f"record {index}: metadata has additional keys: {', '.join(unknown)}"
        )

    return errors, warnings


def validate_records(records: list[Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not records:
        errors.append("document list is empty")
        return errors, warnings

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index}: expected object, got {type(record).__name__}")
            continue

        if not has_text(text_value(record)):
            errors.append(
                f"record {index}: missing non-empty text/content/page_content field"
            )

        metadata = record.get("metadata", {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            errors.append(f"record {index}: metadata must be an object")
            continue

        metadata_errors, metadata_warnings = validate_metadata(index, metadata)
        errors.extend(metadata_errors)
        warnings.extend(metadata_warnings)

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate JSON document-like records for Kotaemon ingestion metadata."
    )
    parser.add_argument("json_file", help="Path to JSON file, or '-' for stdin")
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return non-zero when warnings are present.",
    )
    args = parser.parse_args(argv)

    try:
        payload = load_json(args.json_file)
        records = as_records(payload)
        errors, warnings = validate_records(records)
    except Exception as exc:  # noqa: BLE001 - CLI should report JSON/type failures plainly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors or (args.strict_warnings and warnings):
        print(
            f"invalid: {len(records)} record(s), {len(errors)} error(s), {len(warnings)} warning(s)",
            file=sys.stderr,
        )
        return 1

    print(f"valid: {len(records)} record(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
