#!/usr/bin/env python3
"""Validate MiniMind pretrain/SFT JSONL and optional local tokenizer compatibility.

The validator is intentionally bounded and side-effect safe: it reads local files,
performs no downloads, writes no outputs, and exits non-zero on schema errors.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ALLOWED_ROLES = {"system", "user", "assistant", "tool"}
CORE_TOKENS = {
    "bos_token": "<|im_start|>",
    "eos_token": "<|im_end|>",
    "pad_token": "<|endoftext|>",
    "unk_token": "<|endoftext|>",
}
ADDED_TOKENS = [
    "<tool_call>",
    "</tool_call>",
    "<tool_response>",
    "</tool_response>",
    "<think>",
    "</think>",
]


class Report:
    def __init__(self, strict: bool = False) -> None:
        self.strict = strict
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, line_no: Optional[int], message: str) -> None:
        prefix = f"line {line_no}: " if line_no is not None else ""
        self.errors.append(prefix + message)

    def warn(self, line_no: Optional[int], message: str) -> None:
        prefix = f"line {line_no}: " if line_no is not None else ""
        self.warnings.append(prefix + message)

    def has_failure(self) -> bool:
        return bool(self.errors) or (self.strict and bool(self.warnings))


def _json_loads_field(value: Any, field: str, line_no: int, report: Report) -> Optional[Any]:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            report.error(line_no, f"{field} must be a valid JSON-encoded string: {exc}")
            return None
    report.warn(line_no, f"{field} is {type(value).__name__}; MiniMind training expects a JSON-encoded string")
    return value


def _validate_tool_call(call: Any, line_no: int, index: int, report: Report) -> None:
    if not isinstance(call, dict):
        report.error(line_no, f"tool_calls[{index}] must be an object")
        return

    function_obj = call.get("function") if isinstance(call.get("function"), dict) else None
    name = call.get("name") if function_obj is None else function_obj.get("name")
    arguments = call.get("arguments") if function_obj is None else function_obj.get("arguments")

    if not isinstance(name, str) or not name:
        report.error(line_no, f"tool_calls[{index}] must include a non-empty function name")
    if arguments is None:
        report.error(line_no, f"tool_calls[{index}] must include arguments")
    elif not isinstance(arguments, (dict, str)):
        report.error(line_no, f"tool_calls[{index}].arguments must be an object or JSON string")
    elif isinstance(arguments, str):
        try:
            json.loads(arguments)
        except json.JSONDecodeError:
            report.warn(line_no, f"tool_calls[{index}].arguments is a string but not valid JSON")


def validate_pretrain(obj: Dict[str, Any], line_no: int, report: Report) -> None:
    text = obj.get("text")
    if not isinstance(text, str):
        report.error(line_no, "pretrain sample must contain string field 'text'")
        return
    if not text.strip():
        report.error(line_no, "pretrain field 'text' must not be empty")
    if "conversations" in obj:
        report.warn(line_no, "sample has both 'text' and 'conversations'; choose one schema")


def validate_sft(obj: Dict[str, Any], line_no: int, report: Report) -> Optional[Dict[str, Any]]:
    conversations = obj.get("conversations")
    if not isinstance(conversations, list) or not conversations:
        report.error(line_no, "SFT sample must contain a non-empty 'conversations' list")
        return None

    assistant_count = 0
    tool_count = 0
    decoded_tools: Optional[Any] = None
    normalized_messages: List[Dict[str, Any]] = []

    for idx, message in enumerate(conversations):
        if not isinstance(message, dict):
            report.error(line_no, f"conversations[{idx}] must be an object")
            continue

        role = message.get("role")
        content = message.get("content")
        if role not in ALLOWED_ROLES:
            report.error(line_no, f"conversations[{idx}].role must be one of {sorted(ALLOWED_ROLES)}")
        if not isinstance(content, str):
            report.error(line_no, f"conversations[{idx}].content must be a string")
            content = ""
        elif role == "user" and not content.strip():
            report.warn(line_no, f"conversations[{idx}] has an empty user message")

        norm: Dict[str, Any] = {"role": role, "content": content}

        reasoning = message.get("reasoning_content")
        if reasoning not in (None, ""):
            if role != "assistant":
                report.warn(line_no, f"conversations[{idx}].reasoning_content is normally assistant-only")
            if not isinstance(reasoning, str):
                report.error(line_no, f"conversations[{idx}].reasoning_content must be a string when present")
            else:
                norm["reasoning_content"] = reasoning

        tools_value = message.get("tools")
        if tools_value not in (None, ""):
            if role != "system":
                report.error(line_no, f"conversations[{idx}].tools should be attached to a system message")
            parsed_tools = _json_loads_field(tools_value, f"conversations[{idx}].tools", line_no, report)
            if parsed_tools is not None:
                if not isinstance(parsed_tools, list):
                    report.warn(line_no, f"conversations[{idx}].tools decoded to {type(parsed_tools).__name__}; a list of tool specs is expected")
                decoded_tools = parsed_tools
                norm["tools"] = tools_value

        tool_calls_value = message.get("tool_calls")
        if tool_calls_value not in (None, ""):
            if role != "assistant":
                report.error(line_no, f"conversations[{idx}].tool_calls should be attached to an assistant message")
            parsed_calls = _json_loads_field(tool_calls_value, f"conversations[{idx}].tool_calls", line_no, report)
            if parsed_calls is not None:
                if not isinstance(parsed_calls, list):
                    report.error(line_no, f"conversations[{idx}].tool_calls must decode to a list")
                else:
                    for call_idx, call in enumerate(parsed_calls):
                        _validate_tool_call(call, line_no, call_idx, report)
                    norm["tool_calls"] = parsed_calls

        if role == "assistant":
            assistant_count += 1
            if not content and tool_calls_value in (None, ""):
                report.warn(line_no, f"assistant message {idx} has neither content nor tool_calls")
        elif role == "tool":
            tool_count += 1
            if idx == 0 or conversations[idx - 1].get("role") not in {"assistant", "tool"}:
                report.warn(line_no, f"tool message {idx} is not directly after an assistant/tool message")

        normalized_messages.append(norm)

    if assistant_count == 0:
        report.error(line_no, "SFT sample has no assistant message to supervise")
    if tool_count > 0 and decoded_tools is None:
        report.warn(line_no, "sample has tool role messages but no system.tools definition")

    return {"messages": normalized_messages, "tools": decoded_tools}


def infer_schema(obj: Dict[str, Any], line_no: int, report: Report) -> Optional[str]:
    has_text = "text" in obj
    has_conversations = "conversations" in obj
    if has_text and not has_conversations:
        return "pretrain"
    if has_conversations and not has_text:
        return "sft"
    if has_text and has_conversations:
        report.error(line_no, "cannot auto-detect schema when both 'text' and 'conversations' are present")
    else:
        report.error(line_no, "cannot auto-detect schema; expected 'text' or 'conversations'")
    return None


def iter_jsonl(path: Path, max_lines: int, report: Report) -> Iterable[Tuple[int, Dict[str, Any]]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            seen = 0
            for line_no, raw in enumerate(handle, start=1):
                if max_lines and seen >= max_lines:
                    break
                line = raw.strip()
                if not line:
                    report.warn(line_no, "blank line ignored")
                    continue
                seen += 1
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    report.error(line_no, f"invalid JSON: {exc}")
                    continue
                if not isinstance(obj, dict):
                    report.error(line_no, "each JSONL line must decode to an object")
                    continue
                yield line_no, obj
    except FileNotFoundError:
        report.error(None, f"file not found: {path}")
    except OSError as exc:
        report.error(None, f"could not read {path}: {exc}")


def check_tokenizer(
    tokenizer_dir: Path,
    schema: str,
    samples: List[Dict[str, Any]],
    max_seq_len: Optional[int],
    report: Report,
) -> None:
    try:
        from transformers import AutoTokenizer
    except Exception as exc:  # pragma: no cover - depends on optional environment
        report.error(None, f"transformers is required for tokenizer validation: {exc}")
        return

    try:
        tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir), local_files_only=True)
    except Exception as exc:  # pragma: no cover - depends on local tokenizer files
        report.error(None, f"could not load tokenizer locally from {tokenizer_dir}: {exc}")
        return

    for attr, expected in CORE_TOKENS.items():
        actual = getattr(tokenizer, attr, None)
        if actual != expected:
            report.error(None, f"tokenizer {attr}={actual!r}; expected {expected!r}")

    if len(tokenizer) != 6400:
        report.warn(None, f"tokenizer length is {len(tokenizer)}, expected 6400 for MiniMind default weights")

    if not getattr(tokenizer, "chat_template", None):
        report.error(None, "tokenizer has no chat_template")

    for token in ADDED_TOKENS:
        token_id = tokenizer.convert_tokens_to_ids(token)
        if token_id is None or token_id == tokenizer.unk_token_id:
            report.error(None, f"tokenizer does not contain expected added token {token!r}")

    for sample_idx, sample in enumerate(samples, start=1):
        if schema == "pretrain":
            text = sample.get("text", "")
            ids = tokenizer(str(text), add_special_tokens=False).input_ids
            total_len = len(ids) + 2
            if max_seq_len and total_len > max_seq_len:
                report.warn(None, f"tokenizer sample {sample_idx} pretrain length {total_len} exceeds max_seq_len {max_seq_len}; it will be truncated")
        elif schema == "sft":
            messages = sample["messages"]
            tools = sample.get("tools")
            try:
                rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, tools=tools)
            except Exception as exc:
                report.error(None, f"tokenizer chat_template failed on sample {sample_idx}: {exc}")
                continue
            if "<|im_start|>assistant" not in rendered:
                report.warn(None, f"tokenizer sample {sample_idx} rendered no assistant span")
            if any("tool_calls" in msg for msg in messages) and "<tool_call>" not in rendered:
                report.error(None, f"tokenizer sample {sample_idx} has tool_calls but rendered no <tool_call> block")
            if any(msg.get("role") == "tool" for msg in messages) and "<tool_response>" not in rendered:
                report.error(None, f"tokenizer sample {sample_idx} has tool messages but rendered no <tool_response> block")
            ids = tokenizer(rendered).input_ids
            if max_seq_len and len(ids) > max_seq_len:
                report.warn(None, f"tokenizer sample {sample_idx} SFT length {len(ids)} exceeds max_seq_len {max_seq_len}; it will be truncated")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate MiniMind pretrain/SFT JSONL files.")
    parser.add_argument("jsonl", type=Path, help="Local JSONL file to validate.")
    parser.add_argument("--schema", choices=["auto", "pretrain", "sft"], default="auto", help="Expected MiniMind schema.")
    parser.add_argument("--max-lines", type=int, default=0, help="Validate at most this many non-empty lines; 0 means all lines.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--tokenizer-dir", type=Path, help="Optional local tokenizer directory to check with local_files_only=True.")
    parser.add_argument("--max-seq-len", type=int, help="Warn when tokenized samples exceed this length.")
    parser.add_argument("--tokenizer-samples", type=int, default=3, help="Number of valid samples to render/tokenize when --tokenizer-dir is set.")
    args = parser.parse_args(argv)

    if args.max_lines < 0:
        parser.error("--max-lines must be non-negative")
    if args.max_seq_len is not None and args.max_seq_len <= 0:
        parser.error("--max-seq-len must be positive")
    if args.tokenizer_samples < 0:
        parser.error("--tokenizer-samples must be non-negative")

    report = Report(strict=args.strict)
    expected_schema = None if args.schema == "auto" else args.schema
    counts = {"pretrain": 0, "sft": 0}
    tokenizer_samples: List[Dict[str, Any]] = []

    for line_no, obj in iter_jsonl(args.jsonl, args.max_lines, report):
        schema = expected_schema or infer_schema(obj, line_no, report)
        if schema is None:
            continue
        if expected_schema is None:
            expected_schema = schema
        elif schema != expected_schema:
            report.error(line_no, f"schema mismatch: detected {schema}, expected {expected_schema}")
            continue

        if schema == "pretrain":
            validate_pretrain(obj, line_no, report)
            counts["pretrain"] += 1
            if len(tokenizer_samples) < args.tokenizer_samples:
                tokenizer_samples.append(obj)
        elif schema == "sft":
            normalized = validate_sft(obj, line_no, report)
            counts["sft"] += 1
            if normalized and len(tokenizer_samples) < args.tokenizer_samples:
                tokenizer_samples.append(normalized)

    if counts["pretrain"] + counts["sft"] == 0 and not report.errors:
        report.error(None, "no JSONL samples were validated")

    if args.tokenizer_dir and expected_schema:
        check_tokenizer(args.tokenizer_dir, expected_schema, tokenizer_samples, args.max_seq_len, report)

    print("MiniMind JSONL validation summary")
    print(f"  file: {args.jsonl}")
    print(f"  schema: {expected_schema or args.schema}")
    print(f"  pretrain samples: {counts['pretrain']}")
    print(f"  sft samples: {counts['sft']}")
    print(f"  warnings: {len(report.warnings)}")
    print(f"  errors: {len(report.errors)}")

    for warning in report.warnings[:20]:
        print(f"WARNING: {warning}", file=sys.stderr)
    if len(report.warnings) > 20:
        print(f"WARNING: ... {len(report.warnings) - 20} more warnings suppressed", file=sys.stderr)

    for error in report.errors[:50]:
        print(f"ERROR: {error}", file=sys.stderr)
    if len(report.errors) > 50:
        print(f"ERROR: ... {len(report.errors) - 50} more errors suppressed", file=sys.stderr)

    if report.has_failure():
        if args.strict and report.warnings and not report.errors:
            print("Strict mode treats warnings as failures.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
