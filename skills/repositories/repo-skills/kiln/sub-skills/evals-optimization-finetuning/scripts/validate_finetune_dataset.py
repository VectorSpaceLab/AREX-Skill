#!/usr/bin/env python3
"""Validate small JSONL-style Kiln fine-tune dataset exports without provider calls."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VALID_CHAT_ROLES = {"system", "user", "assistant", "tool"}
VALID_VERTEX_ROLES = {"user", "model"}


class ValidationError(Exception):
    pass


def load_jsonl(path: Path, max_lines: int | None) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            if max_lines is not None and len(rows) >= max_lines:
                break
            line = raw_line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"line {line_no}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValidationError(f"line {line_no}: JSONL row must be an object")
            rows.append((line_no, value))
    if not rows:
        raise ValidationError("no non-empty JSONL rows found")
    return rows


def parse_json_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, str):
        raise ValidationError(f"{label}: expected JSON string, got {type(value).__name__}")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{label}: invalid JSON object string: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValidationError(f"{label}: parsed value must be a JSON object")
    return parsed


def validate_tool_call(call: Any, label: str) -> None:
    if not isinstance(call, dict):
        raise ValidationError(f"{label}: tool call must be an object")
    if call.get("type") != "function":
        raise ValidationError(f"{label}: tool call type must be 'function'")
    function = call.get("function")
    if not isinstance(function, dict):
        raise ValidationError(f"{label}: tool call function must be an object")
    name = function.get("name")
    if not isinstance(name, str) or not name:
        raise ValidationError(f"{label}: tool call function.name must be non-empty")
    parse_json_object(function.get("arguments"), f"{label}: function.arguments")


def validate_chat_messages(
    messages: Any,
    *,
    row_label: str,
    allow_empty_content: bool,
) -> tuple[dict[str, Any], bool, bool]:
    if not isinstance(messages, list) or not messages:
        raise ValidationError(f"{row_label}: messages/conversations must be a non-empty list")

    seen_user = False
    assistant_messages: list[dict[str, Any]] = []
    has_tool_activity = False
    seen_tool_call_ids: set[str] = set()

    for index, message in enumerate(messages):
        label = f"{row_label}: message {index}"
        if not isinstance(message, dict):
            raise ValidationError(f"{label}: message must be an object")
        role = message.get("role")
        if role not in VALID_CHAT_ROLES:
            raise ValidationError(f"{label}: invalid role {role!r}")
        content = message.get("content")
        tool_calls = message.get("tool_calls")

        if role == "user":
            seen_user = True
        if role == "assistant":
            assistant_messages.append(message)

        if role == "tool":
            has_tool_activity = True
            tool_call_id = message.get("tool_call_id")
            if tool_call_id is not None and not isinstance(tool_call_id, str):
                raise ValidationError(f"{label}: tool_call_id must be a string when present")
            if content is None or (not allow_empty_content and str(content) == ""):
                raise ValidationError(f"{label}: tool response content must be non-empty")
        elif tool_calls is None:
            if content is None:
                raise ValidationError(f"{label}: content is required when no tool_calls are present")
            if not isinstance(content, str):
                raise ValidationError(f"{label}: content must be a string")
            if not allow_empty_content and role != "assistant" and content == "":
                raise ValidationError(f"{label}: content must be non-empty")
        else:
            if role != "assistant":
                raise ValidationError(f"{label}: only assistant messages may have tool_calls")
            if not isinstance(tool_calls, list) or not tool_calls:
                raise ValidationError(f"{label}: tool_calls must be a non-empty list")
            has_tool_activity = True
            for call_index, call in enumerate(tool_calls):
                validate_tool_call(call, f"{label}: tool call {call_index}")
                if isinstance(call, dict) and isinstance(call.get("id"), str):
                    seen_tool_call_ids.add(call["id"])
            if content is not None and not isinstance(content, str):
                raise ValidationError(f"{label}: assistant tool-call content must be string or null")

    if not seen_user:
        raise ValidationError(f"{row_label}: at least one user message is required")
    if not assistant_messages:
        raise ValidationError(f"{row_label}: at least one assistant message is required")

    for index, message in enumerate(messages):
        if message.get("role") == "tool":
            tool_call_id = message.get("tool_call_id")
            if isinstance(tool_call_id, str) and seen_tool_call_ids and tool_call_id not in seen_tool_call_ids:
                raise ValidationError(
                    f"{row_label}: message {index}: tool_call_id does not match any assistant tool call"
                )

    has_thinking = any(
        isinstance(message.get("content"), str) and "<think>" in message["content"] and "</think>" in message["content"]
        for message in assistant_messages
    ) or len([m for m in assistant_messages if isinstance(m.get("content"), str) and m.get("content", "").strip()]) >= 2

    return assistant_messages[-1], has_tool_activity, has_thinking


def validate_openai_or_hf(row: dict[str, Any], line_no: int, args: argparse.Namespace, key: str) -> dict[str, bool]:
    row_label = f"line {line_no}"
    last_assistant, has_tool_activity, has_thinking = validate_chat_messages(
        row.get(key),
        row_label=row_label,
        allow_empty_content=args.allow_empty_content,
    )
    top_level_tools = row.get("tools")
    if top_level_tools is not None:
        if not isinstance(top_level_tools, list) or not top_level_tools:
            raise ValidationError(f"{row_label}: tools must be a non-empty list when present")
        has_tool_activity = True

    if args.expect_structured_output:
        tool_calls = last_assistant.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            validate_tool_call(tool_calls[0], f"{row_label}: final assistant tool call")
        else:
            parse_json_object(last_assistant.get("content"), f"{row_label}: final assistant content")

    return {"has_tool_activity": has_tool_activity, "has_thinking": has_thinking}


def validate_vertex_parts(parts: Any, label: str) -> tuple[bool, bool, Any]:
    if not isinstance(parts, list) or not parts:
        raise ValidationError(f"{label}: parts must be a non-empty list")
    has_tool_activity = False
    has_thinking = False
    final_payload: Any = None
    for part_index, part in enumerate(parts):
        part_label = f"{label}: part {part_index}"
        if not isinstance(part, dict):
            raise ValidationError(f"{part_label}: part must be an object")
        keys = {key for key in ("text", "functionCall", "functionResponse") if key in part}
        if len(keys) != 1:
            raise ValidationError(f"{part_label}: expected exactly one of text/functionCall/functionResponse")
        if "text" in part:
            text = part["text"]
            if not isinstance(text, str):
                raise ValidationError(f"{part_label}: text must be a string")
            has_thinking = has_thinking or ("<think>" in text and "</think>" in text)
            final_payload = text
        elif "functionCall" in part:
            has_tool_activity = True
            call = part["functionCall"]
            if not isinstance(call, dict):
                raise ValidationError(f"{part_label}: functionCall must be an object")
            if not isinstance(call.get("name"), str) or not call.get("name"):
                raise ValidationError(f"{part_label}: functionCall.name must be non-empty")
            if not isinstance(call.get("args"), dict):
                raise ValidationError(f"{part_label}: functionCall.args must be an object")
            final_payload = call.get("args")
        else:
            has_tool_activity = True
            response = part["functionResponse"]
            if not isinstance(response, dict):
                raise ValidationError(f"{part_label}: functionResponse must be an object")
            if not isinstance(response.get("name"), str) or not response.get("name"):
                raise ValidationError(f"{part_label}: functionResponse.name must be non-empty")
            if not isinstance(response.get("response"), dict):
                raise ValidationError(f"{part_label}: functionResponse.response must be an object")
            final_payload = response.get("response")
    return has_tool_activity, has_thinking, final_payload


def validate_vertex(row: dict[str, Any], line_no: int, args: argparse.Namespace) -> dict[str, bool]:
    row_label = f"line {line_no}"
    system = row.get("systemInstruction")
    if not isinstance(system, dict):
        raise ValidationError(f"{row_label}: systemInstruction must be an object")
    if system.get("role") != "system":
        raise ValidationError(f"{row_label}: systemInstruction.role must be 'system'")
    validate_vertex_parts(system.get("parts"), f"{row_label}: systemInstruction")

    contents = row.get("contents")
    if not isinstance(contents, list) or not contents:
        raise ValidationError(f"{row_label}: contents must be a non-empty list")

    seen_user = False
    seen_model = False
    has_tool_activity = bool(row.get("tools"))
    has_thinking = False
    final_model_payload: Any = None
    nonzero_model_text_messages = 0

    for index, content in enumerate(contents):
        label = f"{row_label}: content {index}"
        if not isinstance(content, dict):
            raise ValidationError(f"{label}: content must be an object")
        role = content.get("role")
        parts = content.get("parts")
        part_tools, part_thinking, final_payload = validate_vertex_parts(parts, label)
        has_tool_activity = has_tool_activity or part_tools
        has_thinking = has_thinking or part_thinking
        if role is None:
            if not part_tools:
                raise ValidationError(f"{label}: role is required unless content only carries tool responses")
        elif role not in VALID_VERTEX_ROLES:
            raise ValidationError(f"{label}: invalid Vertex role {role!r}")
        elif role == "user":
            seen_user = True
        elif role == "model":
            seen_model = True
            final_model_payload = final_payload
            if any(isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"].strip() for part in parts):
                nonzero_model_text_messages += 1

    if not seen_user:
        raise ValidationError(f"{row_label}: at least one user content is required")
    if not seen_model:
        raise ValidationError(f"{row_label}: at least one model content is required")
    has_thinking = has_thinking or nonzero_model_text_messages >= 2

    if args.expect_structured_output:
        if isinstance(final_model_payload, dict):
            pass
        else:
            parse_json_object(final_model_payload, f"{row_label}: final model text")

    return {"has_tool_activity": has_tool_activity, "has_thinking": has_thinking}


def detect_format(row: dict[str, Any]) -> str:
    if "messages" in row:
        messages = row.get("messages")
        if isinstance(messages, list) and any(isinstance(m, dict) and m.get("tool_calls") for m in messages):
            return "openai-toolcall"
        return "openai-chat"
    if "conversations" in row:
        conversations = row.get("conversations")
        if isinstance(conversations, list) and any(isinstance(m, dict) and m.get("tool_calls") for m in conversations):
            return "huggingface-toolcall"
        return "huggingface-chat"
    if "systemInstruction" in row and "contents" in row:
        return "vertex-gemini"
    return "unknown"


def validate_row(row: dict[str, Any], line_no: int, args: argparse.Namespace) -> tuple[str, dict[str, bool]]:
    fmt = args.format
    if fmt == "auto":
        fmt = detect_format(row)
    if fmt in {"openai-chat", "openai-toolcall"}:
        flags = validate_openai_or_hf(row, line_no, args, "messages")
    elif fmt in {"huggingface-chat", "huggingface-toolcall"}:
        flags = validate_openai_or_hf(row, line_no, args, "conversations")
    elif fmt == "vertex-gemini":
        flags = validate_vertex(row, line_no, args)
    else:
        raise ValidationError(f"line {line_no}: could not detect dataset format")

    if args.require_tools and not flags["has_tool_activity"]:
        raise ValidationError(f"line {line_no}: expected tool definitions or tool-call activity")
    if args.require_thinking and not flags["has_thinking"]:
        raise ValidationError(f"line {line_no}: expected thinking/intermediate training data")
    return fmt, flags


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate small Kiln fine-tune JSONL dataset exports without imports, network, or provider calls."
    )
    parser.add_argument("path", type=Path, help="JSONL file to validate")
    parser.add_argument(
        "--format",
        choices=[
            "auto",
            "openai-chat",
            "openai-toolcall",
            "huggingface-chat",
            "huggingface-toolcall",
            "vertex-gemini",
        ],
        default="auto",
        help="Expected row format; auto detects from top-level keys",
    )
    parser.add_argument(
        "--expect-structured-output",
        action="store_true",
        help="Require final assistant/model output to be a JSON object or final tool-call arguments object",
    )
    parser.add_argument(
        "--require-tools",
        action="store_true",
        help="Require each row to include tool definitions, tool calls, or Vertex function parts",
    )
    parser.add_argument(
        "--require-thinking",
        action="store_true",
        help="Require thinking/intermediate training data, either as a <think> block or multiple assistant/model text turns",
    )
    parser.add_argument(
        "--allow-empty-content",
        action="store_true",
        help="Allow empty string content in messages where the provider format may tolerate it",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=None,
        help="Validate only the first N non-empty JSONL rows",
    )
    parser.add_argument(
        "--summary-json",
        action="store_true",
        help="Print machine-readable summary JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_lines is not None and args.max_lines < 1:
        parser.error("--max-lines must be >= 1")
    if not args.path.exists():
        parser.error(f"file does not exist: {args.path}")
    if not args.path.is_file():
        parser.error(f"path is not a file: {args.path}")

    errors: list[str] = []
    formats: dict[str, int] = {}
    rows_validated = 0
    rows_with_tools = 0
    rows_with_thinking = 0

    try:
        rows = load_jsonl(args.path, args.max_lines)
    except ValidationError as exc:
        errors.append(str(exc))
        rows = []

    for line_no, row in rows:
        try:
            fmt, flags = validate_row(row, line_no, args)
            formats[fmt] = formats.get(fmt, 0) + 1
            rows_validated += 1
            rows_with_tools += int(flags["has_tool_activity"])
            rows_with_thinking += int(flags["has_thinking"])
        except ValidationError as exc:
            errors.append(str(exc))
            if len(errors) >= 20:
                break

    summary = {
        "ok": not errors,
        "rows_validated": rows_validated,
        "formats": formats,
        "rows_with_tools": rows_with_tools,
        "rows_with_thinking": rows_with_thinking,
        "errors": errors,
    }

    if args.summary_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif errors:
        print("FAIL: fine-tune dataset validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    else:
        format_summary = ", ".join(f"{key}={value}" for key, value in sorted(formats.items()))
        print(
            f"PASS: validated {rows_validated} row(s); formats: {format_summary or 'none'}; "
            f"rows_with_tools={rows_with_tools}; rows_with_thinking={rows_with_thinking}"
        )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
