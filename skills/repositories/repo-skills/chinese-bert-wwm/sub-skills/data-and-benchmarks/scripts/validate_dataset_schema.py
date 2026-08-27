#!/usr/bin/env python3
"""Offline schema validator for Chinese-BERT-wwm dataset fixture archives.

The validator intentionally uses only Python standard-library modules.  It does
not download data, open network sockets, mutate archives, train models, or read
anything except the zip file supplied with ``--archive``.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import zipfile
from dataclasses import dataclass
from typing import Callable, Sequence


class SchemaError(Exception):
    """Raised for actionable dataset schema failures."""


@dataclass(frozen=True)
class TaskSpec:
    members: tuple[str, ...]
    validator: Callable[[str, bytes, int], int]


VALID_BINARY_LABELS = {"0", "1"}
VALID_PEOPLEDAILY_TAGS = {
    "O",
    "B-PER",
    "I-PER",
    "B-ORG",
    "I-ORG",
    "B-LOC",
    "I-LOC",
}


def parse_non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer >= 0") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be an integer >= 0")
    return parsed


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Chinese-BERT-wwm fixture zip schemas for ChnSentiCorp, "
            "Weibo, or PeopleDaily without network access."
        )
    )
    parser.add_argument(
        "--task",
        required=True,
        choices=sorted(TASKS),
        help="Dataset task schema to validate.",
    )
    parser.add_argument(
        "--archive",
        required=True,
        help="Path to the zip archive to validate.",
    )
    parser.add_argument(
        "--max-rows",
        type=parse_non_negative_int,
        default=0,
        help=(
            "Validate at most N non-header, non-empty rows per member; "
            "0 scans each member fully."
        ),
    )
    return parser.parse_args(argv)


def decode_text(raw: bytes, member: str) -> str:
    """Decode a text member with encodings seen in common Chinese datasets."""

    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise SchemaError(
        f"{member}: cannot decode as UTF-8/UTF-8-SIG or GB18030; "
        "re-export the member as a supported text encoding"
    )


def ensure_exact_members(zf: zipfile.ZipFile, expected: Sequence[str]) -> None:
    actual = [name for name in zf.namelist() if name]
    actual_set = set(actual)
    expected_set = set(expected)
    missing = sorted(expected_set - actual_set)
    unexpected = sorted(actual_set - expected_set)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append("missing required member(s): " + ", ".join(missing))
        if unexpected:
            details.append("unexpected member(s): " + ", ".join(unexpected))
        raise SchemaError("; ".join(details))


def is_empty_csv_record(row: list[str]) -> bool:
    return not row or all(cell == "" for cell in row)


def validate_binary_text_row(
    *,
    member: str,
    line_label: str,
    row: Sequence[str],
    expected_header: Sequence[str],
    text_column_name: str,
) -> None:
    if len(row) != 2:
        raise SchemaError(
            f"{member}: {line_label} must have exactly 2 columns "
            f"{list(expected_header)!r}, got {len(row)} column(s): {list(row)!r}"
        )
    label, text_value = row
    if label not in VALID_BINARY_LABELS:
        raise SchemaError(
            f"{member}: {line_label} has invalid label {label!r}; expected 0 or 1"
        )
    if not text_value.strip():
        raise SchemaError(f"{member}: {line_label} has empty {text_column_name}")


def validate_chnsenticorp_member(member: str, raw: bytes, max_rows: int) -> int:
    text = decode_text(raw, member)
    lines = text.splitlines()
    if not lines:
        raise SchemaError(f"{member}: file is empty; expected header ['label', 'text_a']")

    header = lines[0].split("\t")
    expected_header = ["label", "text_a"]
    if header != expected_header:
        raise SchemaError(f"{member}: expected header {expected_header!r}, got {header!r}")

    validated = 0
    for line_number, line in enumerate(lines[1:], start=2):
        if not line:
            continue
        row = line.split("\t")
        validate_binary_text_row(
            member=member,
            line_label=f"line {line_number}",
            row=row,
            expected_header=expected_header,
            text_column_name="text_a",
        )
        validated += 1
        if max_rows and validated >= max_rows:
            break

    if validated == 0:
        raise SchemaError(f"{member}: no non-empty data rows found after header")
    return validated


def validate_weibo_member(member: str, raw: bytes, max_rows: int) -> int:
    text = decode_text(raw, member)
    reader = csv.reader(io.StringIO(text, newline=""))
    expected_header = ["label", "review"]
    try:
        header = next(reader)
    except StopIteration as exc:
        raise SchemaError(f"{member}: file is empty; expected header {expected_header!r}") from exc

    if header != expected_header:
        raise SchemaError(f"{member}: expected header {expected_header!r}, got {header!r}")

    validated = 0
    for row in reader:
        if is_empty_csv_record(row):
            continue
        validate_binary_text_row(
            member=member,
            line_label=f"line {reader.line_num}",
            row=row,
            expected_header=expected_header,
            text_column_name="review",
        )
        validated += 1
        if max_rows and validated >= max_rows:
            break

    if validated == 0:
        raise SchemaError(f"{member}: no non-empty data rows found after header")
    return validated


def validate_peopledaily_member(member: str, raw: bytes, max_rows: int) -> int:
    text = decode_text(raw, member)
    validated = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            raise SchemaError(
                f"{member}: line {line_number} must contain exactly one Unicode "
                f"character plus one tag separated by whitespace, got {line!r}"
            )
        char, tag = parts
        if len(char) != 1:
            raise SchemaError(
                f"{member}: line {line_number} character field {char!r} has "
                f"length {len(char)}; expected exactly one Unicode character"
            )
        if tag not in VALID_PEOPLEDAILY_TAGS:
            allowed = ", ".join(sorted(VALID_PEOPLEDAILY_TAGS))
            raise SchemaError(
                f"{member}: line {line_number} has invalid tag {tag!r}; "
                f"allowed tags are {allowed}"
            )
        validated += 1
        if max_rows and validated >= max_rows:
            break

    if validated == 0:
        raise SchemaError(f"{member}: no non-empty tagged rows found")
    return validated


TASKS: dict[str, TaskSpec] = {
    "chnsenticorp": TaskSpec(
        members=("train.tsv", "dev.tsv", "test.tsv"),
        validator=validate_chnsenticorp_member,
    ),
    "weibo": TaskSpec(
        members=("train.csv", "dev.csv", "test.csv"),
        validator=validate_weibo_member,
    ),
    "peopledaily": TaskSpec(
        members=("train.txt", "dev.txt"),
        validator=validate_peopledaily_member,
    ),
}


def validate_archive(task: str, archive_path: str, max_rows: int) -> dict[str, int]:
    spec = TASKS[task]
    counts: dict[str, int] = {}
    try:
        with zipfile.ZipFile(archive_path) as zf:
            ensure_exact_members(zf, spec.members)
            for member in spec.members:
                with zf.open(member) as handle:
                    raw = handle.read()
                counts[member] = spec.validator(member, raw, max_rows)
    except FileNotFoundError as exc:
        raise SchemaError(f"archive not found: {archive_path}") from exc
    except PermissionError as exc:
        raise SchemaError(f"archive is not readable: {archive_path}") from exc
    except zipfile.BadZipFile as exc:
        raise SchemaError(f"not a valid zip archive: {archive_path}: {exc}") from exc
    except OSError as exc:
        raise SchemaError(f"could not read archive {archive_path}: {exc}") from exc
    return counts


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        counts = validate_archive(args.task, args.archive, args.max_rows)
    except SchemaError as exc:
        print(f"schema validation failed: {exc}", file=sys.stderr)
        return 1

    row_summary = ", ".join(f"{member}={count}" for member, count in counts.items())
    scan_mode = "full scan" if args.max_rows == 0 else f"first {args.max_rows} row(s) per member"
    print(f"{args.task}: schema ok ({scan_mode}; validated {row_summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
