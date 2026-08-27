#!/usr/bin/env python3
"""Validate local JSON artifacts used by Mem0 CLI workflows.

This helper is read-only and never contacts Mem0.

Examples:
  mem0 --agent status | python validate_cli_json.py agent-envelope -
  python validate_cli_json.py import-file memories.json
  python validate_cli_json.py messages conversation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """Raised when JSON does not match the expected local contract."""


def _read_json(path: str) -> Any:
    if path == "-":
        raw = sys.stdin.read()
        source = "stdin"
    else:
        raw = Path(path).read_text(encoding="utf-8")
        source = path
    if not raw.strip():
        raise ValidationError(f"{source}: empty input")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{source}: invalid JSON: {exc}") from exc


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _assert_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value


def validate_agent_envelope(value: Any) -> dict[str, Any]:
    obj = _assert_object(value, "agent envelope")
    status = obj.get("status")
    if status not in {"success", "error"}:
        raise ValidationError("agent envelope .status must be 'success' or 'error'")
    if not _is_nonempty_string(obj.get("command")):
        raise ValidationError("agent envelope .command must be a non-empty string")
    if "data" not in obj:
        raise ValidationError("agent envelope must include .data, even when null")
    if status == "error" and not _is_nonempty_string(obj.get("error")):
        raise ValidationError("error envelope must include a non-empty .error string")
    if "duration_ms" in obj and not isinstance(obj["duration_ms"], int):
        raise ValidationError(".duration_ms must be an integer when present")
    if "count" in obj and not isinstance(obj["count"], int):
        raise ValidationError(".count must be an integer when present")
    if "scope" in obj and obj["scope"] is not None and not isinstance(obj["scope"], dict):
        raise ValidationError(".scope must be an object or null when present")
    return {"kind": "agent-envelope", "status": status, "command": obj["command"]}


def validate_memory_item(value: Any, label: str = "memory item") -> dict[str, Any]:
    obj = _assert_object(value, label)
    memory_id = obj.get("id") or obj.get("memory_id")
    text = obj.get("memory") or obj.get("text") or obj.get("content") or obj.get("data")
    if memory_id is not None and not isinstance(memory_id, str):
        raise ValidationError(f"{label} id/memory_id must be a string when present")
    if text is not None and not isinstance(text, (str, int, float, bool, dict, list)):
        raise ValidationError(f"{label} content field has unsupported type")
    if "score" in obj and obj["score"] is not None and not isinstance(obj["score"], (int, float)):
        raise ValidationError(f"{label} score must be numeric when present")
    if "categories" in obj and obj["categories"] is not None and not isinstance(obj["categories"], (list, str)):
        raise ValidationError(f"{label} categories must be a list or string when present")
    if "metadata" in obj and obj["metadata"] is not None and not isinstance(obj["metadata"], dict):
        raise ValidationError(f"{label} metadata must be an object when present")
    return obj


def validate_raw_list(value: Any) -> dict[str, Any]:
    if not isinstance(value, list):
        raise ValidationError("raw list output must be a JSON array")
    for index, item in enumerate(value):
        validate_memory_item(item, f"raw list item {index}")
    return {"kind": "raw-list", "count": len(value)}


def validate_import_file(value: Any) -> dict[str, Any]:
    items = value if isinstance(value, list) else [value]
    if not isinstance(items, list):
        raise ValidationError("import input must be an object or array")
    valid = 0
    missing_content = 0
    for index, item in enumerate(items):
        obj = _assert_object(item, f"import item {index}")
        content = obj.get("memory") or obj.get("text") or obj.get("content")
        if not _is_nonempty_string(content):
            missing_content += 1
        else:
            valid += 1
        for key in ("user_id", "agent_id", "app_id", "run_id"):
            if key in obj and obj[key] is not None and not isinstance(obj[key], str):
                raise ValidationError(f"import item {index}.{key} must be a string when present")
        if "metadata" in obj and obj["metadata"] is not None and not isinstance(obj["metadata"], dict):
            raise ValidationError(f"import item {index}.metadata must be an object when present")
    if valid == 0:
        raise ValidationError("import file contains no items with memory/text/content")
    return {"kind": "import-file", "items": len(items), "validContentItems": valid, "missingContentItems": missing_content}


def validate_messages(value: Any) -> dict[str, Any]:
    if not isinstance(value, list):
        raise ValidationError("messages JSON must be an array")
    for index, item in enumerate(value):
        obj = _assert_object(item, f"message {index}")
        if not _is_nonempty_string(obj.get("role")):
            raise ValidationError(f"message {index}.role must be a non-empty string")
        if not _is_nonempty_string(obj.get("content")):
            raise ValidationError(f"message {index}.content must be a non-empty string")
    return {"kind": "messages", "count": len(value)}


def validate_config(value: Any) -> dict[str, Any]:
    obj = _assert_object(value, "config")
    if "version" in obj and not isinstance(obj["version"], int):
        raise ValidationError("config.version must be an integer when present")
    defaults = obj.get("defaults", {})
    platform = obj.get("platform", {})
    if defaults is not None and not isinstance(defaults, dict):
        raise ValidationError("config.defaults must be an object")
    if platform is not None and not isinstance(platform, dict):
        raise ValidationError("config.platform must be an object")
    for key in ("user_id", "agent_id", "app_id", "run_id"):
        if isinstance(defaults, dict) and key in defaults and defaults[key] is not None and not isinstance(defaults[key], str):
            raise ValidationError(f"config.defaults.{key} must be a string when present")
    for key in ("api_key", "base_url", "user_email", "created_via", "agent_caller", "claimed_at", "default_user_id"):
        if isinstance(platform, dict) and key in platform and platform[key] is not None and not isinstance(platform[key], str):
            raise ValidationError(f"config.platform.{key} must be a string when present")
    if isinstance(platform, dict) and "agent_mode" in platform and not isinstance(platform["agent_mode"], bool):
        raise ValidationError("config.platform.agent_mode must be a boolean when present")
    return {"kind": "config", "hasApiKey": bool(isinstance(platform, dict) and platform.get("api_key"))}


def validate_add_result(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and "results" in value:
        results = value["results"]
    else:
        results = value
    if isinstance(results, dict):
        results = [results]
    if not isinstance(results, list):
        raise ValidationError("add result must be an object, results object, or results array")
    for index, item in enumerate(results):
        obj = validate_memory_item(item, f"add result {index}")
        if "status" in obj and obj["status"] is not None and not isinstance(obj["status"], str):
            raise ValidationError(f"add result {index}.status must be a string when present")
        if obj.get("event_id") is not None and not isinstance(obj.get("event_id"), str):
            raise ValidationError(f"add result {index}.event_id must be a string when present")
    return {"kind": "add-result", "count": len(results)}


def run_validation(kind: str, value: Any) -> dict[str, Any]:
    validators = {
        "agent-envelope": validate_agent_envelope,
        "raw-list": validate_raw_list,
        "import-file": validate_import_file,
        "messages": validate_messages,
        "config": validate_config,
        "add-result": validate_add_result,
    }
    return validators[kind](value)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate local JSON used by Mem0 CLI workflows. Reads only files/stdin; no network or credentials required."
    )
    parser.add_argument(
        "kind",
        choices=["agent-envelope", "raw-list", "import-file", "messages", "config", "add-result"],
        help="JSON contract to validate.",
    )
    parser.add_argument("path", help="Path to JSON file, or '-' for stdin.")
    parser.add_argument("--quiet", action="store_true", help="Print nothing on success.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        value = _read_json(args.path)
        summary = run_validation(args.kind, value)
    except (OSError, ValidationError) as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(json.dumps({"valid": True, **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
