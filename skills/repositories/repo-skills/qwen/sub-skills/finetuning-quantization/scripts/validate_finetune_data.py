#!/usr/bin/env python3
"""Validate Qwen fine-tuning JSON data without loading a model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_ROLES = {"user", "assistant"}

def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid JSON: {type(exc).__name__}: {exc}"]
    if not isinstance(data, list):
        return ["top-level JSON must be a list of samples"]
    for idx, sample in enumerate(data):
        if not isinstance(sample, dict):
            errors.append(f"sample {idx}: must be an object")
            continue
        conv = sample.get("conversations")
        if not isinstance(conv, list) or not conv:
            errors.append(f"sample {idx}: conversations must be a non-empty list")
            continue
        for turn_idx, turn in enumerate(conv):
            if not isinstance(turn, dict):
                errors.append(f"sample {idx} turn {turn_idx}: must be an object")
                continue
            if turn.get("from") not in VALID_ROLES:
                errors.append(f"sample {idx} turn {turn_idx}: invalid role {turn.get('from')!r}")
            if not isinstance(turn.get("value"), str):
                errors.append(f"sample {idx} turn {turn_idx}: value must be a string")
        if conv and conv[0].get("from") != "user":
            errors.append(f"sample {idx}: first turn should normally be user")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description="Validate Qwen fine-tuning conversation JSON.")
    p.add_argument("data_path", help="Path to the fine-tuning JSON file.")
    p.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = p.parse_args()
    errors = validate(Path(args.data_path).expanduser())
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2, ensure_ascii=False))
    else:
        if errors:
            for err in errors:
                print(f"FAIL: {err}")
        else:
            print("PASS: fine-tuning data looks valid")
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
