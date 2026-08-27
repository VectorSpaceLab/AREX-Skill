#!/usr/bin/env python3
"""Validate DB-GPT sandbox-shaped requests without starting a service.

This helper performs schema/policy-shaped checks only. It never imports
DB-GPT, starts Uvicorn, contacts a runtime, installs packages, or executes code.
It is intended for a quick local request review and tiny fixture check.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


# This is deliberately a small conservative subset of the runtime's textual
# checks. It is not a security boundary and must not be used to certify code.
_DANGEROUS_MARKERS = {
    "python": (
        "import os",
        "import subprocess",
        "__import__(",
        "eval(",
        "exec(",
        "open(",
        "socket",
        "requests",
        "urllib",
        "remove(",
        "unlink(",
        "delete",
    ),
    "javascript": ("require(", "child_process", "fetch(", "process.exit"),
    "bash": (
        "rm -rf /",
        "rm -rf /*",
        "mkfs.",
        "dd if=",
        "> /dev/sda",
        "curl | bash",
        "wget | sh",
    ),
    "shell": (
        "rm -rf /",
        "rm -rf /*",
        "mkfs.",
        "dd if=",
        "> /dev/sda",
        "curl | bash",
        "wget | sh",
    ),
}

_REQUIRED = {
    "connect": ("user_id", "task_id", "image_type"),
    "configure": ("user_id", "task_id", "config_info"),
    "execute": ("session_id", "code_type", "code_content"),
    "manual": ("session_id", "action"),
    "status": ("session_id",),
    "disconnect": ("user_id", "task_id"),
    "get_file": ("session_id", "file_name"),
}


def _read_payload(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"payload is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def _validate(operation: str, payload: dict[str, Any]) -> list[str]:
    if operation not in _REQUIRED:
        raise ValueError(f"unsupported operation: {operation}")

    errors: list[str] = []
    for key in _REQUIRED[operation]:
        value = payload.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing required field: {key}")

    if operation == "configure" and not isinstance(payload.get("config_info"), dict):
        errors.append("config_info must be an object")

    if operation == "execute":
        language = str(payload.get("code_type", "")).lower()
        code = payload.get("code_content")
        if not isinstance(code, str):
            errors.append("code_content must be a string")
        else:
            markers = _DANGEROUS_MARKERS.get(language, ())
            lowered = code.lower()
            found = [marker for marker in markers if marker.lower() in lowered]
            if found:
                errors.append(
                    "policy-shaped check rejected known marker(s): "
                    + ", ".join(found)
                )

    if operation == "get_file":
        name = payload.get("file_name")
        if isinstance(name, str):
            # Reject absolute and traversal-shaped names; the runtime/backend
            # must still enforce containment because this helper is advisory.
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                errors.append("file_name must be a relative, non-traversing name")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a DB-GPT sandbox request locally; never starts a service "
            "or executes code."
        )
    )
    parser.add_argument(
        "operation",
        choices=sorted(_REQUIRED),
        help="sandbox operation represented by the JSON payload",
    )
    parser.add_argument(
        "--payload",
        help="JSON object; if omitted, read one JSON object from stdin",
    )
    args = parser.parse_args(argv)

    raw = args.payload if args.payload is not None else sys.stdin.read()
    try:
        payload = _read_payload(raw)
        errors = _validate(args.operation, payload)
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 2

    result = {
        "valid": not errors,
        "operation": args.operation,
        "errors": errors,
        "execution": "not performed",
        "network": "not contacted",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
