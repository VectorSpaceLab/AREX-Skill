#!/usr/bin/env python3
"""Validate local JSONL rows against common TRL dataset shapes.

This checker performs schema validation only. It does not download models,
import TRL, apply templates, or run training.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

VALID_ROLES = {"system", "user", "assistant", "tool"}
VALID_TASKS = {"sft", "dpo", "reward", "grpo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate JSONL rows for common TRL SFT, DPO, reward-modeling, and GRPO dataset schemas."
    )
    parser.add_argument("path", type=Path, help="Path to a local JSONL file.")
    parser.add_argument(
        "--task",
        required=True,
        choices=sorted(VALID_TASKS),
        help="Dataset task shape to validate: sft, dpo, reward, or grpo.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Stop after this many row/schema errors (defaults to 20).",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as error:
                errors.append(f"line {line_number}: invalid JSON: {error.msg}")
                continue
            if not isinstance(row, dict):
                errors.append(f"line {line_number}: row must be a JSON object")
                continue
            rows.append({"__line__": line_number, **row})
    return rows, errors


def is_string(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def is_message(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    role = value.get("role")
    if role not in VALID_ROLES:
        return False
    has_content = "content" in value
    has_tool_calls = "tool_calls" in value
    if role == "assistant" and has_tool_calls:
        return True
    if role == "tool" and "name" not in value:
        return False
    return has_content


def is_messages(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(is_message(message) for message in value)


def is_text_or_messages(value: Any) -> bool:
    return is_string(value) or is_messages(value)


def is_completion_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(is_string(item) or is_messages(item) for item in value)


def has_any(row: dict[str, Any], keys: Iterable[str]) -> bool:
    return any(key in row for key in keys)


def validate_tools(row: dict[str, Any]) -> list[str]:
    if "tools" not in row:
        return []
    tools = row["tools"]
    if isinstance(tools, str):
        try:
            parsed = json.loads(tools)
        except json.JSONDecodeError:
            return ["tools is a string but not valid JSON"]
        tools = parsed
    if not isinstance(tools, list):
        return ["tools must be a list or a JSON string encoding a list"]
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            return [f"tools[{index}] must be an object"]
    return []


def validate_sft(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    has_language_modeling = is_string(row.get("text")) or is_messages(row.get("messages"))
    has_prompt_completion = is_text_or_messages(row.get("prompt")) and is_text_or_messages(row.get("completion"))
    has_prompt_only = is_text_or_messages(row.get("prompt")) and "completion" not in row
    if not (has_language_modeling or has_prompt_completion or has_prompt_only):
        errors.append("sft row must have text, messages, prompt, or prompt+completion")
    errors.extend(validate_tools(row))
    return errors


def validate_dpo(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    explicit = (
        is_text_or_messages(row.get("prompt"))
        and is_text_or_messages(row.get("chosen"))
        and is_text_or_messages(row.get("rejected"))
    )
    implicit = "prompt" not in row and is_text_or_messages(row.get("chosen")) and is_text_or_messages(row.get("rejected"))
    if not (explicit or implicit):
        errors.append("dpo row must have prompt+chosen+rejected or implicit chosen+rejected")
    return errors


def validate_reward(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    paired = is_text_or_messages(row.get("chosen")) and is_text_or_messages(row.get("rejected"))
    unpaired = is_text_or_messages(row.get("prompt")) and is_text_or_messages(row.get("completion")) and is_bool(row.get("label"))
    scored = is_text_or_messages(row.get("prompt")) and is_completion_list(row.get("completions")) and isinstance(
        row.get("labels"), list
    )
    if scored and len(row["completions"]) != len(row["labels"]):
        errors.append("completions and labels must have matching lengths")
    if not (paired or unpaired or scored):
        errors.append("reward row must be paired chosen/rejected, unpaired prompt+completion+label, or prompt+completions+labels")
    return errors


def validate_grpo(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not is_text_or_messages(row.get("prompt")):
        errors.append("grpo row must have a prompt string or prompt message list")
    if has_any(row, ["solution", "answer"]) and not any(is_string(row.get(key)) for key in ["solution", "answer"]):
        errors.append("solution/answer columns, when present, must be non-empty strings")
    errors.extend(validate_tools(row))
    return errors


def validate_row(task: str, row: dict[str, Any]) -> list[str]:
    if task == "sft":
        return validate_sft(row)
    if task == "dpo":
        return validate_dpo(row)
    if task == "reward":
        return validate_reward(row)
    if task == "grpo":
        return validate_grpo(row)
    raise ValueError(f"unsupported task: {task}")


def main() -> int:
    args = parse_args()
    if not args.path.is_file():
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2
    if args.max_errors < 1:
        print("error: --max-errors must be at least 1", file=sys.stderr)
        return 2

    rows, errors = load_jsonl(args.path)
    if not rows and not errors:
        errors.append("file contains no JSON objects")

    for row in rows:
        line_number = row.pop("__line__")
        for error in validate_row(args.task, row):
            errors.append(f"line {line_number}: {error}")
            if len(errors) >= args.max_errors:
                break
        if len(errors) >= args.max_errors:
            break

    if errors:
        for error in errors[: args.max_errors]:
            print(f"error: {error}", file=sys.stderr)
        if len(errors) >= args.max_errors:
            print(f"error: stopped after {args.max_errors} errors", file=sys.stderr)
        return 1

    print(f"OK: validated {len(rows)} JSONL row(s) for task {args.task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
