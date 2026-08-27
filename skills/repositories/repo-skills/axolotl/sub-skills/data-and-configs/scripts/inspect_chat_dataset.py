#!/usr/bin/env python3
"""Inspect a local JSON/JSONL chat dataset for Axolotl chat_template fields."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

MESSAGE_FIELD_CANDIDATES = ("messages", "conversation", "conversations")
ROLE_FIELD_CANDIDATES = ("role", "from", "speaker", "author")
CONTENT_FIELD_CANDIDATES = ("content", "text", "value", "message")
CANONICAL_ROLE_HINTS = {
    "human": "user",
    "user": "user",
    "assistant": "assistant",
    "gpt": "assistant",
    "bot": "assistant",
    "system": "system",
    "tool": "tool",
}


class InspectionError(ValueError):
    """Raised for expected user-facing inspection failures."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview a local JSON/JSONL chat dataset and suggest Axolotl "
            "type: chat_template field mappings. This script never downloads data, "
            "imports Axolotl, loads tokenizers, or writes files."
        )
    )
    parser.add_argument("dataset", help="Path to a local .jsonl or .json dataset file")
    parser.add_argument(
        "--field-messages",
        help="Message-list field to inspect. Defaults to auto-detecting common names.",
    )
    parser.add_argument(
        "--records-key",
        help=(
            "For JSON objects containing a list of records, read records from this key "
            "instead of treating the object as one row."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum rows to inspect from the beginning of the file (default: 5).",
    )
    parser.add_argument(
        "--max-scan-lines",
        type=int,
        default=200,
        help="Maximum JSONL lines to scan while looking for valid rows (default: 200).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of a human-readable report.",
    )
    return parser.parse_args()


def load_jsonl(path: Path, limit: int, max_scan_lines: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > max_scan_lines:
                break
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise InspectionError(
                    f"line {line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise InspectionError(
                    f"line {line_number}: expected each JSONL row to be an object"
                )
            rows.append(value)
            if len(rows) >= limit:
                break
    return rows


def load_json(path: Path, limit: int, records_key: str | None) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InspectionError(f"invalid JSON: {exc.msg}") from exc

    if records_key:
        if not isinstance(value, dict):
            raise InspectionError("--records-key requires the JSON root to be an object")
        if records_key not in value:
            raise InspectionError(f"records key {records_key!r} not found in JSON root")
        value = value[records_key]
    elif isinstance(value, dict):
        list_keys = [key for key, item in value.items() if isinstance(item, list)]
        if len(list_keys) == 1 and not any(key in value for key in MESSAGE_FIELD_CANDIDATES):
            value = value[list_keys[0]]
        else:
            value = [value]

    if not isinstance(value, list):
        raise InspectionError("expected JSON root, records key, or detected records value to be a list")

    rows = value[:limit]
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise InspectionError(f"record {index}: expected an object")
    return rows


def load_rows(path: Path, limit: int, max_scan_lines: int, records_key: str | None) -> list[dict[str, Any]]:
    if limit < 1:
        raise InspectionError("--limit must be at least 1")
    if max_scan_lines < 1:
        raise InspectionError("--max-scan-lines must be at least 1")
    if not path.exists():
        raise InspectionError(f"dataset file not found: {path}")
    if path.is_dir():
        raise InspectionError(f"expected a file, got a directory: {path}")

    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        if records_key:
            raise InspectionError("--records-key is only valid for JSON files, not JSONL")
        rows = load_jsonl(path, limit, max_scan_lines)
    elif suffix == ".json":
        rows = load_json(path, limit, records_key)
    else:
        raise InspectionError("expected a .jsonl, .ndjson, or .json file")

    if not rows:
        raise InspectionError("no records found to inspect")
    return rows


def choose_message_field(rows: list[dict[str, Any]], requested: str | None) -> tuple[str, list[str]]:
    if requested:
        missing = [str(index) for index, row in enumerate(rows) if requested not in row]
        if missing:
            raise InspectionError(
                f"field_messages {requested!r} missing from inspected row indexes: {', '.join(missing)}"
            )
        return requested, []

    counts = Counter()
    for row in rows:
        for key in MESSAGE_FIELD_CANDIDATES:
            if isinstance(row.get(key), list):
                counts[key] += 1

    if not counts:
        available = sorted({key for row in rows for key in row.keys()})
        raise InspectionError(
            "no message-list field found; tried "
            f"{', '.join(MESSAGE_FIELD_CANDIDATES)}. Available row keys: {', '.join(available)}"
        )

    chosen, _ = counts.most_common(1)[0]
    alternatives = [key for key, count in counts.items() if key != chosen and count > 0]
    return chosen, alternatives


def first_message_dicts(rows: list[dict[str, Any]], field_messages: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        value = row.get(field_messages)
        if not isinstance(value, list):
            raise InspectionError(f"row {row_index}: {field_messages!r} is not a list")
        for message_index, message in enumerate(value):
            if not isinstance(message, dict):
                raise InspectionError(
                    f"row {row_index} message {message_index}: expected an object"
                )
            messages.append(message)
    if not messages:
        raise InspectionError(f"field_messages {field_messages!r} contains no messages")
    return messages


def choose_field(messages: list[dict[str, Any]], candidates: tuple[str, ...], label: str) -> tuple[str | None, list[str]]:
    counts = Counter()
    for message in messages:
        for key in candidates:
            if key in message:
                counts[key] += 1
    if not counts:
        return None, []
    chosen, _ = counts.most_common(1)[0]
    alternatives = [key for key, count in counts.items() if key != chosen and count > 0]
    return chosen, alternatives


def inspect(rows: list[dict[str, Any]], requested_field_messages: str | None) -> dict[str, Any]:
    field_messages, message_field_alternatives = choose_message_field(rows, requested_field_messages)
    messages = first_message_dicts(rows, field_messages)
    role_field, role_alternatives = choose_field(messages, ROLE_FIELD_CANDIDATES, "role")
    content_field, content_alternatives = choose_field(messages, CONTENT_FIELD_CANDIDATES, "content")

    warnings: list[str] = []
    errors: list[str] = []
    if role_field is None:
        errors.append("No role field found in inspected messages.")
    if content_field is None:
        errors.append("No content field found in inspected messages.")

    role_counts: Counter[str] = Counter()
    message_key_counts: Counter[str] = Counter()
    empty_content_indexes: list[str] = []
    unknown_roles: set[str] = set()

    for row_index, row in enumerate(rows):
        row_messages = row[field_messages]
        previous_role = None
        for message_index, message in enumerate(row_messages):
            message_key_counts.update(message.keys())
            role_value = message.get(role_field) if role_field else None
            if isinstance(role_value, str):
                role_counts[role_value] += 1
                if role_value not in CANONICAL_ROLE_HINTS:
                    unknown_roles.add(role_value)
                if previous_role == role_value and role_value not in {"tool", "system"}:
                    warnings.append(
                        f"row {row_index} messages {message_index - 1}-{message_index}: repeated role {role_value!r}"
                    )
                previous_role = role_value
            elif role_field:
                warnings.append(f"row {row_index} message {message_index}: role is not a string")

            content_value = message.get(content_field) if content_field else None
            if content_field and (content_value is None or content_value == ""):
                empty_content_indexes.append(f"{row_index}:{message_index}")

    if empty_content_indexes:
        warnings.append(
            "empty content values at row:message indexes " + ", ".join(empty_content_indexes[:10])
        )
    if unknown_roles:
        warnings.append(
            "roles not covered by Axolotl's common defaults: " + ", ".join(sorted(unknown_roles))
        )
    if role_counts and not any(
        CANONICAL_ROLE_HINTS.get(role) == "assistant" for role in role_counts
    ):
        warnings.append("no assistant-like role found; labels may all be ignored")

    suggested_entry: dict[str, Any] = {
        "path": "<your-local-or-hub-dataset>",
        "type": "chat_template",
        "field_messages": field_messages,
    }
    if role_field and content_field:
        suggested_entry["message_property_mappings"] = {
            "role": role_field,
            "content": content_field,
        }

    roles_suggestion: dict[str, list[str]] = {}
    for source_role in sorted(role_counts):
        canonical = CANONICAL_ROLE_HINTS.get(source_role)
        if canonical:
            roles_suggestion.setdefault(canonical, []).append(source_role)
    if roles_suggestion:
        suggested_entry["roles"] = roles_suggestion

    return {
        "rows_inspected": len(rows),
        "field_messages": field_messages,
        "message_field_alternatives": sorted(message_field_alternatives),
        "message_keys": dict(sorted(message_key_counts.items())),
        "role_field": role_field,
        "role_field_alternatives": sorted(role_alternatives),
        "content_field": content_field,
        "content_field_alternatives": sorted(content_alternatives),
        "role_counts": dict(sorted(role_counts.items())),
        "suggested_dataset_entry": suggested_entry,
        "warnings": warnings,
        "errors": errors,
    }


def print_human(report: dict[str, Any]) -> None:
    print("Axolotl chat dataset inspection")
    print(f"rows_inspected: {report['rows_inspected']}")
    print(f"field_messages: {report['field_messages']}")
    print(f"role_field: {report['role_field'] or '<not found>'}")
    print(f"content_field: {report['content_field'] or '<not found>'}")
    if report["role_counts"]:
        print("role_counts:")
        for role, count in report["role_counts"].items():
            print(f"  {role}: {count}")
    print("suggested_dataset_entry:")
    print("  path: <your-local-or-hub-dataset>")
    print("  type: chat_template")
    print(f"  field_messages: {report['field_messages']}")
    mappings = report["suggested_dataset_entry"].get("message_property_mappings")
    if mappings:
        print("  message_property_mappings:")
        print(f"    role: {mappings['role']}")
        print(f"    content: {mappings['content']}")
    roles = report["suggested_dataset_entry"].get("roles")
    if roles:
        print("  roles:")
        for target, sources in roles.items():
            print(f"    {target}:")
            for source in sources:
                print(f"      - {source}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    try:
        rows = load_rows(
            Path(args.dataset),
            limit=args.limit,
            max_scan_lines=args.max_scan_lines,
            records_key=args.records_key,
        )
        report = inspect(rows, args.field_messages)
    except InspectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
