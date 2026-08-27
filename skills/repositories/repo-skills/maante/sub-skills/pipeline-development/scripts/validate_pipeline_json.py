#!/usr/bin/env python3
"""Validate MaaNTE Pipeline JSON/JSONC files for basic structural issues.

This helper is safe and does not call MaaFramework or launch the game.
Example:
    python sub-skills/pipeline-development/scripts/validate_pipeline_json.py assets/resource/base/pipeline/Fish/Fish.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def strip_jsonc(text: str) -> str:
    out: list[str] = []
    i = 0
    in_str = False
    esc = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def load_jsonc(path: Path) -> Any:
    return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))


def validate_node(node_name: str, node: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(node, dict):
        errors.append(f"{node_name}: node must be an object")
        return errors
    if "recognition" not in node and "action" not in node and "next" not in node:
        errors.append(f"{node_name}: node does not define recognition/action/next")
    if "next" in node and not isinstance(node["next"], list):
        errors.append(f"{node_name}: next must be a list")
    if "next" in node:
        for idx, item in enumerate(node["next"]):
            if not isinstance(item, (str, dict)):
                errors.append(f"{node_name}: next[{idx}] must be string or object")
    if "action" in node and isinstance(node["action"], dict):
        action = node["action"]
        if action.get("type") == "Custom" and "custom_action" not in action and "param" not in action:
            errors.append(f"{node_name}: custom action missing custom_action/custom_action_param fields")
    return errors


def validate_pipeline(path: Path) -> list[str]:
    data = load_jsonc(path)
    if not isinstance(data, dict):
        return ["pipeline root must be an object"]
    errors: list[str] = []
    for name, node in data.items():
        if not isinstance(name, str):
            errors.append("node name must be a string")
            continue
        errors.extend(validate_node(name, node))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline_json", type=Path)
    args = parser.parse_args(argv)
    errors = validate_pipeline(args.pipeline_json)
    if errors:
        print(f"FAIL: {args.pipeline_json}")
        for error in errors:
            print(f"  - {error}")
        return 2
    print(f"OK: {args.pipeline_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
