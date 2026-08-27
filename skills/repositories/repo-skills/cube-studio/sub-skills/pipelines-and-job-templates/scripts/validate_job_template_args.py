#!/usr/bin/env python3
"""Validate CubeStudio job-template args JSON.

This helper is intentionally standalone and safe:
- it does not import the original repository
- it does not submit jobs or touch the cluster
- it only validates the README-described JSON structure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ALLOWED_TYPES = {
    "int",
    "str",
    "text",
    "bool",
    "enum",
    "float",
    "multiple",
    "date",
    "datetime",
    "file",
    "dict",
    "list",
}

SAMPLE_SPEC: Dict[str, Dict[str, Dict[str, Any]]] = {
    "basic": {
        "input_file_path": {
            "type": "str",
            "label": "输入文件",
            "require": 1,
            "default": "data.csv",
            "placeholder": "path/to/input.csv",
            "describe": "输入数据文件或目录",
            "editable": 1,
        },
        "debug": {
            "type": "bool",
            "label": "调试",
            "require": 0,
            "default": False,
            "describe": "是否输出更多日志",
            "editable": 1,
        },
    },
    "advanced": {
        "mode": {
            "type": "enum",
            "label": "模式",
            "require": 1,
            "choice": ["train", "eval"],
            "item_type": "str",
            "default": "train",
            "describe": "选择任务模式",
            "editable": 1,
        },
        "tags": {
            "type": "list",
            "label": "标签",
            "require": 0,
            "item_type": "str",
            "default": [],
            "describe": "可选标签列表",
            "editable": 1,
        },
    },
}


def load_payload(path: str | None) -> Dict[str, Any]:
    if path in (None, "-"):
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def iter_field_errors(group_name: str, field_name: str, field: Any) -> Iterable[str]:
    prefix = f"{group_name}.{field_name}"
    if not isinstance(field, dict):
        yield f"{prefix}: field must be an object"
        return

    field_type = field.get("type")
    if not isinstance(field_type, str):
        yield f"{prefix}: missing string `type`"
    elif field_type not in ALLOWED_TYPES:
        yield f"{prefix}: unsupported type {field_type!r}"

    label = field.get("label")
    if not isinstance(label, str) or not label.strip():
        yield f"{prefix}: missing non-empty `label`"

    require = field.get("require")
    if require not in (0, 1, True, False):
        yield f"{prefix}: `require` should be 0/1 or bool"

    if field_type in {"enum", "multiple"}:
        choice = field.get("choice")
        if not isinstance(choice, list) or not choice:
            yield f"{prefix}: enum/multiple fields should define a non-empty `choice` list"

    if field_type in {"enum", "multiple", "list"} and "item_type" not in field:
        yield f"{prefix}: list-like fields usually need `item_type`"

    if field_type in {"int", "float"} and "range" in field and not isinstance(field.get("range"), (str, list, tuple)):
        yield f"{prefix}: numeric `range` should be a string or sequence"

    if "default" not in field:
        yield f"{prefix}: missing `default` (allowed, but uncommon)"


def validate(payload: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(payload, dict):
        return ["top-level payload must be an object"], warnings

    if not payload:
        warnings.append("payload is empty")

    for group_name, group in payload.items():
        if not isinstance(group, dict):
            errors.append(f"{group_name}: group must be an object")
            continue
        if not group:
            warnings.append(f"{group_name}: group is empty")
        for field_name, field in group.items():
            for msg in iter_field_errors(group_name, field_name, field):
                if "missing `default`" in msg:
                    warnings.append(msg)
                else:
                    errors.append(msg)
    return errors, warnings


def render_text(errors: List[str], warnings: List[str], payload: Any) -> str:
    lines = []
    lines.append("CubeStudio job-template args validation")
    lines.append(f"status: {'ok' if not errors else 'invalid'}")
    if warnings:
        lines.append("warnings:")
        lines.extend(f"- {w}" for w in warnings)
    if errors:
        lines.append("errors:")
        lines.extend(f"- {e}" for e in errors)
    if isinstance(payload, dict):
        lines.append(f"groups: {len(payload)}")
        lines.append(", ".join(sorted(payload.keys())))
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Path to a job-template args JSON file. Use '-' or omit to read stdin.")
    parser.add_argument("--sample", action="store_true", help="Validate the bundled sample payload instead of reading a file.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    args = parser.parse_args(argv)

    payload = SAMPLE_SPEC if args.sample else load_payload(args.path)
    errors, warnings = validate(payload)
    if args.strict and warnings:
        errors = errors + [f"warning treated as error: {w}" for w in warnings]

    result = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "group_count": len(payload) if isinstance(payload, dict) else None,
        "groups": sorted(payload.keys()) if isinstance(payload, dict) else None,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(errors, warnings, payload))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
