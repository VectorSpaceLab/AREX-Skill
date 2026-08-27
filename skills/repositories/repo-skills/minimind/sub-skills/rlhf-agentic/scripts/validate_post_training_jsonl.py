#!/usr/bin/env python3
"""Validate MiniMind DPO, RLAIF, and Agentic RL JSONL fixtures.

This bundled helper is intentionally lightweight: it performs schema checks only,
does not import MiniMind source modules, does not download data/models, and does
not launch training. Use it before expensive post-training jobs.

Examples:
  python scripts/validate_post_training_jsonl.py --input-file dpo.jsonl --schema dpo
  python scripts/validate_post_training_jsonl.py --input-file agent_rl.jsonl --schema agent-rl --require-tools
  python scripts/validate_post_training_jsonl.py data.jsonl --schema auto --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ALLOWED_ROLES = {"system", "user", "assistant", "tool"}


def parse_json_maybe(value: Any, label: str, errors: list[str], line_no: int) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return value
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: {label} string is not valid JSON: {exc.msg}")
            return None
    return value


def first_user(messages: list[dict[str, Any]]) -> str | None:
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content")
            return content if isinstance(content, str) else None
    return None


def validate_messages(messages: Any, label: str, errors: list[str], warnings: list[str], line_no: int) -> list[dict[str, Any]]:
    if not isinstance(messages, list) or not messages:
        errors.append(f"line {line_no}: {label} must be a non-empty list of messages")
        return []
    normalized: list[dict[str, Any]] = []
    for idx, msg in enumerate(messages):
        where = f"line {line_no}: {label}[{idx}]"
        if not isinstance(msg, dict):
            errors.append(f"{where} must be an object")
            continue
        role = msg.get("role")
        if role not in ALLOWED_ROLES:
            errors.append(f"{where}.role must be one of {sorted(ALLOWED_ROLES)}, got {role!r}")
        content = msg.get("content", "")
        if content is not None and not isinstance(content, str):
            errors.append(f"{where}.content must be a string when present")
        if "tools" in msg:
            tools = parse_json_maybe(msg.get("tools"), f"{label}[{idx}].tools", errors, line_no)
            if tools is not None and not isinstance(tools, list):
                errors.append(f"{where}.tools must parse to a list")
        if "tool_calls" in msg:
            calls = parse_json_maybe(msg.get("tool_calls"), f"{label}[{idx}].tool_calls", errors, line_no)
            if calls is not None and not isinstance(calls, list):
                errors.append(f"{where}.tool_calls must parse to a list")
        normalized.append(msg)
    if not any(m.get("role") == "user" for m in normalized):
        warnings.append(f"line {line_no}: {label} has no user message")
    return normalized


def validate_tool_definitions(messages: list[dict[str, Any]], errors: list[str], warnings: list[str], line_no: int, require_tools: bool) -> None:
    found = False
    for msg in messages:
        if msg.get("role") != "system" or "tools" not in msg:
            continue
        tools = parse_json_maybe(msg.get("tools"), "system.tools", errors, line_no)
        if not isinstance(tools, list):
            continue
        found = True
        for i, tool in enumerate(tools):
            where = f"line {line_no}: tools[{i}]"
            if not isinstance(tool, dict):
                errors.append(f"{where} must be an object")
                continue
            if tool.get("type") != "function":
                errors.append(f"{where}.type should be 'function'")
            fn = tool.get("function")
            if not isinstance(fn, dict):
                errors.append(f"{where}.function must be an object")
                continue
            if not isinstance(fn.get("name"), str) or not fn.get("name"):
                errors.append(f"{where}.function.name must be a non-empty string")
            params = fn.get("parameters", {})
            if not isinstance(params, dict):
                errors.append(f"{where}.function.parameters must be an object")
            elif params.get("type") != "object":
                errors.append(f"{where}.function.parameters.type should be 'object'")
            required = params.get("required", []) if isinstance(params, dict) else []
            if required is not None and not isinstance(required, list):
                errors.append(f"{where}.function.parameters.required must be a list when present")
    if require_tools and not found:
        errors.append(f"line {line_no}: agent-rl schema requires system tools but none were found")
    elif not found:
        warnings.append(f"line {line_no}: no system tools found; tool-use reward will not validate tool names/args")


def detect_schema(record: dict[str, Any]) -> str | None:
    if "chosen" in record or "rejected" in record:
        return "dpo"
    if "conversations" in record and "gt" in record:
        return "agent-rl"
    if "conversations" in record:
        return "rlaif"
    return None


def validate_record(record: dict[str, Any], schema: str, line_no: int, require_tools: bool) -> tuple[list[str], list[str], str | None]:
    errors: list[str] = []
    warnings: list[str] = []
    detected = detect_schema(record)
    effective = detected if schema == "auto" else schema
    if effective is None:
        errors.append(f"line {line_no}: cannot detect schema; expected chosen/rejected or conversations")
        return errors, warnings, detected
    if schema != "auto" and detected and detected != schema:
        warnings.append(f"line {line_no}: forced schema {schema!r} but record looks like {detected!r}")

    if effective == "dpo":
        if "conversations" in record:
            warnings.append(f"line {line_no}: DPO record also has conversations; ensure this is intentional")
        chosen = validate_messages(record.get("chosen"), "chosen", errors, warnings, line_no)
        rejected = validate_messages(record.get("rejected"), "rejected", errors, warnings, line_no)
        if chosen and not any(m.get("role") == "assistant" and (m.get("content") or m.get("tool_calls")) for m in chosen):
            errors.append(f"line {line_no}: chosen side needs an assistant response")
        if rejected and not any(m.get("role") == "assistant" and (m.get("content") or m.get("tool_calls")) for m in rejected):
            errors.append(f"line {line_no}: rejected side needs an assistant response")
        if first_user(chosen) and first_user(rejected) and first_user(chosen) != first_user(rejected):
            warnings.append(f"line {line_no}: first user message differs between chosen and rejected")

    elif effective == "rlaif":
        if "chosen" in record or "rejected" in record:
            errors.append(f"line {line_no}: RLAIF schema must not contain chosen/rejected")
        if "gt" in record:
            warnings.append(f"line {line_no}: gt is ignored by plain RLAIF; use agent-rl for verifier/tool reward")
        conv = validate_messages(record.get("conversations"), "conversations", errors, warnings, line_no)
        if conv:
            last = conv[-1]
            if last.get("role") == "assistant" and str(last.get("content", "")).strip():
                warnings.append(f"line {line_no}: final assistant content is substantive; PPO/GRPO will generate online instead of training that text")
            if last.get("role") != "assistant":
                warnings.append(f"line {line_no}: final message is not an assistant placeholder")

    elif effective == "agent-rl":
        conv = validate_messages(record.get("conversations"), "conversations", errors, warnings, line_no)
        gt = record.get("gt")
        if not isinstance(gt, list):
            errors.append(f"line {line_no}: agent-rl gt must be a list of scalar targets")
        else:
            for i, item in enumerate(gt):
                if isinstance(item, (dict, list)) or item is None:
                    errors.append(f"line {line_no}: gt[{i}] should be a scalar string/number/bool, got {type(item).__name__}")
        if conv:
            if conv[-1].get("role") != "assistant":
                warnings.append(f"line {line_no}: final message should usually be an assistant placeholder")
            validate_tool_definitions(conv, errors, warnings, line_no, require_tools=require_tools)

    else:
        errors.append(f"line {line_no}: unsupported schema {effective!r}")
    return errors, warnings, detected


def iter_records(path: Path, max_records: int | None) -> Iterable[tuple[int, dict[str, Any] | None, str | None]]:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if max_records is not None and count >= max_records:
                break
            text = raw.strip()
            if not text:
                continue
            count += 1
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                yield line_no, None, exc.msg
                continue
            if not isinstance(obj, dict):
                yield line_no, None, "record must be a JSON object"
                continue
            yield line_no, obj, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate MiniMind post-training JSONL schemas.")
    parser.add_argument("path", nargs="?", help="JSONL file path. Equivalent to --input-file.")
    parser.add_argument("--input-file", dest="input_file", help="JSONL file path.")
    parser.add_argument("--schema", choices=["auto", "dpo", "rlaif", "agent-rl"], default="auto")
    parser.add_argument("--max-records", type=int, default=None, help="Maximum non-blank records to inspect.")
    parser.add_argument("--require-tools", action="store_true", help="For agent-rl, require system tools definitions.")
    parser.add_argument("--warnings-as-errors", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable summary.")
    args = parser.parse_args(argv)

    input_path = Path(args.input_file or args.path or "")
    if not input_path:
        parser.error("provide a JSONL file via path or --input-file")
    if not input_path.exists():
        print(f"ERROR: input file does not exist: {input_path}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    all_warnings: list[str] = []
    detected_counts: dict[str, int] = {}
    records = 0
    for line_no, record, parse_error in iter_records(input_path, args.max_records):
        records += 1
        if parse_error:
            all_errors.append(f"line {line_no}: {parse_error}")
            continue
        assert record is not None
        errors, warnings, detected = validate_record(record, args.schema, line_no, args.require_tools)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        if detected:
            detected_counts[detected] = detected_counts.get(detected, 0) + 1

    if records == 0:
        all_errors.append("no non-blank JSONL records found")

    failed = bool(all_errors) or (args.warnings_as_errors and bool(all_warnings))
    summary = {
        "ok": not failed,
        "records_checked": records,
        "schema": args.schema,
        "detected_counts": detected_counts,
        "errors": all_errors,
        "warnings": all_warnings,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"checked={records} schema={args.schema} detected={detected_counts}")
        for warning in all_warnings:
            print(f"WARNING: {warning}")
        for error in all_errors:
            print(f"ERROR: {error}")
        print("status=OK" if not failed else "status=FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
