#!/usr/bin/env python3
"""Validate text2vec text-matching / CoSENT TSV or JSONL training data.

The script is intentionally safe: it imports only the Python standard library,
performs no model or dataset downloads, and prints one JSON summary to stdout.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PAIR_SCHEMAS: Tuple[Tuple[str, str, str], ...] = (
    ("text1", "text2", "text1/text2"),
    ("sentence1", "sentence2", "sentence1/sentence2"),
)


def detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    suffixes = [s.lower() for s in path.suffixes]
    if suffixes and suffixes[-1] == ".gz":
        suffixes = suffixes[:-1]
    if suffixes and suffixes[-1] in {".jsonl", ".json", ".ndjson"}:
        return "jsonl"
    return "tsv"


def open_text(path: Path):
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def finite_float(value: Any) -> Tuple[Optional[float], Optional[str]]:
    if value is None:
        return None, "missing label"
    if isinstance(value, str) and not value.strip():
        return None, "empty label"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"label is not numeric: {value!r}"
    if not math.isfinite(number):
        return None, f"label is not finite: {value!r}"
    return number, None


def is_integer_like(value: float) -> bool:
    return abs(value - round(value)) <= 1e-9


def normalize_text(value: Any) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(value, str):
        return None, f"text value is not a string: {type(value).__name__}"
    if not value.strip():
        return None, "text value is empty"
    return value, None


def classify_json_schema(row: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    """Return text_a_key, text_b_key, schema_name, ambiguous."""
    complete: List[Tuple[str, str, str]] = []
    for a_key, b_key, schema_name in PAIR_SCHEMAS:
        if a_key in row and b_key in row:
            complete.append((a_key, b_key, schema_name))
    if not complete:
        return None, None, None, False
    ambiguous = len(complete) > 1
    # Loader precedence is text1/text2, then sentence1/sentence2.
    chosen = complete[0]
    return chosen[0], chosen[1], chosen[2], ambiguous


def add_error(summary: Dict[str, Any], line_no: int, message: str, max_errors: int) -> bool:
    summary["records_invalid"] += 1
    summary["error_count"] += 1
    if len(summary["errors"]) < max_errors:
        summary["errors"].append({"line": line_no, "message": message})
    return summary["error_count"] >= max_errors


def add_warning(summary: Dict[str, Any], message: str) -> None:
    if message not in summary["warnings"]:
        summary["warnings"].append(message)


def record_label(summary: Dict[str, Any], label: float) -> None:
    stats = summary["label_stats"]
    stats["count"] += 1
    stats["min"] = label if stats["min"] is None else min(stats["min"], label)
    stats["max"] = label if stats["max"] is None else max(stats["max"], label)
    if is_integer_like(label):
        stats["integer_like_count"] += 1
    else:
        stats["non_integer_count"] += 1
    if label in (0.0, 1.0):
        stats["binary_label_count"] += 1


def validate_jsonl_line(
    line: str,
    line_no: int,
    summary: Dict[str, Any],
    max_errors: int,
) -> bool:
    try:
        row = json.loads(line)
    except json.JSONDecodeError as exc:
        return add_error(summary, line_no, f"invalid JSON: {exc.msg}", max_errors)

    if not isinstance(row, dict):
        return add_error(summary, line_no, "JSONL row must be an object", max_errors)

    a_key, b_key, schema_name, ambiguous = classify_json_schema(row)
    if a_key is None or b_key is None or schema_name is None:
        return add_error(
            summary,
            line_no,
            "missing complete text pair; expected text1/text2 or sentence1/sentence2",
            max_errors,
        )

    summary["schema_counts"][schema_name] = summary["schema_counts"].get(schema_name, 0) + 1
    if ambiguous:
        summary["ambiguous_schema_rows"] += 1

    text_a, err_a = normalize_text(row.get(a_key))
    text_b, err_b = normalize_text(row.get(b_key))
    if err_a:
        return add_error(summary, line_no, f"{a_key}: {err_a}", max_errors)
    if err_b:
        return add_error(summary, line_no, f"{b_key}: {err_b}", max_errors)

    label, label_err = finite_float(row.get("label"))
    if label_err:
        return add_error(summary, line_no, label_err, max_errors)

    record_label(summary, label)
    summary["records_valid"] += 1
    return False


def validate_tsv_line(
    line: str,
    line_no: int,
    summary: Dict[str, Any],
    max_errors: int,
) -> bool:
    parts = line.split("\t")
    if len(parts) != 3:
        return add_error(
            summary,
            line_no,
            f"TSV row must have exactly 3 tab-separated fields, got {len(parts)}",
            max_errors,
        )
    text_a, text_b, raw_label = parts
    if not text_a.strip():
        return add_error(summary, line_no, "first text field is empty", max_errors)
    if not text_b.strip():
        return add_error(summary, line_no, "second text field is empty", max_errors)
    label, label_err = finite_float(raw_label)
    if label_err:
        lowered = [p.strip().lower() for p in parts]
        if line_no == 1 and lowered in (["text1", "text2", "label"], ["sentence1", "sentence2", "label"]):
            label_err += "; TSV headers are not supported by the package loaders"
        return add_error(summary, line_no, label_err, max_errors)
    summary["schema_counts"]["tsv"] = summary["schema_counts"].get("tsv", 0) + 1
    record_label(summary, label)
    summary["records_valid"] += 1
    return False


def finalize_hints(summary: Dict[str, Any], task: str, input_path: Path) -> None:
    stats = summary["label_stats"]
    if stats["count"] == 0:
        add_error(summary, 0, "no valid records with numeric labels found", summary["max_errors"])
        return

    label_min = stats["min"]
    label_max = stats["max"]
    has_non_binary = stats["binary_label_count"] < stats["count"]
    looks_like_sts = label_min is not None and label_max is not None and 0 <= label_min and label_max <= 5 and has_non_binary
    path_triggers_sts = "STS" in str(input_path).upper()

    summary["sts_hint"] = {
        "looks_like_sts_range": bool(looks_like_sts),
        "path_contains_STS": bool(path_triggers_sts),
        "loader_train_conversion": "int(score > 2.5) when local train-file path contains STS",
    }

    if task == "text-matching" and stats["non_integer_count"]:
        add_warning(
            summary,
            "text-matching loaders cast labels with int(label); non-integer labels will be truncated unless STS conversion applies first",
        )
    if task == "text-matching" and has_non_binary:
        add_warning(
            summary,
            "non-binary labels require a matching num_classes for SentenceBert/BertMatch or intentional STS binary conversion",
        )
    if looks_like_sts and path_triggers_sts:
        add_warning(
            summary,
            "labels look like STS scores and the path contains STS; local train loaders will binarize with score > 2.5",
        )
    elif looks_like_sts and task == "text-matching":
        add_warning(
            summary,
            "labels look like STS scores but the path does not contain STS; local text-matching train loaders will not auto-binarize",
        )
    elif looks_like_sts and task == "cosent" and path_triggers_sts:
        add_warning(
            summary,
            "CoSENT local-file loader also applies the STS filename heuristic; rename or custom-load if raw scores are required",
        )

    if label_min is not None and label_max is not None and (label_min < 0 or label_max > 5):
        add_warning(
            summary,
            "labels fall outside the common 0/1 or 0-5 STS ranges; verify label semantics and class count",
        )
    if summary["ambiguous_schema_rows"]:
        add_warning(
            summary,
            "some JSONL rows contain both text1/text2 and sentence1/sentence2; loader precedence uses text1/text2",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate text2vec TSV/JSONL data for text-matching or CoSENT training."
    )
    parser.add_argument("--input-file", required=True, help="Path to TSV, JSONL, or gzipped TSV/JSONL file.")
    parser.add_argument(
        "--format",
        choices=("auto", "jsonl", "tsv"),
        default="auto",
        help="Input format. auto selects JSONL for .json/.jsonl/.ndjson and TSV otherwise.",
    )
    parser.add_argument(
        "--task",
        choices=("text-matching", "cosent"),
        default="text-matching",
        help="Target loader family. text-matching covers SBERT/BERT-match; cosent covers CoSENT flattening.",
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

    path = Path(args.input_file).expanduser()
    fmt = detect_format(path, args.format)
    summary: Dict[str, Any] = {
        "ok": False,
        "input_file": str(path),
        "format": fmt,
        "task": args.task,
        "records_seen": 0,
        "records_valid": 0,
        "records_invalid": 0,
        "error_count": 0,
        "errors": [],
        "warnings": [],
        "schema_counts": {},
        "ambiguous_schema_rows": 0,
        "label_stats": {
            "count": 0,
            "min": None,
            "max": None,
            "integer_like_count": 0,
            "non_integer_count": 0,
            "binary_label_count": 0,
        },
        "sts_hint": {},
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
                line = raw_line.rstrip("\n\r")
                if not line.strip():
                    continue
                summary["records_seen"] += 1
                if fmt == "jsonl":
                    stop = validate_jsonl_line(line, line_no, summary, args.max_errors)
                else:
                    stop = validate_tsv_line(line, line_no, summary, args.max_errors)
                if stop:
                    summary["stopped_early"] = True
                    break
    except UnicodeDecodeError as exc:
        add_error(summary, 0, f"failed to decode input as UTF-8: {exc}", args.max_errors)
    except OSError as exc:
        add_error(summary, 0, f"failed to read input: {exc}", args.max_errors)

    finalize_hints(summary, args.task, path)
    summary["ok"] = summary["error_count"] == 0
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
