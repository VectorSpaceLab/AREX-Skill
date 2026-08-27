#!/usr/bin/env python3
"""Validate common ms-swift JSONL/JSON/CSV dataset rows before long runs."""
from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

VALID_ROLES = {"system", "user", "assistant", "tool_call", "tool_response", "tool"}
MESSAGE_FIELDS = {"messages", "rejected_messages", "positive_messages", "negative_messages"}
MEDIA_FIELDS = {
    "images",
    "videos",
    "audios",
    "rejected_images",
    "rejected_videos",
    "rejected_audios",
    "positive_images",
    "positive_videos",
    "positive_audios",
    "negative_images",
    "negative_videos",
    "negative_audios",
}
JSON_LIKE_FIELDS = MESSAGE_FIELDS | MEDIA_FIELDS | {
    "conversation",
    "conversations",
    "tools",
    "rejected_tools",
    "positive_tools",
    "negative_tools",
    "objects",
    "chat_template_kwargs",
    "history",
}
QUERY_ALIASES = {"query", "prompt", "input", "instruction", "question", "problem"}
RESPONSE_ALIASES = {
    "response",
    "answer",
    "output",
    "targets",
    "target",
    "answer_key",
    "answers",
    "solution",
    "text",
    "completion",
    "content",
}
SYSTEM_ALIASES = {"system", "system_prompt"}
PLACEHOLDER_BY_MEDIA = {"images": "<image>", "videos": "<video>", "audios": "<audio>"}
REMOTE_SCHEMES = {"http", "https", "s3", "oss", "gs", "az"}


class RowDiagnostics:
    def __init__(self, row_label: str) -> None:
        self.row_label = row_label
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate common ms-swift dataset row fields in JSONL, JSON, or CSV files.")
    parser.add_argument("path", help="Dataset file to validate.")
    parser.add_argument("--format", choices=["auto", "jsonl", "json", "csv"], default="auto")
    parser.add_argument(
        "--columns",
        nargs="*",
        default=[],
        metavar="SOURCE=TARGET",
        help="Apply ms-swift-style column renames before validation. Use TARGET=_ to ignore a column.",
    )
    parser.add_argument(
        "--check-media",
        choices=["none", "syntax", "exists"],
        default="syntax",
        help="Validate media field syntax only, require local paths to exist, or skip media checks.",
    )
    parser.add_argument("--max-errors", type=int, default=50, help="Stop after this many row-level errors.")
    parser.add_argument("--max-rows", type=int, default=None, help="Validate at most this many rows.")
    parser.add_argument("--quiet-ok", action="store_true", help="Only print rows with warnings or errors.")
    return parser.parse_args()


def parse_column_mapping(items: Sequence[str]) -> List[Tuple[str, str]]:
    mappings: List[Tuple[str, str]] = []
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Invalid --columns item {item!r}; expected SOURCE=TARGET")
        source, target = item.split("=", 1)
        source = source.strip()
        target = target.strip()
        if not source or not target:
            raise SystemExit(f"Invalid --columns item {item!r}; source and target must be non-empty")
        mappings.append((source, target))
    return mappings


def detect_format(path: Path, explicit_format: str) -> str:
    if explicit_format != "auto":
        return explicit_format
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    return "jsonl"


def load_rows(path: Path, file_format: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
    if file_format == "jsonl":
        with path.open("r", encoding="utf-8") as dataset_file:
            for line_number, line in enumerate(dataset_file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    yield f"line {line_number}", {"__parse_error__": str(exc)}
                    continue
                if not isinstance(row, dict):
                    yield f"line {line_number}", {"__parse_error__": "row is not a JSON object"}
                else:
                    yield f"line {line_number}", row
        return

    if file_format == "json":
        with path.open("r", encoding="utf-8") as dataset_file:
            try:
                data = json.load(dataset_file)
            except json.JSONDecodeError as exc:
                yield "json", {"__parse_error__": str(exc)}
                return
        if isinstance(data, list):
            for row_number, row in enumerate(data, start=1):
                if isinstance(row, dict):
                    yield f"row {row_number}", row
                else:
                    yield f"row {row_number}", {"__parse_error__": "row is not a JSON object"}
        elif isinstance(data, dict):
            if isinstance(data.get("data"), list):
                for row_number, row in enumerate(data["data"], start=1):
                    if isinstance(row, dict):
                        yield f"data[{row_number}]", row
                    else:
                        yield f"data[{row_number}]", {"__parse_error__": "row is not a JSON object"}
            else:
                yield "row 1", data
        else:
            yield "json", {"__parse_error__": "top-level JSON must be an object or list"}
        return

    if file_format == "csv":
        with path.open("r", encoding="utf-8", newline="") as dataset_file:
            reader = csv.DictReader(dataset_file)
            for row_number, row in enumerate(reader, start=2):
                yield f"line {row_number}", dict(row)
        return

    raise ValueError(f"Unsupported format: {file_format}")


def apply_column_mapping(row: Dict[str, Any], mappings: Sequence[Tuple[str, str]], diagnostics: RowDiagnostics) -> Dict[str, Any]:
    mapped_row = dict(row)
    for source, target in mappings:
        if source not in mapped_row:
            continue
        value = mapped_row.pop(source)
        if target == "_":
            diagnostics.note(f"ignored column {source!r} via --columns")
            continue
        if target in mapped_row and source != target:
            diagnostics.warn(f"--columns overwrote existing {target!r} from source {source!r}")
        mapped_row[target] = value
    return mapped_row


def parse_structured_value(field_name: str, value: Any, diagnostics: RowDiagnostics) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if stripped == "":
        return value
    should_parse = field_name in JSON_LIKE_FIELDS or stripped[:1] in "[{" or stripped in {"true", "false", "null"}
    if not should_parse:
        return value
    try:
        return json.loads(stripped)
    except Exception:
        pass
    try:
        return ast.literal_eval(stripped)
    except Exception:
        if field_name in JSON_LIKE_FIELDS:
            diagnostics.warn(f"{field_name!r} is a string that could not be parsed as JSON/Python literal")
        return value


def coerce_structured_fields(row: Dict[str, Any], diagnostics: RowDiagnostics) -> Dict[str, Any]:
    coerced: Dict[str, Any] = {}
    for field_name, value in row.items():
        coerced[field_name] = parse_structured_value(field_name, value, diagnostics)
    return coerced


def text_from_messages(messages: Any) -> str:
    if not isinstance(messages, list):
        return ""
    parts: List[str] = []
    for message in messages:
        if isinstance(message, dict):
            content = message.get("content")
            if content is not None:
                parts.append(str(content))
    return "\n".join(parts)


def count_placeholder(messages: Any, placeholder: str) -> int:
    return text_from_messages(messages).count(placeholder)


def last_message_content(messages: Any) -> Optional[str]:
    if not isinstance(messages, list) or not messages:
        return None
    last_message = messages[-1]
    if isinstance(last_message, dict) and last_message.get("content") is not None:
        return str(last_message.get("content"))
    return None


def is_remote_or_data_uri(value: str) -> bool:
    if value.startswith("data:"):
        return True
    parsed = urlparse(value)
    return parsed.scheme.lower() in REMOTE_SCHEMES


def media_count(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, str):
        return 1
    if isinstance(value, dict):
        return 1
    if isinstance(value, list):
        return len(value)
    return 0


def iter_media_paths(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        path_value = value.get("path")
        if isinstance(path_value, str):
            yield path_value
    elif isinstance(value, list):
        for item in value:
            yield from iter_media_paths(item)


def validate_messages(messages: Any, field_name: str, diagnostics: RowDiagnostics) -> bool:
    if not isinstance(messages, list):
        diagnostics.error(f"{field_name} must be a list of message objects")
        return False
    if not messages:
        diagnostics.error(f"{field_name} must not be empty")
        return False

    valid = True
    previous_role: Optional[str] = None
    previous_tool_call_had_loss = False
    for message_index, message in enumerate(messages):
        location = f"{field_name}[{message_index}]"
        if not isinstance(message, dict):
            diagnostics.error(f"{location} must be an object")
            valid = False
            continue
        role = message.get("role")
        content = message.get("content")
        if role not in VALID_ROLES:
            diagnostics.error(f"{location}.role must be one of {sorted(VALID_ROLES)}, got {role!r}")
            valid = False
        if content is None:
            diagnostics.error(f"{location}.content must not be null")
            valid = False
        extra_keys = set(message) - {"role", "content", "loss", "loss_scale"}
        if extra_keys:
            diagnostics.warn(f"{location} has extra keys that standard preprocessing may drop: {sorted(extra_keys)}")
        if "loss" in message and not isinstance(message["loss"], bool):
            diagnostics.error(f"{location}.loss must be boolean when present")
            valid = False
        if "loss_scale" in message and not isinstance(message["loss_scale"], (int, float)):
            diagnostics.error(f"{location}.loss_scale must be numeric when present")
            valid = False
        if ("loss" in message or "loss_scale" in message) and role != "assistant" and role != "tool_call":
            diagnostics.warn(f"{location} has loss controls on role {role!r}; standard use is assistant spans")
        current_tool_call_had_loss = role == "tool_call" and ("loss" in message or "loss_scale" in message)
        if previous_role == "tool_call" and role == "tool_call" and previous_tool_call_had_loss:
            diagnostics.warn("consecutive tool_call messages may only honor the first loss/loss_scale setting")
        previous_role = role if isinstance(role, str) else None
        previous_tool_call_had_loss = current_tool_call_had_loss
    return valid


def validate_sharegpt(row: Dict[str, Any], diagnostics: RowDiagnostics) -> None:
    conversation = row.get("conversation", row.get("conversations"))
    if conversation is None:
        return
    if isinstance(conversation, dict) and len(conversation) == 1:
        conversation = next(iter(conversation.values()))
    if not isinstance(conversation, list):
        diagnostics.error("conversation/conversations must be a list for MessagesPreprocessor")
        return
    if not conversation:
        diagnostics.error("conversation/conversations must not be empty")
        return
    first_item = conversation[0]
    if isinstance(first_item, dict):
        if {"human", "assistant"}.issubset(first_item):
            diagnostics.note("detected ShareGPT pair format")
        elif {"from", "value"}.issubset(first_item) or {"role", "content"}.issubset(first_item):
            diagnostics.note("detected message-like conversation format")
        else:
            diagnostics.warn("conversation entries do not use obvious ShareGPT/message keys")
    else:
        diagnostics.error("conversation entries must be objects")


def validate_media(row: Dict[str, Any], diagnostics: RowDiagnostics, check_media: str, dataset_dir: Path) -> None:
    if check_media == "none":
        return
    for field_name in sorted(MEDIA_FIELDS):
        if field_name not in row or row[field_name] in (None, ""):
            continue
        value = row[field_name]
        if not isinstance(value, (str, list, dict)):
            diagnostics.error(f"{field_name} must be a path/URL string, object, or list")
            continue
        if check_media == "exists":
            for media_path in iter_media_paths(value):
                if not media_path or is_remote_or_data_uri(media_path):
                    continue
                local_path = Path(media_path).expanduser()
                if not local_path.is_absolute():
                    local_path = dataset_dir / local_path
                if not local_path.exists():
                    diagnostics.error(f"{field_name} path does not exist: {media_path}")

    messages = row.get("messages")
    if isinstance(messages, list):
        for media_field, placeholder in PLACEHOLDER_BY_MEDIA.items():
            placeholder_count = count_placeholder(messages, placeholder)
            current_media_count = media_count(row.get(media_field))
            if placeholder_count != current_media_count:
                if placeholder_count or current_media_count:
                    diagnostics.warn(
                        f"{placeholder} count ({placeholder_count}) differs from {media_field} count ({current_media_count})")

    rejected_messages = row.get("rejected_messages")
    if isinstance(rejected_messages, list):
        for media_field, placeholder in PLACEHOLDER_BY_MEDIA.items():
            rejected_field = f"rejected_{media_field}"
            placeholder_count = count_placeholder(rejected_messages, placeholder)
            rejected_count = media_count(row.get(rejected_field))
            if placeholder_count and rejected_count == 0 and media_count(row.get(media_field)):
                diagnostics.warn(f"rejected_messages contains {placeholder} but {rejected_field} is absent")


def validate_tools(row: Dict[str, Any], diagnostics: RowDiagnostics) -> None:
    for field_name in ["tools", "rejected_tools", "positive_tools", "negative_tools"]:
        if field_name not in row or row[field_name] in (None, ""):
            continue
        value = row[field_name]
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                diagnostics.error(f"{field_name} must be a JSON list or list object")
                continue
        if not isinstance(value, list):
            diagnostics.error(f"{field_name} must be a list of tool schemas")
            continue
        for tool_index, tool in enumerate(value):
            if not isinstance(tool, dict):
                diagnostics.warn(f"{field_name}[{tool_index}] is not an object")

    messages = row.get("messages")
    if isinstance(messages, list):
        for message_index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            if message.get("role") not in {"tool_call", "tool_response", "tool"}:
                continue
            content = message.get("content")
            if isinstance(content, str):
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    diagnostics.warn(f"messages[{message_index}].content for {message.get('role')} is not valid JSON")
            elif content is not None:
                diagnostics.warn(f"messages[{message_index}].content for {message.get('role')} should usually be a JSON string")


def validate_objects(row: Dict[str, Any], diagnostics: RowDiagnostics) -> None:
    objects = row.get("objects")
    if objects is None or objects == "":
        return
    if not isinstance(objects, dict):
        diagnostics.error("objects must be an object with ref/bbox/bbox_type/image_id fields")
        return
    refs = objects.get("ref", [])
    boxes = objects.get("bbox")
    image_ids = objects.get("image_id")
    if refs is not None and not isinstance(refs, list):
        diagnostics.error("objects.ref must be a list when present")
    if not isinstance(boxes, list):
        diagnostics.error("objects.bbox must be a list")
        return
    for box_index, box in enumerate(boxes):
        if not isinstance(box, list) or len(box) not in {2, 4}:
            diagnostics.error(f"objects.bbox[{box_index}] must be a list of length 2 or 4")
        elif not all(isinstance(coordinate, (int, float)) for coordinate in box):
            diagnostics.error(f"objects.bbox[{box_index}] coordinates must be numeric")
    if image_ids is not None:
        if not isinstance(image_ids, list):
            diagnostics.error("objects.image_id must be a list when present")
        elif len(image_ids) != len(boxes):
            diagnostics.error("objects.image_id length must match objects.bbox length")
    messages = row.get("messages")
    if isinstance(messages, list):
        ref_placeholders = count_placeholder(messages, "<ref-object>")
        bbox_placeholders = count_placeholder(messages, "<bbox>")
        if isinstance(refs, list) and ref_placeholders != len(refs):
            diagnostics.warn(f"<ref-object> count ({ref_placeholders}) differs from objects.ref length ({len(refs)})")
        if bbox_placeholders != len(boxes):
            diagnostics.warn(f"<bbox> count ({bbox_placeholders}) differs from objects.bbox length ({len(boxes)})")


def validate_preference_fields(row: Dict[str, Any], diagnostics: RowDiagnostics) -> None:
    if "rejected_response" in row:
        rejected_response = row.get("rejected_response")
        if rejected_response in (None, "", []):
            diagnostics.error("rejected_response must not be empty when present")
        chosen_content = last_message_content(row.get("messages"))
        if chosen_content is not None and isinstance(rejected_response, str) and rejected_response == chosen_content:
            diagnostics.error("rejected_response is identical to the final chosen message content")
    if "rejected_messages" in row:
        validate_messages(row.get("rejected_messages"), "rejected_messages", diagnostics)
    if "label" in row:
        label = row["label"]
        if not isinstance(label, (bool, int, float, str, list)) and label is not None:
            diagnostics.warn("label has an unusual type; KTO/classification/regression labels are usually bool, number, string, or list")


def validate_misc_fields(row: Dict[str, Any], diagnostics: RowDiagnostics) -> None:
    chat_template_kwargs = row.get("chat_template_kwargs")
    if chat_template_kwargs is not None and not isinstance(chat_template_kwargs, dict):
        diagnostics.error("chat_template_kwargs must be an object")
    if "channel" in row and row.get("channel") in (None, ""):
        diagnostics.warn("channel is present but empty")
    if "loss" in row or "loss_scale" in row:
        diagnostics.warn("row-level loss/loss_scale found; ms-swift standard examples place these inside assistant messages")


def detect_auto_preprocessor_shape(row: Dict[str, Any], diagnostics: RowDiagnostics) -> None:
    if "messages" in row:
        return
    if "conversation" in row or "conversations" in row:
        diagnostics.note("AutoPreprocessor should choose MessagesPreprocessor")
        return
    if "instruction" in row and "input" in row:
        diagnostics.note("AutoPreprocessor should choose AlpacaPreprocessor")
        return
    has_query = bool(QUERY_ALIASES & set(row))
    has_response = bool(RESPONSE_ALIASES & set(row))
    if has_query or has_response:
        diagnostics.note("AutoPreprocessor should choose ResponsePreprocessor")
        if not has_response:
            diagnostics.warn("query-like fields are present without an obvious response field")
        return
    diagnostics.error("row does not contain messages, conversation(s), alpaca fields, or query/response-style fields")


def summarize_row(row: Dict[str, Any]) -> str:
    parts: List[str] = []
    if isinstance(row.get("messages"), list):
        parts.append(f"messages={len(row['messages'])}")
    for media_field in ["images", "videos", "audios"]:
        count = media_count(row.get(media_field))
        if count:
            parts.append(f"{media_field}={count}")
    if "rejected_response" in row:
        parts.append("rejected_response")
    if "rejected_messages" in row:
        parts.append("rejected_messages")
    if "tools" in row:
        parts.append("tools")
    if "objects" in row:
        parts.append("objects")
    return ", ".join(parts) or "recognized auto-preprocessor row"


def validate_row(
    raw_row: Dict[str, Any],
    row_label: str,
    mappings: Sequence[Tuple[str, str]],
    check_media: str,
    dataset_dir: Path,
) -> Tuple[RowDiagnostics, Dict[str, Any]]:
    diagnostics = RowDiagnostics(row_label)
    if "__parse_error__" in raw_row:
        diagnostics.error(f"parse error: {raw_row['__parse_error__']}")
        return diagnostics, raw_row
    mapped_row = apply_column_mapping(raw_row, mappings, diagnostics)
    row = coerce_structured_fields(mapped_row, diagnostics)
    detect_auto_preprocessor_shape(row, diagnostics)
    validate_sharegpt(row, diagnostics)
    if "messages" in row:
        validate_messages(row.get("messages"), "messages", diagnostics)
    validate_preference_fields(row, diagnostics)
    validate_media(row, diagnostics, check_media, dataset_dir)
    validate_tools(row, diagnostics)
    validate_objects(row, diagnostics)
    validate_misc_fields(row, diagnostics)
    return diagnostics, row


def print_diagnostics(diagnostics: RowDiagnostics, row: Dict[str, Any], quiet_ok: bool) -> None:
    status = "ERROR" if diagnostics.errors else "WARN" if diagnostics.warnings else "OK"
    if quiet_ok and status == "OK":
        return
    print(f"[{status}] {diagnostics.row_label}: {summarize_row(row)}")
    for message in diagnostics.errors:
        print(f"  error: {message}")
    for message in diagnostics.warnings:
        print(f"  warn: {message}")
    for message in diagnostics.info:
        print(f"  info: {message}")


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.path)
    if not dataset_path.exists():
        print(f"Dataset file not found: {dataset_path}", file=sys.stderr)
        return 2
    mappings = parse_column_mapping(args.columns)
    file_format = detect_format(dataset_path, args.format)
    total_rows = 0
    error_rows = 0
    warning_rows = 0
    dataset_dir = dataset_path.resolve().parent

    for row_label, raw_row in load_rows(dataset_path, file_format):
        total_rows += 1
        if args.max_rows is not None and total_rows > args.max_rows:
            total_rows -= 1
            break
        diagnostics, row = validate_row(raw_row, row_label, mappings, args.check_media, dataset_dir)
        if diagnostics.errors:
            error_rows += 1
        elif diagnostics.warnings:
            warning_rows += 1
        print_diagnostics(diagnostics, row, args.quiet_ok)
        if error_rows >= args.max_errors:
            print(f"Stopped after reaching --max-errors={args.max_errors}")
            break

    print(f"Summary: rows={total_rows}, error_rows={error_rows}, warning_rows={warning_rows}, format={file_format}")
    return 1 if error_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
