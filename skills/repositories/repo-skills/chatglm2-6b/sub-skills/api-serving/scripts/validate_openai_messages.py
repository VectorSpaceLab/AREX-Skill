#!/usr/bin/env python3
"""Validate OpenAI-shaped messages and show ChatGLM query/history conversion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROLES = {"user", "assistant", "system"}


def load_request(raw: str | None, file: Path | None) -> dict[str, Any]:
    if bool(raw) == bool(file):
        raise ValueError("provide exactly one of --json or --file")
    value = json.loads(raw) if raw else json.loads(file.read_text(encoding="utf-8"))  # type: ignore[union-attr]
    if not isinstance(value, dict):
        raise ValueError("request must be a JSON object")
    return value


def convert(request: dict[str, Any]) -> dict[str, Any]:
    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list")
    normalized: list[dict[str, str]] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict) or message.get("role") not in ROLES or not isinstance(message.get("content"), str):
            raise ValueError(f"messages[{index}] must have role user|assistant|system and string content")
        normalized.append({"role": message["role"], "content": message["content"]})
    if normalized[-1]["role"] != "user":
        raise ValueError("the last message must have role user")

    query = normalized[-1]["content"]
    previous = normalized[:-1]
    system_content = None
    if previous and previous[0]["role"] == "system":
        system_content = previous.pop(0)["content"]
        query = system_content + query

    history: list[list[str]] = []
    warnings: list[str] = []
    if len(previous) % 2:
        warnings.append("earlier messages have odd length; the repo source ignores the unmatched message")
    for index in range(0, len(previous) - 1, 2):
        user, assistant = previous[index], previous[index + 1]
        if user["role"] == "user" and assistant["role"] == "assistant":
            history.append([user["content"], assistant["content"]])
        else:
            warnings.append(f"messages[{index}:{index + 2}] is not a user/assistant pair and was ignored")
    return {
        "model": request.get("model"),
        "stream": bool(request.get("stream", False)),
        "query": query,
        "system_content": system_content,
        "history": history,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="OpenAI chat-completions JSON request")
    parser.add_argument("--file", type=Path, help="Read request JSON from a file")
    args = parser.parse_args()
    try:
        request = load_request(args.json, args.file)
        result = convert(request)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"invalid messages: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
