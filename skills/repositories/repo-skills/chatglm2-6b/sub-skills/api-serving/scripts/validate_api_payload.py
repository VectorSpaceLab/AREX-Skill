#!/usr/bin/env python3
"""Validate and normalize the simple ChatGLM2-6B API payload without a model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def load_payload(raw: str | None, file: Path | None) -> dict[str, Any]:
    if bool(raw) == bool(file):
        raise ValueError("provide exactly one of --json or --file")
    value = json.loads(raw) if raw else json.loads(file.read_text(encoding="utf-8"))  # type: ignore[union-attr]
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def validate_history(value: Any) -> list[list[str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("history must be a list of [query, response] pairs")
    result: list[list[str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, (list, tuple)) or len(item) != 2 or not all(isinstance(x, str) for x in item):
            raise ValueError(f"history[{index}] must contain exactly two strings")
        result.append([item[0], item[1]])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="JSON payload string")
    parser.add_argument("--file", type=Path, help="Read JSON payload from a file")
    args = parser.parse_args()
    try:
        payload = load_payload(args.json, args.file)
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        history = validate_history(payload.get("history"))
        normalized = {
            "prompt": prompt,
            "history": history,
            "max_length": payload.get("max_length") or 2048,
            "top_p": payload.get("top_p") or 0.7,
            "temperature": payload.get("temperature") or 0.95,
        }
        if not isinstance(normalized["max_length"], int) or normalized["max_length"] <= 0:
            raise ValueError("max_length must be a positive integer")
        for name in ("top_p", "temperature"):
            value = normalized[name]
            if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                raise ValueError(f"{name} must be a number between 0 and 1")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"invalid payload: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(normalized, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
