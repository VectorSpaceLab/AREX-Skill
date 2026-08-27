#!/usr/bin/env python3
"""Validate text2vec BGE JSONL triples.

The script is intentionally safe: it imports only the Python standard library,
performs no model or dataset downloads, and prints one JSON summary to stdout.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def open_text(path: Path):
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def add_error(summary: Dict[str, Any], line_no: int, message: str, max_errors: int) -> bool:
    summary["records_invalid"] += 1
    summary["error_count"] += 1
    if len(summary["errors"]) < max_errors:
        summary["errors"].append({"line": line_no, "message": message})
    return summary["error_count"] >= max_errors


def add_warning(summary: Dict[str, Any], message: str) -> None:
    if message not in summary["warnings"]:
        summary["warnings"].append(message)


def validate_string_field(value: Any, field_name: str) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(value, str):
        return None, f"{field_name} must be a string"
    if not value.strip():
        return None, f"{field_name} must be non-empty"
    return value, None


def validate_string_list(value: Any, field_name: str) -> Tuple[Optional[List[str]], Optional[str]]:
    if not isinstance(value, list):
        return None, f"{field_name} must be a list of strings"
    if not value:
        return None, f"{field_name} must be non-empty"
    cleaned: List[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str):
            return None, f"{field_name}[{idx}] must be a string"
        if not item.strip():
            return None, f"{field_name}[{idx}] must be non-empty"
        cleaned.append(item)
    return cleaned, None


def update_min_max(summary: Dict[str, Any], key_prefix: str, value: int) -> None:
    min_key = f"min_{key_prefix}"
    max_key = f"max_{key_prefix}"
    summary[min_key] = value if summary[min_key] is None else min(summary[min_key], value)
    summary[max_key] = value if summary[max_key] is None else max(summary[max_key], value)


def validate_row(
    row: Dict[str, Any],
    line_no: int,
    summary: Dict[str, Any],
    max_errors: int,
    train_group_size: int,
) -> bool:
    query, query_err = validate_string_field(row.get("query"), "query")
    if query_err:
        return add_error(summary, line_no, query_err, max_errors)

    pos, pos_err = validate_string_list(row.get("pos"), "pos")
    if pos_err:
        return add_error(summary, line_no, pos_err, max_errors)

    neg, neg_err = validate_string_list(row.get("neg"), "neg")
    if neg_err:
        return add_error(summary, line_no, neg_err, max_errors)

    assert query is not None and pos is not None and neg is not None
    summary["records_valid"] += 1
    update_min_max(summary, "pos_count", len(pos))
    update_min_max(summary, "neg_count", len(neg))

    needed_negatives = train_group_size - 1
    if len(neg) < needed_negatives:
        summary["rows_needing_negative_duplication"] += 1
        if len(summary["negative_duplication_example_lines"]) < max_errors:
            summary["negative_duplication_example_lines"].append(line_no)

    query_text = query.strip()
    pos_set: Set[str] = {item.strip() for item in pos}
    neg_set: Set[str] = {item.strip() for item in neg}
    overlap = pos_set & neg_set
    if overlap:
        summary["rows_with_pos_neg_overlap"] += 1
        if len(summary["pos_neg_overlap_example_lines"]) < max_errors:
            summary["pos_neg_overlap_example_lines"].append(line_no)
    if query_text in neg_set:
        summary["rows_with_query_in_neg"] += 1
        if len(summary["query_in_neg_example_lines"]) < max_errors:
            summary["query_in_neg_example_lines"].append(line_no)
    if query_text in pos_set:
        summary["rows_with_query_in_pos"] += 1
        if len(summary["query_in_pos_example_lines"]) < max_errors:
            summary["query_in_pos_example_lines"].append(line_no)

    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate BGE JSONL triples for text2vec fine-tuning.")
    parser.add_argument("--input-file", required=True, help="Path to BGE JSONL file, optionally gzipped.")
    parser.add_argument(
        "--train-group-size",
        type=int,
        default=8,
        help="BGE train group size; rows need at least train_group_size - 1 negatives to avoid duplication warnings.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help="Stop after this many validation errors and include up to this many error details.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_errors < 1:
        parser.error("--max-errors must be >= 1")
    if args.train_group_size < 2:
        parser.error("--train-group-size must be >= 2")

    path = Path(args.input_file).expanduser()
    summary: Dict[str, Any] = {
        "ok": False,
        "input_file": str(path),
        "train_group_size": args.train_group_size,
        "records_seen": 0,
        "records_valid": 0,
        "records_invalid": 0,
        "error_count": 0,
        "errors": [],
        "warnings": [],
        "min_pos_count": None,
        "max_pos_count": None,
        "min_neg_count": None,
        "max_neg_count": None,
        "rows_needing_negative_duplication": 0,
        "negative_duplication_example_lines": [],
        "rows_with_pos_neg_overlap": 0,
        "pos_neg_overlap_example_lines": [],
        "rows_with_query_in_pos": 0,
        "query_in_pos_example_lines": [],
        "rows_with_query_in_neg": 0,
        "query_in_neg_example_lines": [],
        "stopped_early": False,
        "max_errors": args.max_errors,
    }

    if not path.is_file():
        add_error(summary, 0, f"input file does not exist: {path}", args.max_errors)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 1

    try:
        with open_text(path) as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                summary["records_seen"] += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    stop = add_error(summary, line_no, f"invalid JSON: {exc.msg}", args.max_errors)
                    if stop:
                        summary["stopped_early"] = True
                        break
                    continue
                if not isinstance(row, dict):
                    stop = add_error(summary, line_no, "JSONL row must be an object", args.max_errors)
                else:
                    stop = validate_row(row, line_no, summary, args.max_errors, args.train_group_size)
                if stop:
                    summary["stopped_early"] = True
                    break
    except UnicodeDecodeError as exc:
        add_error(summary, 0, f"failed to decode input as UTF-8: {exc}", args.max_errors)
    except OSError as exc:
        add_error(summary, 0, f"failed to read input: {exc}", args.max_errors)

    if summary["records_valid"] == 0:
        add_error(summary, 0, "no valid BGE records found", args.max_errors)

    if summary["records_valid"] and summary["rows_needing_negative_duplication"]:
        add_warning(
            summary,
            (
                f"{summary['rows_needing_negative_duplication']} row(s) have fewer negatives than "
                "train_group_size - 1; BgeTrainDataset will repeat negatives before sampling"
            ),
        )
    if summary["records_valid"] and summary["rows_with_pos_neg_overlap"]:
        add_warning(
            summary,
            f"{summary['rows_with_pos_neg_overlap']} row(s) have overlapping positive and negative passages",
        )
    if summary["records_valid"] and summary["rows_with_query_in_neg"]:
        add_warning(
            summary,
            f"{summary['rows_with_query_in_neg']} row(s) include the query text in neg",
        )
    if summary["records_valid"] and summary["rows_with_query_in_pos"]:
        add_warning(
            summary,
            f"{summary['rows_with_query_in_pos']} row(s) include the query text in pos",
        )

    summary["ok"] = summary["error_count"] == 0
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
