#!/usr/bin/env python3
"""Validate the official Qwen-VL finetuning JSON conversation schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _is_box_markup(text: str) -> bool:
    return "<box>" in text and "</box>" in text


def validate_sample(sample: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(sample, dict):
        return [f"sample[{index}] is not an object"]
    if "id" not in sample:
        errors.append(f"sample[{index}] missing id")
    if "conversations" not in sample:
        errors.append(f"sample[{index}] missing conversations")
        return errors
    conversations = sample["conversations"]
    if not isinstance(conversations, list) or not conversations:
        errors.append(f"sample[{index}].conversations must be a non-empty list")
        return errors
    expected = "user"
    for turn_idx, turn in enumerate(conversations):
        if not isinstance(turn, dict):
            errors.append(f"sample[{index}].conversations[{turn_idx}] is not an object")
            continue
        role = turn.get("from")
        value = turn.get("value")
        if role not in {"user", "assistant"}:
            errors.append(
                f"sample[{index}].conversations[{turn_idx}].from must be user or assistant"
            )
        elif role != expected:
            errors.append(
                f"sample[{index}].conversations[{turn_idx}] role order mismatch: expected {expected}, found {role}"
            )
        if not isinstance(value, str) or not value.strip():
            errors.append(f"sample[{index}].conversations[{turn_idx}].value must be a non-empty string")
        if isinstance(value, str) and ("<ref>" in value or "<box>" in value):
            if role != "assistant":
                errors.append(
                    f"sample[{index}].conversations[{turn_idx}] contains grounding markup outside assistant turn"
                )
            if "<ref>" in value and not _is_box_markup(value):
                errors.append(
                    f"sample[{index}].conversations[{turn_idx}] contains <ref> without a matching <box>"
                )
        expected = "assistant" if expected == "user" else "user"
    return errors


def validate_dataset(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, list):
        return ["top-level JSON value must be a list"]
    for idx, sample in enumerate(data):
        errors.extend(validate_sample(sample, idx))
    return errors


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to the finetuning JSON file")
    args = parser.parse_args(argv)

    path = Path(args.data)
    data = _load_json(path)
    errors = validate_dataset(data)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1
    print(f"Validated {len(data)} samples in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
