#!/usr/bin/env python3
"""Validate Qwen OpenAI-style function-calling messages or fine-tune samples."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_ROLES = {"system", "user", "assistant", "function"}


def validate_messages(messages: list[dict]) -> list[str]:
    errors: list[str] = []
    if not any(m.get("role") == "user" for m in messages):
        errors.append("at least one user message is required")
    if messages and messages[0].get("role") == "system":
        body = messages[1:]
    else:
        body = messages
    for i, msg in enumerate(messages):
        role = msg.get("role")
        if role not in VALID_ROLES:
            errors.append(f"message {i}: invalid role {role!r}")
        if role == "function" and (i == 0 or messages[i - 1].get("role") != "assistant"):
            errors.append(f"message {i}: function role must follow assistant")
    # After removing optional system, all complete history before latest user should be user/assistant pairs, with optional function observations after assistant.
    if body and body[-1].get("role") == "function":
        errors.append("last message should not be a bare function observation")
    return errors


def validate_finetune(samples: list[dict]) -> list[str]:
    errors: list[str] = []
    if not isinstance(samples, list):
        return ["fine-tune file must be a list"]
    for si, sample in enumerate(samples):
        conv = sample.get("conversations") if isinstance(sample, dict) else None
        if not isinstance(conv, list):
            errors.append(f"sample {si}: missing conversations list")
            continue
        for ti, turn in enumerate(conv):
            role = turn.get("from") if isinstance(turn, dict) else None
            if role not in {"user", "assistant"}:
                errors.append(f"sample {si} turn {ti}: fine-tune role must be user or assistant, not {role!r}")
            if not isinstance(turn.get("value") if isinstance(turn, dict) else None, str):
                errors.append(f"sample {si} turn {ti}: value must be string")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description="Validate Qwen function-calling messages or ReAct fine-tune samples.")
    p.add_argument("path", help="JSON file containing messages or fine-tune samples.")
    p.add_argument("--mode", choices=["messages", "finetune"], default="messages")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    errors = validate_messages(data) if args.mode == "messages" else validate_finetune(data)
    output = {"ok": not errors, "errors": errors}
    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        if errors:
            for e in errors:
                print(f"FAIL: {e}")
        else:
            print("PASS: Qwen function-calling input looks valid")
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
