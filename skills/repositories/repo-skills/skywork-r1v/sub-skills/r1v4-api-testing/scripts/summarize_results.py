#!/usr/bin/env python3
"""Summarize Skywork R1V4 batch result JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line_num, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                records.append(
                    {
                        "line_num": line_num,
                        "parse_error": f"invalid JSON: {exc}",
                        "raw_line": line.rstrip("\n"),
                    }
                )
                continue
            records.append(record)
    return records


def _record_image(record: Dict[str, Any]) -> str:
    image = record.get("image")
    if isinstance(image, str):
        return image
    input_block = record.get("input")
    if isinstance(input_block, dict):
        maybe_image = input_block.get("image")
        if isinstance(maybe_image, str):
            return maybe_image
    return ""


def _record_response_block(record: Dict[str, Any]) -> Dict[str, Any]:
    response = record.get("response")
    if isinstance(response, dict):
        return response
    raw_response = record.get("raw_response")
    if isinstance(raw_response, dict):
        return raw_response
    if isinstance(record.get("parsed_response"), dict):
        return record["parsed_response"]
    return {}


def _extract_full_response(record: Dict[str, Any]) -> str:
    response = _record_response_block(record)
    for key in ("full_response", "content", "answer"):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value

    nested = response.get("raw_response")
    if isinstance(nested, dict):
        for key in ("full_response", "content", "answer"):
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                return value

    value = record.get("full_response")
    if isinstance(value, str) and value.strip():
        return value
    return ""


def _has_error(record: Dict[str, Any]) -> bool:
    response = _record_response_block(record)
    if isinstance(response.get("error"), str):
        return True
    if isinstance(record.get("parse_error"), str):
        return True
    return False


def summarize_results(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    success = 0
    error = 0
    with_image = 0
    text_only = 0
    response_lengths: List[int] = []

    for record in records:
        image = _record_image(record)
        if image:
            with_image += 1
        else:
            text_only += 1

        full_response = _extract_full_response(record)
        if full_response:
            response_lengths.append(len(full_response))

        if _has_error(record) or not full_response:
            error += 1
        else:
            success += 1

    average_length = None
    if response_lengths:
        average_length = sum(response_lengths) / len(response_lengths)

    return {
        "total": total,
        "success": success,
        "error": error,
        "with_image": with_image,
        "text_only": text_only,
        "responses_with_length": len(response_lengths),
        "average_response_length_chars": average_length,
    }


def _print_human(summary: Dict[str, Any]) -> None:
    print(f"Total: {summary['total']}")
    print(f"Success: {summary['success']}")
    print(f"Error: {summary['error']}")
    print(f"With image: {summary['with_image']}")
    print(f"Text only: {summary['text_only']}")
    if summary["average_response_length_chars"] is None:
        print("Average response length: n/a")
    else:
        print(
            "Average response length: "
            f"{summary['average_response_length_chars']:.2f} chars"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize Skywork R1V4 batch result JSONL files.",
    )
    parser.add_argument("--input", required=True, help="Path to a result JSONL file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the summary as JSON.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional file path for the summary JSON.",
    )
    args = parser.parse_args()

    records = _load_jsonl(args.input)
    summary = summarize_results(records)

    if args.output:
        Path(args.output).write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.json or args.output:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_human(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
