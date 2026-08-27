#!/usr/bin/env python3
"""Validate small local DPO/KTO preference dataset fixtures.

The checker is deterministic and local-only: it does not import Axolotl, load
models, download datasets, write outputs, or train. Use it before Axolotl
preprocessing to catch common record-shape mistakes.

Examples:
  python scripts/check_preference_dataset.py --mode dpo --input sample.jsonl
  python scripts/check_preference_dataset.py --mode kto --input sample.jsonl \
      --prompt-field question --completion-field answer --label-field is_good
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

TRUE_STRINGS = {"1", "true", "yes", "y", "desirable", "good", "positive", "chosen"}
FALSE_STRINGS = {"0", "false", "no", "n", "undesirable", "bad", "negative", "rejected"}


class ValidationIssue:
    def __init__(self, record_number: int, severity: str, message: str) -> None:
        self.record_number = record_number
        self.severity = severity
        self.message = message

    def format(self) -> str:
        prefix = f"record {self.record_number}" if self.record_number else "input"
        return f"{self.severity.upper()}: {prefix}: {self.message}"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate small local JSON/JSONL records for Axolotl DPO-style "
            "chosen/rejected data or KTO prompt/completion/label data."
        )
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=("dpo", "kto"),
        help="Validation mode: dpo for paired chosen/rejected rows, kto for unpaired labeled completions.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a JSON or JSONL file. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--prompt-field",
        default="prompt",
        help="Prompt field name or dotted path used with --require-prompt and KTO checks. Default: prompt.",
    )
    parser.add_argument(
        "--messages-field",
        default="messages",
        help="DPO chat-history field accepted as prompt context when --require-prompt is set. Default: messages.",
    )
    parser.add_argument(
        "--chosen-field",
        default="chosen",
        help="DPO chosen response field name or dotted path. Default: chosen.",
    )
    parser.add_argument(
        "--rejected-field",
        default="rejected",
        help="DPO rejected response field name or dotted path. Default: rejected.",
    )
    parser.add_argument(
        "--completion-field",
        default="completion",
        help="KTO completion field name or dotted path. Default: completion.",
    )
    parser.add_argument(
        "--label-field",
        default="label",
        help="KTO binary label field name or dotted path. Default: label.",
    )
    parser.add_argument(
        "--require-prompt",
        action="store_true",
        help="Require a prompt/messages field in DPO mode or prompt field in KTO mode.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        help="Validate at most this many records; 0 means all records. Default: 0.",
    )
    parser.add_argument(
        "--allow-identical-pairs",
        action="store_true",
        help="Do not warn when DPO chosen and rejected values normalize to the same text.",
    )
    return parser.parse_args(argv)


def read_text(input_path: str) -> str:
    if input_path == "-":
        return sys.stdin.read()
    path = Path(input_path)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"ERROR: cannot read {input_path!r}: {error}") from error


def load_records(text: str) -> tuple[list[dict[str, Any]], str]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("input is empty")

    if stripped[0] in "[{":
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as json_error:
            return load_jsonl_records(text)
        if isinstance(parsed, list):
            records = parsed
        elif isinstance(parsed, dict):
            records = [parsed]
        else:
            raise ValueError("JSON input must be an object, a list of objects, or JSONL objects")
        return ensure_record_objects(records), "json"

    return load_jsonl_records(text)


def load_jsonl_records(text: str) -> tuple[list[dict[str, Any]], str]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"line {line_number} is not valid JSON: {error.msg}") from error
        if not isinstance(parsed, dict):
            raise ValueError(f"line {line_number} must be a JSON object")
        records.append(parsed)
    if not records:
        raise ValueError("JSONL input contains no records")
    return records, "jsonl"


def ensure_record_objects(records: list[Any]) -> list[dict[str, Any]]:
    checked: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"record {index} must be a JSON object")
        checked.append(record)
    if not checked:
        raise ValueError("input contains no records")
    return checked


def field_exists(record: dict[str, Any], field_path: str) -> bool:
    exists, _ = get_field(record, field_path)
    return exists


def get_field(record: dict[str, Any], field_path: str) -> tuple[bool, Any]:
    if field_path in record:
        return True, record[field_path]

    current: Any = record
    for part in field_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def normalize_value(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.split())
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def parse_binary_label(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, float) and value in (0.0, 1.0):
        return bool(int(value))
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in TRUE_STRINGS:
            return True
        if lowered in FALSE_STRINGS:
            return False
    return None


def validate_dpo_record(record: dict[str, Any], record_number: int, args: argparse.Namespace) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    chosen_exists, chosen = get_field(record, args.chosen_field)
    rejected_exists, rejected = get_field(record, args.rejected_field)

    if not chosen_exists:
        issues.append(ValidationIssue(record_number, "error", f"missing chosen field {args.chosen_field!r}"))
    elif not is_non_empty(chosen):
        issues.append(ValidationIssue(record_number, "error", f"chosen field {args.chosen_field!r} is empty"))

    if not rejected_exists:
        issues.append(ValidationIssue(record_number, "error", f"missing rejected field {args.rejected_field!r}"))
    elif not is_non_empty(rejected):
        issues.append(ValidationIssue(record_number, "error", f"rejected field {args.rejected_field!r} is empty"))

    if args.require_prompt:
        has_prompt = field_exists(record, args.prompt_field) or field_exists(record, args.messages_field)
        if not has_prompt:
            issues.append(
                ValidationIssue(
                    record_number,
                    "error",
                    f"missing prompt context: expected {args.prompt_field!r} or {args.messages_field!r}",
                )
            )

    if (
        chosen_exists
        and rejected_exists
        and is_non_empty(chosen)
        and is_non_empty(rejected)
        and not args.allow_identical_pairs
        and normalize_value(chosen) == normalize_value(rejected)
    ):
        issues.append(
            ValidationIssue(
                record_number,
                "warning",
                "chosen and rejected normalize to identical values; verify preference polarity",
            )
        )

    if "completion" in record and not (chosen_exists and rejected_exists):
        issues.append(
            ValidationIssue(
                record_number,
                "warning",
                "record has completion but lacks a complete chosen/rejected pair; KTO may be the better mode",
            )
        )

    return issues


def validate_kto_record(record: dict[str, Any], record_number: int, args: argparse.Namespace) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if args.require_prompt:
        prompt_exists, prompt = get_field(record, args.prompt_field)
        if not prompt_exists:
            issues.append(ValidationIssue(record_number, "error", f"missing prompt field {args.prompt_field!r}"))
        elif not is_non_empty(prompt):
            issues.append(ValidationIssue(record_number, "error", f"prompt field {args.prompt_field!r} is empty"))

    completion_exists, completion = get_field(record, args.completion_field)
    if not completion_exists:
        issues.append(ValidationIssue(record_number, "error", f"missing completion field {args.completion_field!r}"))
    elif not is_non_empty(completion):
        issues.append(ValidationIssue(record_number, "error", f"completion field {args.completion_field!r} is empty"))

    label_exists, label = get_field(record, args.label_field)
    if not label_exists:
        issues.append(ValidationIssue(record_number, "error", f"missing label field {args.label_field!r}"))
    elif parse_binary_label(label) is None:
        issues.append(
            ValidationIssue(
                record_number,
                "error",
                f"label field {args.label_field!r} must be binary; got {label!r}",
            )
        )

    has_chosen = field_exists(record, args.chosen_field)
    has_rejected = field_exists(record, args.rejected_field)
    if has_chosen and has_rejected and not completion_exists:
        issues.append(
            ValidationIssue(
                record_number,
                "warning",
                "record has chosen/rejected but no completion; DPO/ORPO/SimPO may be the better mode",
            )
        )

    return issues


def validate_records(records: Iterable[dict[str, Any]], args: argparse.Namespace) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for index, record in enumerate(records, start=1):
        if args.max_records and index > args.max_records:
            break
        if args.mode == "dpo":
            issues.extend(validate_dpo_record(record, index, args))
        else:
            issues.extend(validate_kto_record(record, index, args))
    return issues


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.max_records < 0:
        print("ERROR: --max-records must be >= 0", file=sys.stderr)
        return 2

    try:
        records, input_format = load_records(read_text(args.input))
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    checked_count = len(records) if args.max_records == 0 else min(len(records), args.max_records)
    issues = validate_records(records, args)
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]

    for issue in issues:
        print(issue.format(), file=sys.stderr)

    if errors:
        print(
            f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s) across {checked_count} checked {input_format} record(s).",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: checked {checked_count} {input_format} record(s) for {args.mode.upper()} shape; {len(warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
