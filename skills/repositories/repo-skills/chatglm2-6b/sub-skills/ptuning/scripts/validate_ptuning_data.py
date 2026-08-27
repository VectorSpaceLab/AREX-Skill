#!/usr/bin/env python3
"""Validate ADGEN or multi-turn chat fine-tuning records without loading a model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable


def records(path: Path) -> Iterable[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: JSONL record must be an object")
            yield value
        return
    if isinstance(parsed, dict):
        yield parsed
    elif isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
        yield from parsed
    else:
        raise ValueError(f"{path}: expected a JSON object, list of objects, or JSONL objects")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--format", choices=("auto", "adgen", "chat"), default="auto")
    parser.add_argument("--prompt-column", default=None)
    parser.add_argument("--response-column", default=None)
    parser.add_argument("--history-column", default=None)
    parser.add_argument("--max-records", type=int, default=None)
    args = parser.parse_args()
    if not args.file.is_file():
        print(f"missing data file: {args.file}", file=sys.stderr)
        return 2
    fmt = args.format
    prompt_col = args.prompt_column or ("content" if fmt != "chat" else "prompt")
    response_col = args.response_column or ("summary" if fmt != "chat" else "response")
    history_col = args.history_column or ("history" if fmt == "chat" else None)
    count = 0
    errors: list[str] = []
    history_count = 0
    try:
        for index, record in enumerate(records(args.file), 1):
            if args.max_records is not None and count >= args.max_records:
                break
            count += 1
            if fmt == "auto":
                if "history" in record or "prompt" in record or "response" in record:
                    prompt_col, response_col, history_col = "prompt", "response", "history"
                    fmt = "chat"
                else:
                    prompt_col, response_col, history_col = "content", "summary", None
                    fmt = "adgen"
            for name in (prompt_col, response_col):
                if not isinstance(record.get(name), str) or not record[name].strip():
                    errors.append(f"record {index}: {name!r} must be a non-empty string")
            if history_col is not None and history_col in record:
                history = record[history_col]
                if not isinstance(history, list):
                    errors.append(f"record {index}: {history_col!r} must be a list")
                    continue
                history_count += 1
                for pair_index, pair in enumerate(history):
                    if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(item, str) for item in pair):
                        errors.append(f"record {index}: {history_col}[{pair_index}] must be [query, response] strings")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"invalid data: {exc}", file=sys.stderr)
        return 2
    result = {"format": fmt, "prompt_column": prompt_col, "response_column": response_col, "history_column": history_col, "records": count, "records_with_history": history_count, "errors": len(errors)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
