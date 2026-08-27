#!/usr/bin/env python3
"""Validate Alpaca-style instruction data offline.

The script accepts either:

- a JSON array of records, or
- JSONL / NDJSON with one record per line.

Each record must be an object with the keys:

- instruction
- input
- output

By default, blank ``output`` values are reported as warnings instead of hard
failures because the public Alpaca release contains a small number of blank or
near-blank targets. Use ``--require-nonempty-output`` for a stricter corpus.

Examples:

    python validate_alpaca_data.py alpaca_data.json --expect-count 52002
    python validate_alpaca_data.py my_data.jsonl --preview 2
    python validate_alpaca_data.py my_data.json --strict-keys --require-nonempty-output
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence, Tuple

EXPECTED_KEYS = ("instruction", "input", "output")
DEFAULT_EOS_TOKEN = "</s>"
PROMPT_INPUT = (
    "Below is an instruction that describes a task, paired with an input that provides further context. "
    "Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:"
)
PROMPT_NO_INPUT = (
    "Below is an instruction that describes a task. "
    "Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{instruction}\n\n### Response:"
)


@dataclass
class RowIssue:
    level: str
    row_index: int
    message: str


@dataclass
class ValidationResult:
    row_count: int = 0
    blank_lines: int = 0
    issue_count: int = 0
    warnings: List[RowIssue] = field(default_factory=list)
    errors: List[RowIssue] = field(default_factory=list)
    key_present_counts: dict = field(default_factory=lambda: {key: 0 for key in EXPECTED_KEYS})
    key_nonempty_counts: dict = field(default_factory=lambda: {key: 0 for key in EXPECTED_KEYS})
    key_type_errors: dict = field(default_factory=lambda: {key: 0 for key in EXPECTED_KEYS})
    extra_keys: dict = field(default_factory=dict)
    prompt_branch_counts: dict = field(default_factory=lambda: {"prompt_input": 0, "prompt_no_input": 0})

    @property
    def ok(self) -> bool:
        return not self.errors


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: not valid UTF-8") from exc


def _sniff_format(path: Path, raw: str, cli_format: str) -> str:
    if cli_format != "auto":
        return cli_format
    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    if suffix == ".json":
        return "json"
    stripped = raw.lstrip()
    if stripped.startswith("["):
        return "json"
    if stripped.startswith("{"):
        # Could still be JSONL with the first row starting on the first line.
        # Try JSON first and fall back to JSONL if parsing fails.
        return "auto-json-first"
    return "jsonl"


def _load_json_records(raw: str, source_name: str) -> List[dict]:
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError(f"{source_name}: expected a top-level JSON array")
    records = []
    for idx, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{source_name}: row {idx} is not an object")
        records.append(item)
    return records


def _load_jsonl_records(raw: str, source_name: str) -> Tuple[List[dict], int]:
    records: List[dict] = []
    blank_lines = 0
    for line_no, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            blank_lines += 1
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source_name}: line {line_no} is not valid JSON: {exc.msg}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"{source_name}: line {line_no} is not a JSON object")
        records.append(item)
    return records, blank_lines


def load_records(path: Path, cli_format: str) -> Tuple[List[dict], int, str]:
    raw = _read_text(path)
    mode = _sniff_format(path, raw, cli_format)

    if mode == "json":
        records = _load_json_records(raw, str(path))
        return records, 0, "json"
    if mode == "jsonl":
        records, blank_lines = _load_jsonl_records(raw, str(path))
        return records, blank_lines, "jsonl"
    if mode == "auto-json-first":
        try:
            records = _load_json_records(raw, str(path))
            return records, 0, "json"
        except Exception:
            records, blank_lines = _load_jsonl_records(raw, str(path))
            return records, blank_lines, "jsonl"
    raise ValueError(f"{path}: unsupported format mode {cli_format!r}")


def _trim(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _render_prompt(record: dict) -> Tuple[str, str, str]:
    instruction = str(record.get("instruction", ""))
    input_text = str(record.get("input", ""))
    output_text = str(record.get("output", ""))
    if input_text != "":
        prompt = PROMPT_INPUT.format(instruction=instruction, input=input_text)
        branch = "prompt_input"
    else:
        prompt = PROMPT_NO_INPUT.format(instruction=instruction)
        branch = "prompt_no_input"
    target = f"{output_text}{DEFAULT_EOS_TOKEN}"
    return branch, prompt, target


def validate_records(
    records: Sequence[dict],
    *,
    strict_keys: bool = False,
    require_nonempty_output: bool = False,
) -> ValidationResult:
    result = ValidationResult(row_count=len(records))
    for row_index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            result.errors.append(RowIssue("error", row_index, "row is not an object"))
            continue

        record_keys = set(record)
        extra = sorted(record_keys.difference(EXPECTED_KEYS))
        if extra:
            result.extra_keys[";".join(extra)] = result.extra_keys.get(";".join(extra), 0) + 1
            issue = RowIssue(
                "error" if strict_keys else "warning",
                row_index,
                f"extra keys present: {', '.join(extra)}",
            )
            if strict_keys:
                result.errors.append(issue)
                result.issue_count += 1
            else:
                result.warnings.append(issue)
        for key in EXPECTED_KEYS:
            if key in record:
                result.key_present_counts[key] += 1
            else:
                result.errors.append(RowIssue("error", row_index, f"missing key: {key}"))
                result.issue_count += 1
                continue
            value = record[key]
            if isinstance(value, str):
                if value.strip() != "":
                    result.key_nonempty_counts[key] += 1
            else:
                result.key_type_errors[key] += 1
                result.errors.append(RowIssue("error", row_index, f"key {key!r} is not a string"))
                result.issue_count += 1

        instruction = record.get("instruction")
        if isinstance(instruction, str) and instruction.strip() == "":
            result.errors.append(RowIssue("error", row_index, "instruction is empty"))
            result.issue_count += 1

        output = record.get("output")
        if isinstance(output, str) and output.strip() == "":
            if require_nonempty_output:
                result.errors.append(RowIssue("error", row_index, "output is empty"))
                result.issue_count += 1
            else:
                result.warnings.append(RowIssue("warning", row_index, "output is empty"))

        input_text = record.get("input")
        if isinstance(input_text, str) and input_text != "":
            result.prompt_branch_counts["prompt_input"] += 1
        elif isinstance(input_text, str):
            result.prompt_branch_counts["prompt_no_input"] += 1

    result.issue_count += len(result.warnings)
    return result


def _print_summary(path: Path, source_format: str, result: ValidationResult, expect_count: int | None) -> None:
    print(f"file: {path}")
    print(f"format: {source_format}")
    print(f"rows: {result.row_count}")
    if result.blank_lines:
        print(f"blank_lines: {result.blank_lines}")
    if expect_count is not None:
        print(f"expected_rows: {expect_count}")
        print("count_match: yes" if expect_count == result.row_count else "count_match: no")
    print("key_coverage:")
    for key in EXPECTED_KEYS:
        present = result.key_present_counts[key]
        nonempty = result.key_nonempty_counts[key]
        type_errors = result.key_type_errors[key]
        print(f"  - {key}: present {present}/{result.row_count}, nonempty {nonempty}/{result.row_count}, type_errors {type_errors}")
    if result.extra_keys:
        print("extra_keys:")
        for keyset, count in sorted(result.extra_keys.items()):
            print(f"  - {keyset}: {count}")
    print("prompt_branches:")
    for branch, count in result.prompt_branch_counts.items():
        print(f"  - {branch}: {count}")
    print(f"warnings: {len(result.warnings)}")
    print(f"errors: {len(result.errors)}")


def _print_preview(records: Sequence[dict], preview_count: int, max_chars: int) -> None:
    if preview_count <= 0:
        return
    print("preview:")
    for idx, record in enumerate(records[:preview_count], start=1):
        branch, prompt, target = _render_prompt(record)
        print(f"--- row {idx} ({branch}) ---")
        print("instruction:")
        print(_trim(str(record.get("instruction", "")), max_chars))
        print("input:")
        print(_trim(str(record.get("input", "")), max_chars))
        print("prompt:")
        print(_trim(prompt, max_chars))
        print("target_with_eos:")
        print(_trim(target, max_chars))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to a JSON or JSONL Alpaca-style file.")
    parser.add_argument(
        "--format",
        choices=("auto", "json", "jsonl"),
        default="auto",
        help="Input format. Auto tries JSON first, then JSONL.",
    )
    parser.add_argument(
        "--expect-count",
        type=int,
        default=None,
        help="Fail if the number of parsed rows does not match this value.",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=0,
        help="Print a small Alpaca prompt preview for the first N rows.",
    )
    parser.add_argument(
        "--max-preview-chars",
        type=int,
        default=400,
        help="Truncate preview text after this many characters.",
    )
    parser.add_argument(
        "--strict-keys",
        action="store_true",
        help="Fail when a row contains extra keys beyond instruction/input/output.",
    )
    parser.add_argument(
        "--require-nonempty-output",
        action="store_true",
        help="Fail when output is empty instead of warning.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        records, blank_lines, source_format = load_records(args.path, args.format)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = validate_records(
        records,
        strict_keys=args.strict_keys,
        require_nonempty_output=args.require_nonempty_output,
    )
    result.blank_lines = blank_lines
    _print_summary(args.path, source_format, result, args.expect_count)
    _print_preview(records, args.preview, args.max_preview_chars)

    if args.expect_count is not None and result.row_count != args.expect_count:
        print(
            f"error: expected {args.expect_count} rows but found {result.row_count}",
            file=sys.stderr,
        )
        return 1
    if result.errors:
        for issue in result.errors[:20]:
            print(f"error[row {issue.row_index}]: {issue.message}", file=sys.stderr)
        if len(result.errors) > 20:
            print(f"error: {len(result.errors) - 20} more validation errors omitted", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
