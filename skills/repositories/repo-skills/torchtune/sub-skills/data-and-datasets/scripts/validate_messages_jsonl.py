#!/usr/bin/env python3
"""Validate torchtune-style JSONL data rows without training or downloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_MESSAGE_ROLES = {"system", "user", "assistant", "ipython", "tool"}
VALID_SHAREGPT_ROLES = {"system", "human", "gpt"}


class Issue:
    def __init__(self, line: int, level: str, message: str, fix: str) -> None:
        self.line = line
        self.level = level
        self.message = message
        self.fix = fix

    def format(self) -> str:
        return f"line {self.line}: {self.level}: {self.message}\n  fix: {self.fix}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate local JSONL rows for common torchtune data shapes. "
            "This script uses only the Python standard library and never downloads datasets."
        )
    )
    parser.add_argument("jsonl", type=Path, help="Path to a local .jsonl file.")
    parser.add_argument(
        "--shape",
        choices=["auto", "messages", "conversations", "input-output", "chosen-rejected"],
        default="auto",
        help="Expected row shape. 'auto' detects supported shapes per row.",
    )
    parser.add_argument("--messages-key", default="messages", help="OpenAI-style messages key.")
    parser.add_argument("--conversations-key", default="conversations", help="ShareGPT-style conversations key.")
    parser.add_argument("--input-key", default="input", help="Input/prompt column key.")
    parser.add_argument("--output-key", default="output", help="Output/response column key.")
    parser.add_argument("--chosen-key", default="chosen", help="Chosen preference column key.")
    parser.add_argument("--rejected-key", default="rejected", help="Rejected preference column key.")
    parser.add_argument("--image-key", default=None, help="Optional image path column key to validate.")
    parser.add_argument("--image-root", type=Path, default=Path("."), help="Root used for relative image paths.")
    parser.add_argument(
        "--check-image-paths",
        action="store_true",
        help="Require local image paths in --image-key to exist. URLs are accepted without network checks.",
    )
    parser.add_argument("--image-tag", default=None, help="Optional placeholder expected in the first user prompt.")
    parser.add_argument(
        "--require-matching-preference-prompts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require chosen/rejected preference rows to share the same prompt prefix before the final assistant answer.",
    )
    parser.add_argument(
        "--train-on-input",
        choices=["true", "false", "unspecified"],
        default="unspecified",
        help="Document the expected prompt masking mode in the summary; no tokenization is performed.",
    )
    parser.add_argument("--max-lines", type=int, default=None, help="Stop after validating this many non-empty JSONL rows.")
    return parser.parse_args()


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("content", item.get("text", ""))))
                elif item.get("type") == "image":
                    parts.append("<image>")
                elif item.get("type") == "image_url":
                    parts.append("<image>")
        return "".join(parts)
    return ""


def normalized_prompt_prefix(messages: list[dict[str, Any]]) -> list[tuple[str, str]]:
    prefix = messages[:]
    if prefix and prefix[-1].get("role") == "assistant":
        prefix = prefix[:-1]
    return [(str(message.get("role")), text_from_content(message.get("content"))) for message in prefix]


def validate_openai_messages(messages: Any, line: int, container: str) -> list[Issue]:
    issues: list[Issue] = []
    if not isinstance(messages, list):
        return [
            Issue(
                line,
                "error",
                f"{container} must be a list of message objects",
                "Store each conversation as a JSON list, not a string or object.",
            )
        ]
    if len(messages) < 2:
        issues.append(
            Issue(
                line,
                "error",
                f"{container} has {len(messages)} messages; torchtune expects at least one user/assistant turn",
                "Add a user prompt and an assistant response or filter this row out.",
            )
        )
    last_role = "assistant"
    last_ipython = False
    for index, message in enumerate(messages):
        path = f"{container}[{index}]"
        if not isinstance(message, dict):
            issues.append(Issue(line, "error", f"{path} is not an object", "Use objects with role and content fields."))
            continue
        role = message.get("role")
        if role not in VALID_MESSAGE_ROLES:
            issues.append(
                Issue(
                    line,
                    "error",
                    f"{path}.role={role!r} is not supported",
                    "Use one of system, user, assistant, ipython, or tool; map ShareGPT roles before using OpenAI style.",
                )
            )
        content = message.get("content")
        if content is None or text_from_content(content) == "":
            issues.append(
                Issue(
                    line,
                    "error",
                    f"{path}.content is empty or missing",
                    "Provide non-empty text content, or remove/filter empty turns.",
                )
            )
        if role == "assistant" and last_role not in {"user", "tool", "ipython"}:
            issues.append(
                Issue(
                    line,
                    "error",
                    f"assistant message at {path} appears before an expected user/tool/ipython message",
                    "Start each conversation with optional system then user, or fix missing/misordered turns.",
                )
            )
        if role == "user" and last_role == "user":
            issues.append(
                Issue(
                    line,
                    "error",
                    f"consecutive user messages at {container}[{index - 1}] and {path}",
                    "Merge adjacent user turns or insert the missing assistant response.",
                )
            )
        if role == "system" and index > 0:
            issues.append(
                Issue(
                    line,
                    "error",
                    f"system message at {path} is not first",
                    "Move the system prompt to index 0 or use new_system_prompt to replace per-row prompts.",
                )
            )
        if role in {"tool", "ipython"} and not last_ipython:
            issues.append(
                Issue(
                    line,
                    "error",
                    f"tool/ipython message at {path} does not follow an assistant tool call",
                    "Keep tool returns immediately after an assistant tool-call message with ipython/tool-call metadata.",
                )
            )
        last_role = role if isinstance(role, str) else "invalid"
        last_ipython = bool(message.get("ipython")) or role == "assistant" and bool(message.get("tool_calls"))
    return issues


def validate_sharegpt_messages(messages: Any, line: int, container: str, image_tag: str | None) -> list[Issue]:
    issues: list[Issue] = []
    if not isinstance(messages, list):
        return [Issue(line, "error", f"{container} must be a list", "Store ShareGPT conversations as a JSON list.")]
    converted: list[dict[str, Any]] = []
    first_user_text = None
    for index, message in enumerate(messages):
        path = f"{container}[{index}]"
        if not isinstance(message, dict):
            issues.append(Issue(line, "error", f"{path} is not an object", "Use objects with from and value fields."))
            continue
        raw_role = message.get("from")
        if raw_role not in VALID_SHAREGPT_ROLES:
            issues.append(
                Issue(
                    line,
                    "error",
                    f"{path}.from={raw_role!r} is not supported by ShareGPTToMessages",
                    "Map roles to system, human, or gpt, or use OpenAI message style with conversation_style=openai.",
                )
            )
        value = message.get("value")
        if not isinstance(value, str) or value == "":
            issues.append(
                Issue(line, "error", f"{path}.value is empty or not a string", "Provide non-empty text in the value field.")
            )
        role = {"system": "system", "human": "user", "gpt": "assistant"}.get(raw_role, "invalid")
        if role == "user" and first_user_text is None:
            first_user_text = value if isinstance(value, str) else ""
        converted.append({"role": role, "content": value})
    issues.extend(validate_openai_messages(converted, line, container))
    if image_tag and first_user_text is not None and image_tag not in first_user_text:
        issues.append(
            Issue(
                line,
                "warning",
                f"first user message does not contain image_tag {image_tag!r}",
                "Add the placeholder where the image should appear, or pass image_tag=None to prepend images.",
            )
        )
    return issues


def validate_input_output(row: dict[str, Any], line: int, args: argparse.Namespace) -> list[Issue]:
    issues: list[Issue] = []
    for key_name, key_value in [("input", args.input_key), ("output", args.output_key)]:
        if key_value not in row:
            issues.append(
                Issue(
                    line,
                    "error",
                    f"missing {key_name} column {key_value!r}",
                    f"Set the correct --{key_name}-key or update column_map.{key_name} in the torchtune config.",
                )
            )
        elif not isinstance(row[key_value], str) or row[key_value] == "":
            issues.append(
                Issue(line, "error", f"{key_value!r} must be a non-empty string", "Filter empty rows or convert values to strings.")
            )
    return issues


def validate_preference(row: dict[str, Any], line: int, args: argparse.Namespace) -> list[Issue]:
    issues: list[Issue] = []
    chosen = row.get(args.chosen_key)
    rejected = row.get(args.rejected_key)
    if args.chosen_key not in row:
        issues.append(
            Issue(
                line,
                "error",
                f"missing chosen column {args.chosen_key!r}",
                "Set --chosen-key or map column_map.chosen to the raw chosen conversation column.",
            )
        )
    if args.rejected_key not in row:
        issues.append(
            Issue(
                line,
                "error",
                f"missing rejected column {args.rejected_key!r}",
                "Set --rejected-key or map column_map.rejected to the raw rejected conversation column.",
            )
        )
    if args.chosen_key in row:
        issues.extend(validate_openai_messages(chosen, line, args.chosen_key))
    if args.rejected_key in row:
        issues.extend(validate_openai_messages(rejected, line, args.rejected_key))
    if (
        args.require_matching_preference_prompts
        and isinstance(chosen, list)
        and isinstance(rejected, list)
        and normalized_prompt_prefix(chosen) != normalized_prompt_prefix(rejected)
    ):
        issues.append(
            Issue(
                line,
                "warning",
                "chosen and rejected prompt prefixes differ before the final assistant response",
                "Ensure both branches share the same prompt context; only the preferred/rejected answer should differ for standard DPO data.",
            )
        )
    return issues


def validate_image(row: dict[str, Any], line: int, args: argparse.Namespace) -> list[Issue]:
    issues: list[Issue] = []
    if not args.image_key:
        return issues
    if args.image_key not in row:
        return [
            Issue(
                line,
                "error",
                f"missing image column {args.image_key!r}",
                "Set --image-key to the raw image column or remove multimodal image validation for text-only rows.",
            )
        ]
    image_value = row[args.image_key]
    if not isinstance(image_value, str) or image_value == "":
        return [Issue(line, "error", f"image column {args.image_key!r} must be a non-empty string path or URL", "Fix or filter this row.")]
    if args.check_image_paths and not is_url(image_value):
        image_path = Path(image_value)
        if not image_path.is_absolute():
            image_path = args.image_root / image_path
        if not image_path.exists():
            issues.append(
                Issue(
                    line,
                    "error",
                    f"image path does not exist: {image_value}",
                    "Place the image under --image-root, correct the row path, or set image_dir consistently in the torchtune config.",
                )
            )
    return issues


def detect_shape(row: dict[str, Any], args: argparse.Namespace) -> str | None:
    if args.messages_key in row:
        return "messages"
    if args.conversations_key in row:
        return "conversations"
    if args.chosen_key in row or args.rejected_key in row:
        return "chosen-rejected"
    if args.input_key in row or args.output_key in row:
        return "input-output"
    return None


def validate_row(row: Any, line: int, args: argparse.Namespace) -> tuple[str | None, list[Issue]]:
    if not isinstance(row, dict):
        return None, [Issue(line, "error", "row is not a JSON object", "Use one JSON object per line.")]
    shape = args.shape if args.shape != "auto" else detect_shape(row, args)
    if shape is None:
        return None, [
            Issue(
                line,
                "error",
                "could not detect a supported shape",
                "Use messages, conversations, input/output, or chosen/rejected columns, or pass explicit key options.",
            )
        ]
    issues: list[Issue] = []
    if shape == "messages":
        if args.messages_key not in row:
            issues.append(Issue(line, "error", f"missing messages column {args.messages_key!r}", "Set --messages-key correctly."))
        else:
            issues.extend(validate_openai_messages(row[args.messages_key], line, args.messages_key))
    elif shape == "conversations":
        if args.conversations_key not in row:
            issues.append(Issue(line, "error", f"missing conversations column {args.conversations_key!r}", "Set --conversations-key correctly."))
        else:
            issues.extend(validate_sharegpt_messages(row[args.conversations_key], line, args.conversations_key, args.image_tag))
    elif shape == "input-output":
        issues.extend(validate_input_output(row, line, args))
    elif shape == "chosen-rejected":
        issues.extend(validate_preference(row, line, args))
    issues.extend(validate_image(row, line, args))
    return shape, issues


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                yield line_number, json.loads(stripped), None
            except json.JSONDecodeError as error:
                yield line_number, None, Issue(
                    line_number,
                    "error",
                    f"invalid JSON: {error.msg}",
                    "Fix the JSON syntax on this line; JSONL requires one complete JSON object per line.",
                )


def main() -> int:
    args = parse_args()
    if not args.jsonl.exists():
        print(f"error: file does not exist: {args.jsonl}", file=sys.stderr)
        return 2
    if not args.jsonl.is_file():
        print(f"error: not a file: {args.jsonl}", file=sys.stderr)
        return 2

    issues: list[Issue] = []
    shape_counts: dict[str, int] = {}
    rows = 0
    for line_number, row, parse_issue in iter_jsonl(args.jsonl):
        if parse_issue is not None:
            issues.append(parse_issue)
            rows += 1
        else:
            shape, row_issues = validate_row(row, line_number, args)
            rows += 1
            if shape is not None:
                shape_counts[shape] = shape_counts.get(shape, 0) + 1
            issues.extend(row_issues)
        if args.max_lines is not None and rows >= args.max_lines:
            break

    if rows == 0:
        issues.append(Issue(0, "error", "file contains no non-empty JSONL rows", "Add one JSON object per line."))

    for issue in issues:
        print(issue.format(), file=sys.stderr if issue.level == "error" else sys.stdout)

    error_count = sum(issue.level == "error" for issue in issues)
    warning_count = sum(issue.level == "warning" for issue in issues)
    shape_summary = ", ".join(f"{name}={count}" for name, count in sorted(shape_counts.items())) or "none"
    print(f"validated_rows={rows} shapes={shape_summary} errors={error_count} warnings={warning_count}")
    if args.train_on_input != "unspecified":
        masking = "prompt tokens may contribute to loss" if args.train_on_input == "true" else "prompt tokens should be masked from loss"
        print(f"train_on_input={args.train_on_input}: {masking}; inspect tokenized labels to confirm.")

    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
