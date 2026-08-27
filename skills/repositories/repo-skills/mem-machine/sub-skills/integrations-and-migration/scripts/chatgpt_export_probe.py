#!/usr/bin/env python3
"""Local-only probe for ChatGPT/OpenAI-style conversation export JSON files.

The script prints schema/count summaries and small redacted previews. It never
contacts MemMachine and never uploads data.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def redact(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def extract_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(extract_text(item.get("text") or item.get("content") or item.get("parts")))
        return " ".join(p for p in parts if p)
    if isinstance(value, dict):
        for key in ("text", "content", "parts"):
            if key in value:
                return extract_text(value[key])
    return ""


def iter_messages(root: Any):
    # ChatGPT export often uses a list of conversations with mapping nodes.
    conversations = root if isinstance(root, list) else root.get("conversations", []) if isinstance(root, dict) else []
    for conv_index, conv in enumerate(conversations):
        conv_id = conv.get("id") or conv.get("conversation_id") or str(conv_index) if isinstance(conv, dict) else str(conv_index)
        if isinstance(conv, dict) and isinstance(conv.get("mapping"), dict):
            for node in conv["mapping"].values():
                msg = node.get("message") if isinstance(node, dict) else None
                if isinstance(msg, dict):
                    yield conv_id, msg
        elif isinstance(conv, dict) and isinstance(conv.get("messages"), list):
            for msg in conv["messages"]:
                if isinstance(msg, dict):
                    yield conv_id, msg


def summarize(path: Path, preview: int) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    root_type = type(data).__name__
    messages = list(iter_messages(data))
    role_counts: Counter[str] = Counter()
    non_empty = 0
    previews: list[str] = []
    for conv_id, msg in messages:
        author = msg.get("author") if isinstance(msg.get("author"), dict) else {}
        role = author.get("role") or msg.get("role") or "unknown"
        role_counts[str(role)] += 1
        text = extract_text(msg.get("content") or msg)
        if text:
            non_empty += 1
            if len(previews) < 5:
                previews.append(f"conversation={conv_id!r} role={role!r} text={redact(text, preview)!r}")
    print(f"file: {path}")
    print(f"root_type: {root_type}")
    print(f"message_count: {len(messages)}")
    print(f"non_empty_message_count: {non_empty}")
    print(f"role_counts: {dict(role_counts)}")
    if not messages:
        print("warning: no ChatGPT/OpenAI-style messages detected; inspect top-level keys and adapt parser")
    for item in previews:
        print(f"preview: {item}")
    return 0 if messages else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe a local conversation export JSON without uploading it.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--preview-chars", type=int, default=80)
    args = parser.parse_args(argv)
    return summarize(args.path, args.preview_chars)


if __name__ == "__main__":
    raise SystemExit(main())
