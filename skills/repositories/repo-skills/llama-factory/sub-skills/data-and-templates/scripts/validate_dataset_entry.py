#!/usr/bin/env python3
# Copyright 2025 the LlamaFactory team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Static validator for LlamaFactory dataset_info entries and tiny sample row files.

This script intentionally does not import LlamaFactory. It checks registry shape, column/tag mappings,
conversation ordering, ranking/KTO fields, multimodal placeholder counts, and optional local media paths.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any


SOURCE_KEYS = ("hf_hub_url", "ms_hub_url", "om_hub_url", "script_url", "cloud_file_name", "file_name")
HUB_KEYS = ("hf_hub_url", "ms_hub_url", "om_hub_url")
FORMATS = ("alpaca", "sharegpt", "openai")
ALLOWED_COLUMNS = {
    "prompt",
    "query",
    "response",
    "history",
    "messages",
    "system",
    "tools",
    "images",
    "videos",
    "audios",
    "chosen",
    "rejected",
    "kto_tag",
}
ALLOWED_TAGS = {
    "role_tag",
    "content_tag",
    "user_tag",
    "assistant_tag",
    "observation_tag",
    "function_tag",
    "system_tag",
}
LOCAL_SUFFIXES = {".json", ".jsonl", ".csv", ".parquet", ".arrow"}
PLACEHOLDERS = {"images": "<image>", "videos": "<video>", "audios": "<audio>"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def print(self) -> None:
        for message in self.errors:
            print(f"ERROR: {message}")
        for message in self.warnings:
            print(f"WARN: {message}")
        if not self.errors and not self.warnings:
            print("OK: no issues found")
        elif not self.errors:
            print(f"OK: no errors found ({len(self.warnings)} warning(s))")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a LlamaFactory dataset_info entry and optional tiny row file without imports."
    )
    parser.add_argument(
        "--dataset-info",
        type=Path,
        required=True,
        help="Path to a JSON file containing either full dataset_info content or one dataset entry.",
    )
    parser.add_argument(
        "--dataset-name",
        help="Top-level dataset key to validate. Required when --dataset-info contains multiple entries.",
    )
    parser.add_argument(
        "--row-file",
        type=Path,
        help="Optional tiny JSON, JSONL, or CSV file with representative raw row(s) to validate statically.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=20,
        help="Maximum rows to inspect from --row-file (default: 20).",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        help="Optional dataset_dir used to check local file_name existence.",
    )
    parser.add_argument(
        "--media-root",
        type=Path,
        help="Optional media_dir used to check relative image/video/audio file existence.",
    )
    parser.add_argument(
        "--stage",
        choices=("pt", "sft", "rm", "ppo", "kto"),
        help="Optional training stage compatibility check.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser.parse_args()


def load_json(path: Path, reporter: Reporter) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        reporter.error(f"cannot read JSON {path}: {exc}")
        return None


def select_entry(raw: Any, dataset_name: str | None, reporter: Reporter) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(raw, dict):
        reporter.error("dataset info must be a JSON object")
        return dataset_name or "<entry>", None

    if any(key in raw for key in SOURCE_KEYS) or "columns" in raw or "formatting" in raw:
        return dataset_name or "<entry>", raw

    if dataset_name is None:
        if len(raw) == 1:
            name = next(iter(raw))
            entry = raw[name]
            if not isinstance(entry, dict):
                reporter.error(f"entry {name!r} must be an object")
                return name, None
            return name, entry
        reporter.error("--dataset-name is required when dataset_info contains multiple entries")
        return "<missing>", None

    if dataset_name not in raw:
        reporter.error(f"undefined dataset {dataset_name!r} in dataset_info")
        return dataset_name, None

    entry = raw[dataset_name]
    if not isinstance(entry, dict):
        reporter.error(f"entry {dataset_name!r} must be an object")
        return dataset_name, None
    return dataset_name, entry


def columns(entry: dict[str, Any]) -> dict[str, str | None]:
    raw_columns = entry.get("columns") or {}
    return {
        "prompt": raw_columns.get("prompt", "instruction"),
        "query": raw_columns.get("query", "input"),
        "response": raw_columns.get("response", "output"),
        "history": raw_columns.get("history"),
        "messages": raw_columns.get("messages", "conversations"),
        "system": raw_columns.get("system"),
        "tools": raw_columns.get("tools"),
        "images": raw_columns.get("images"),
        "videos": raw_columns.get("videos"),
        "audios": raw_columns.get("audios"),
        "chosen": raw_columns.get("chosen"),
        "rejected": raw_columns.get("rejected"),
        "kto_tag": raw_columns.get("kto_tag"),
    }


def tags(entry: dict[str, Any]) -> dict[str, str | None]:
    raw_tags = entry.get("tags") or {}
    return {
        "role_tag": raw_tags.get("role_tag", "from"),
        "content_tag": raw_tags.get("content_tag", "value"),
        "user_tag": raw_tags.get("user_tag", "human"),
        "assistant_tag": raw_tags.get("assistant_tag", "gpt"),
        "observation_tag": raw_tags.get("observation_tag", "observation"),
        "function_tag": raw_tags.get("function_tag", "function_call"),
        "system_tag": raw_tags.get("system_tag", "system"),
    }


def load_rows(path: Path, max_rows: int, reporter: Reporter) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    rows: list[dict[str, Any]] = []
    try:
        if suffix == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                rows = raw[:max_rows]
            elif isinstance(raw, dict):
                rows = [raw]
            else:
                reporter.error("JSON row file must contain an object or list of objects")
        elif suffix == ".jsonl":
            with path.open(encoding="utf-8") as file_obj:
                for line in file_obj:
                    if line.strip():
                        rows.append(json.loads(line))
                    if len(rows) >= max_rows:
                        break
        elif suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as file_obj:
                rows = list(csv.DictReader(file_obj))[:max_rows]
        else:
            reporter.error("row validation supports only .json, .jsonl, and .csv")
    except Exception as exc:  # noqa: BLE001
        reporter.error(f"cannot read row file {path}: {exc}")

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            reporter.error(f"row {index}: expected object, got {type(row).__name__}")
    return [row for row in rows if isinstance(row, dict)]


def validate_entry(name: str, entry: dict[str, Any], args: argparse.Namespace, reporter: Reporter) -> None:
    source_keys = [key for key in SOURCE_KEYS if key in entry]
    if not source_keys:
        reporter.error(f"{name}: one of {', '.join(SOURCE_KEYS)} is required")
    if len(source_keys) > 1:
        reporter.warn(f"{name}: multiple source keys {source_keys}; hub/script/cloud/local precedence may ignore later keys")
    if any(key in entry for key in HUB_KEYS) and "file_name" in entry:
        reporter.warn(f"{name}: hub URL key is present, so local file_name is not the primary source")

    formatting = entry.get("formatting", "alpaca")
    if formatting not in FORMATS:
        reporter.error(f"{name}: formatting must be one of {FORMATS}, got {formatting!r}")

    if not isinstance(entry.get("ranking", False), bool):
        reporter.error(f"{name}: ranking must be boolean when present")

    raw_columns = entry.get("columns", {})
    if raw_columns is not None and not isinstance(raw_columns, dict):
        reporter.error(f"{name}: columns must be an object")
    else:
        for key, value in raw_columns.items():
            if key not in ALLOWED_COLUMNS:
                reporter.warn(f"{name}: unknown columns key {key!r}")
            if not isinstance(value, str):
                reporter.error(f"{name}: columns.{key} must be a string")

    raw_tags = entry.get("tags", {})
    if raw_tags is not None and not isinstance(raw_tags, dict):
        reporter.error(f"{name}: tags must be an object")
    else:
        for key, value in raw_tags.items():
            if key not in ALLOWED_TAGS:
                reporter.warn(f"{name}: unknown tags key {key!r}")
            if not isinstance(value, str):
                reporter.error(f"{name}: tags.{key} must be a string")

    if formatting == "openai" and not raw_tags:
        reporter.warn(f"{name}: openai rows usually need tags mapping role/content/user/assistant/tool/system")

    if "tokenized_path" in entry:
        reporter.warn(f"{name}: tokenized_path is a data argument, not a dataset_info entry key")

    if args.stage:
        ranking = entry.get("ranking", False)
        if args.stage == "rm" and not ranking:
            reporter.error(f"{name}: stage rm expects ranking: true")
        if args.stage != "rm" and ranking:
            reporter.error(f"{name}: stage {args.stage} rejects ranking: true datasets")

    if args.dataset_dir and "file_name" in entry and not any(key in entry for key in HUB_KEYS + ("script_url", "cloud_file_name")):
        local_path = args.dataset_dir / str(entry["file_name"])
        if not local_path.exists():
            reporter.error(f"{name}: local file_name does not exist under dataset_dir: {local_path}")
        elif local_path.is_file() and local_path.suffix.lower() not in LOCAL_SUFFIXES:
            reporter.error(f"{name}: unsupported local file suffix {local_path.suffix}")
        elif local_path.is_dir():
            suffixes = {child.suffix.lower() for child in local_path.iterdir() if child.is_file()}
            if not suffixes:
                reporter.warn(f"{name}: local directory file_name contains no files")
            if len(suffixes) > 1:
                reporter.error(f"{name}: local directory mixes file types: {sorted(suffixes)}")
            for suffix in suffixes:
                if suffix not in LOCAL_SUFFIXES:
                    reporter.error(f"{name}: unsupported local file suffix {suffix}")


def require_key(row: dict[str, Any], key: str | None, label: str, row_index: int, reporter: Reporter) -> bool:
    if key is None:
        reporter.error(f"row {row_index}: registry must map columns.{label}")
        return False
    if key not in row:
        reporter.error(f"row {row_index}: missing column {key!r} for {label}")
        return False
    return True


def text_count(value: Any, token: str) -> int:
    if isinstance(value, str):
        return value.count(token)
    if isinstance(value, list):
        return sum(text_count(item, token) for item in value)
    if isinstance(value, dict):
        return sum(text_count(item, token) for item in value.values())
    return 0


def media_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def flatten_media_paths(items: list[Any]) -> list[str]:
    paths: list[str] = []
    for item in items:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, list):
            paths.extend(flatten_media_paths(item))
        elif isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.append(item["path"])
    return paths


def validate_media(row: dict[str, Any], row_index: int, colmap: dict[str, str | None], reporter: Reporter, media_root: Path | None) -> None:
    text_blob = row
    for media_kind, placeholder in PLACEHOLDERS.items():
        expected = text_count(text_blob, placeholder)
        column = colmap[media_kind]
        actual_items = media_list(row.get(column)) if column else []
        actual = len(actual_items)
        if expected and not column:
            reporter.error(f"row {row_index}: found {placeholder} but columns.{media_kind} is not mapped")
        if column and column in row and actual != expected:
            reporter.error(
                f"row {row_index}: {media_kind} count {actual} does not match {placeholder} placeholder count {expected}"
            )
        if column and column in row and actual and media_root:
            for media_path in flatten_media_paths(actual_items):
                candidate = Path(media_path)
                if not candidate.is_absolute():
                    candidate = media_root / candidate
                if not candidate.exists():
                    reporter.error(f"row {row_index}: missing {media_kind} file {candidate}")


def validate_alpaca_row(
    row: dict[str, Any], row_index: int, entry: dict[str, Any], colmap: dict[str, str | None], reporter: Reporter
) -> None:
    require_key(row, colmap["prompt"], "prompt", row_index, reporter)
    if colmap["history"] and colmap["history"] in row:
        history = row[colmap["history"]]
        if not isinstance(history, list) or not all(isinstance(pair, list) and len(pair) == 2 for pair in history):
            reporter.error(f"row {row_index}: history must be a list of two-item lists")

    if entry.get("ranking", False):
        for label in ("chosen", "rejected"):
            if require_key(row, colmap[label], label, row_index, reporter) and not isinstance(row[colmap[label]], str):
                reporter.error(f"row {row_index}: alpaca ranking {label} must be a string")
    elif colmap["kto_tag"]:
        require_key(row, colmap["response"], "response", row_index, reporter)
        if require_key(row, colmap["kto_tag"], "kto_tag", row_index, reporter) and not isinstance(row[colmap["kto_tag"]], bool):
            reporter.error(f"row {row_index}: kto_tag must be boolean")
    else:
        if colmap["response"] not in row:
            reporter.warn(f"row {row_index}: response column {colmap['response']!r} is absent; this may be unsupervised/PT data")


def validate_message_sequence(
    messages: Any,
    row_index: int,
    tagmap: dict[str, str | None],
    ranking: bool,
    reporter: Reporter,
) -> None:
    if not isinstance(messages, list):
        reporter.error(f"row {row_index}: messages must be a list")
        return
    if not messages:
        reporter.error(f"row {row_index}: messages list is empty")
        return

    role_key = tagmap["role_tag"]
    content_key = tagmap["content_tag"]
    for turn_index, message in enumerate(messages):
        if not isinstance(message, dict):
            reporter.error(f"row {row_index} turn {turn_index}: message must be an object")
            continue
        if role_key not in message:
            reporter.error(f"row {row_index} turn {turn_index}: missing role tag {role_key!r}")
        if content_key not in message:
            reporter.error(f"row {row_index} turn {turn_index}: missing content tag {content_key!r}")

    aligned = messages[:]
    if aligned and isinstance(aligned[0], dict) and aligned[0].get(role_key) == tagmap["system_tag"]:
        aligned = aligned[1:]

    odd_tags = {tagmap["user_tag"], tagmap["observation_tag"]}
    even_tags = {tagmap["assistant_tag"], tagmap["function_tag"]}
    for turn_index, message in enumerate(aligned):
        if not isinstance(message, dict) or role_key not in message:
            continue
        accepted = odd_tags if turn_index % 2 == 0 else even_tags
        if message[role_key] not in accepted:
            reporter.error(
                f"row {row_index} turn {turn_index}: role {message[role_key]!r} violates alternating role order"
            )

    if not ranking and len(aligned) % 2 != 0:
        reporter.error(f"row {row_index}: non-ranking conversations need an even aligned message count")
    if ranking and len(aligned) % 2 != 1:
        reporter.error(f"row {row_index}: ranking conversations need an odd aligned prompt message count")


def validate_chat_row(
    row: dict[str, Any],
    row_index: int,
    entry: dict[str, Any],
    colmap: dict[str, str | None],
    tagmap: dict[str, str | None],
    reporter: Reporter,
) -> None:
    if require_key(row, colmap["messages"], "messages", row_index, reporter):
        validate_message_sequence(row[colmap["messages"]], row_index, tagmap, entry.get("ranking", False), reporter)

    if entry.get("ranking", False):
        assistant_like = {tagmap["assistant_tag"], tagmap["function_tag"]}
        for label in ("chosen", "rejected"):
            if not require_key(row, colmap[label], label, row_index, reporter):
                continue
            value = row[colmap[label]]
            if not isinstance(value, dict):
                reporter.error(f"row {row_index}: {label} must be a message object")
            elif value.get(tagmap["role_tag"]) not in assistant_like:
                reporter.error(f"row {row_index}: {label} role must be assistant-like")
    elif colmap["kto_tag"]:
        if require_key(row, colmap["kto_tag"], "kto_tag", row_index, reporter) and not isinstance(row[colmap["kto_tag"]], bool):
            reporter.error(f"row {row_index}: kto_tag must be boolean")


def validate_rows(entry: dict[str, Any], rows: list[dict[str, Any]], args: argparse.Namespace, reporter: Reporter) -> None:
    formatting = entry.get("formatting", "alpaca")
    colmap = columns(entry)
    tagmap = tags(entry)
    for row_index, row in enumerate(rows):
        if formatting == "alpaca":
            validate_alpaca_row(row, row_index, entry, colmap, reporter)
        elif formatting in {"sharegpt", "openai"}:
            validate_chat_row(row, row_index, entry, colmap, tagmap, reporter)
        validate_media(row, row_index, colmap, reporter, args.media_root)


def main() -> int:
    args = parse_args()
    reporter = Reporter()
    raw = load_json(args.dataset_info, reporter)
    name, entry = select_entry(raw, args.dataset_name, reporter)
    if entry is not None:
        validate_entry(name, entry, args, reporter)
        if args.row_file:
            rows = load_rows(args.row_file, args.max_rows, reporter)
            validate_rows(entry, rows, args, reporter)
    reporter.print()
    if reporter.errors or (args.strict and reporter.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
