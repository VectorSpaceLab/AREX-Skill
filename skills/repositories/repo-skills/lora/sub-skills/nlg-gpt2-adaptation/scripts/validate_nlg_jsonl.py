#!/usr/bin/env python3
"""Validate the small JSONL formats used by the LoRA GPT-2 examples.

This helper checks the stage-specific keys and basic value types for the E2E /
WebNLG / DART formatting pipeline. It does not encode tokens, start training,
or download evaluation tools.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


KINDS = {"text", "tokenized", "prediction", "reference-text"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=sorted(KINDS), required=True)
    parser.add_argument("--input-file", type=Path, required=True)
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"ERROR: {message}")
    return 1


def load_lines(path: Path) -> Iterable[tuple[int, dict]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError(f"line {line_no}: expected JSON object")
            yield line_no, data


def require_keys(data: dict, line_no: int, keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"line {line_no}: missing keys {missing}")


def validate_text(data: dict, line_no: int) -> None:
    require_keys(data, line_no, ["context", "completion"])
    if not isinstance(data["context"], str) or not isinstance(data["completion"], str):
        raise ValueError(f"line {line_no}: context/completion must be strings")


def validate_tokenized(data: dict, line_no: int) -> None:
    require_keys(data, line_no, ["context", "completion"])
    for key in ("context", "completion"):
        value = data[key]
        if not isinstance(value, list) or not all(isinstance(item, int) for item in value):
            raise ValueError(f"line {line_no}: {key} must be a list of integers")


def validate_prediction(data: dict, line_no: int) -> None:
    require_keys(data, line_no, ["id", "predict"])
    if not isinstance(data["id"], int):
        raise ValueError(f"line {line_no}: id must be an integer")
    if not isinstance(data["predict"], list) or not all(isinstance(item, int) for item in data["predict"]):
        raise ValueError(f"line {line_no}: predict must be a list of integers")


def validate_reference_text(data: dict, line_no: int) -> None:
    require_keys(data, line_no, ["context", "completion"])
    if not isinstance(data["context"], str) or not isinstance(data["completion"], str):
        raise ValueError(f"line {line_no}: reference-text records must be strings")


def main() -> int:
    args = parse_args()
    validators = {
        "text": validate_text,
        "tokenized": validate_tokenized,
        "prediction": validate_prediction,
        "reference-text": validate_reference_text,
    }
    try:
        count = 0
        for line_no, data in load_lines(args.input_file):
            validators[args.kind](data, line_no)
            count += 1
    except Exception as exc:
        return fail(str(exc))

    print(json.dumps({"ok": True, "kind": args.kind, "records": count, "file": str(args.input_file)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
