#!/usr/bin/env python3
"""Validate MOSS SFT conversation JSON/JSONL schema safely.

This checks structure and marker conventions derived from finetune_moss.py and
SFT_data samples. It does not tokenize, download checkpoints, or run training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TURN_KEYS = ["Human", "Inner Thoughts", "Commands", "Tool Responses", "MOSS"]
MARKERS = {
    "Human": ("<|Human|>:", "<eoh>"),
    "Inner Thoughts": ("<|Inner Thoughts|>:", "<eot>"),
    "Commands": ("<|Commands|>:", "<eoc>"),
    "Tool Responses": ("<|Results|>:", "<eor>"),
    "MOSS": ("<|MOSS|>:", "<eom>"),
}
PLUGIN_COMMANDS = ["Search(", "Calculate(", "Solve(", "Text2Image("]


def iter_records(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return
    if path.suffix == ".jsonl":
        for line_no, line in enumerate(text.splitlines(), 1):
            if line.strip():
                yield line_no, json.loads(line)
    else:
        yield 1, json.loads(text)


def validate_record(record: Dict[str, Any], line_no: int, expect_plugin: bool, max_turns: int) -> List[str]:
    errors: List[str] = []
    for key in ["conversation_id", "meta_instruction", "num_turns", "chat"]:
        if key not in record:
            errors.append(f"line {line_no}: missing top-level key {key}")
    if errors:
        return errors
    if not isinstance(record["chat"], dict):
        return [f"line {line_no}: chat must be an object"]
    try:
        num_turns = int(record["num_turns"])
    except Exception:
        return [f"line {line_no}: num_turns must be an integer or integer-like string"]
    if num_turns < 1:
        errors.append(f"line {line_no}: num_turns must be positive")
    if max_turns and num_turns > max_turns:
        errors.append(f"line {line_no}: num_turns {num_turns} exceeds configured max_turns {max_turns}")

    saw_plugin_command = False
    for idx in range(1, num_turns + 1):
        turn_key = f"turn_{idx}"
        turn = record["chat"].get(turn_key)
        if not isinstance(turn, dict):
            errors.append(f"line {line_no}: missing or non-object {turn_key}")
            continue
        for key in TURN_KEYS:
            value = turn.get(key)
            if not isinstance(value, str):
                errors.append(f"line {line_no}: {turn_key}.{key} missing or not a string")
                continue
            start, end = MARKERS[key]
            if start not in value or end not in value:
                errors.append(f"line {line_no}: {turn_key}.{key} should contain {start!r} and {end!r}")
        command_value = turn.get("Commands", "")
        if any(token in command_value for token in PLUGIN_COMMANDS):
            saw_plugin_command = True
    if expect_plugin and not saw_plugin_command:
        errors.append(f"line {line_no}: --expect-plugin was set but no known plugin command was found")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MOSS SFT conversation JSON/JSONL structure.")
    parser.add_argument("path", help="Conversation .json or .jsonl file to validate.")
    parser.add_argument("--expect-plugin", action="store_true", help="Require at least one Search/Calculate/Solve/Text2Image command.")
    parser.add_argument("--max-turns", type=int, default=0, help="Optional upper bound for num_turns; 0 disables the check.")
    parser.add_argument("--sample-limit", type=int, default=0, help="Validate at most this many records from a JSONL file; 0 means all.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable report.")
    args = parser.parse_args()

    path = Path(args.path).expanduser()
    if not path.exists():
        print(f"missing input file: {path}")
        return 2

    all_errors: List[str] = []
    checked = 0
    try:
        for line_no, record in iter_records(path):
            checked += 1
            all_errors.extend(validate_record(record, line_no, args.expect_plugin, args.max_turns))
            if args.sample_limit and checked >= args.sample_limit:
                break
    except json.JSONDecodeError as exc:
        all_errors.append(f"invalid JSON: {exc}")
    except Exception as exc:
        all_errors.append(f"validation failed: {type(exc).__name__}: {exc}")

    report = {"ok": not all_errors, "path": str(path), "records_checked": checked, "errors": all_errors}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("MOSS SFT schema:", "PASS" if report["ok"] else "FAIL")
        print(f"records checked: {checked}")
        for error in all_errors:
            print("-", error)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
