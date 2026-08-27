#!/usr/bin/env python3
"""Validate the structure of a SuperAGI agent/run payload.

This helper checks common fields without contacting SuperAGI services.

Example:
  python validate_agent_payload.py --payload '{"name":"A","goal":["x"],"tools":[]}'
  python validate_agent_payload.py --file payload.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL = {"name", "goal"}
OPTIONAL_LIST_FIELDS = {"instruction", "constraints", "tools"}


def load_payload(args: argparse.Namespace) -> dict:
    if args.file:
        return json.loads(Path(args.file).read_text(encoding="utf-8"))
    if args.payload:
        return json.loads(args.payload)
    raise ValueError("provide --payload or --file")


def ensure_list(value, field: str, errors: list[str], allow_empty: bool = True):
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
    elif not allow_empty and not value:
        errors.append(f"{field} must not be empty")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate common SuperAGI agent/run payload structure")
    parser.add_argument("--payload", help="JSON string to validate")
    parser.add_argument("--file", help="Path to a JSON file to validate")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    try:
        data = load_payload(args)
    except Exception as exc:
        print(f"failed to parse payload: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("payload must be a JSON object", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing required field: {key}")
    if "name" in data and not isinstance(data["name"], str):
        errors.append("name must be a string")
    if "goal" in data:
        ensure_list(data["goal"], "goal", errors, allow_empty=False)
    for field in OPTIONAL_LIST_FIELDS:
        if field in data:
            ensure_list(data[field], field, errors)
    if "schedule" in data and data["schedule"] is not None and not isinstance(data["schedule"], dict):
        errors.append("schedule must be an object or null")
    if "model" in data and data["model"] is not None and not isinstance(data["model"], str):
        errors.append("model must be a string")
    if "tools" in data and isinstance(data.get("tools"), list):
        for i, tool in enumerate(data["tools"]):
            if not isinstance(tool, dict):
                errors.append(f"tools[{i}] must be an object")
                continue
            if "name" not in tool:
                errors.append(f"tools[{i}] missing name")
            elif not isinstance(tool["name"], str):
                errors.append(f"tools[{i}].name must be a string")
    if not data.get("goal"):
        warnings.append("goal is empty; the agent may have no task direction")

    result = {"ok": not errors, "errors": errors, "warnings": warnings, "summary": {"fields": sorted(data)}}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("OK" if result["ok"] else "NOT OK")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
