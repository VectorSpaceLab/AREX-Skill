#!/usr/bin/env python3
"""Validate FlagEmbedding embedder/reranker fine-tuning JSONL files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def iter_json_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            files.extend(sorted(p for p in path.iterdir() if p.suffix in {".json", ".jsonl"} and p.is_file()))
        else:
            files.append(path)
    return files


def require_string(errors: list[str], value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")


def require_string_list(errors: list[str], value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a non-empty list of strings")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}[{index}] must be a non-empty string")


def validate_scores(
    errors: list[str],
    warnings: list[str],
    record: dict[str, Any],
    kd_required: bool,
) -> None:
    has_pos_scores = "pos_scores" in record
    has_neg_scores = "neg_scores" in record
    if kd_required and (not has_pos_scores or not has_neg_scores):
        errors.append("knowledge distillation requires both pos_scores and neg_scores")
        return
    if has_pos_scores != has_neg_scores:
        errors.append("pos_scores and neg_scores must appear together")
        return
    if not has_pos_scores:
        return

    pos = record.get("pos")
    neg = record.get("neg")
    pos_scores = record.get("pos_scores")
    neg_scores = record.get("neg_scores")
    if not isinstance(pos_scores, list):
        errors.append("pos_scores must be a list")
    if not isinstance(neg_scores, list):
        errors.append("neg_scores must be a list")
    if isinstance(pos_scores, list) and isinstance(pos, list) and len(pos_scores) != len(pos):
        errors.append(f"len(pos_scores)={len(pos_scores)} must equal len(pos)={len(pos)}")
    if isinstance(neg_scores, list) and isinstance(neg, list) and len(neg_scores) != len(neg):
        errors.append(f"len(neg_scores)={len(neg_scores)} must equal len(neg)={len(neg)}")
    if isinstance(pos_scores, list):
        for index, score in enumerate(pos_scores):
            if not is_number(score):
                errors.append(f"pos_scores[{index}] must be numeric")
    if isinstance(neg_scores, list):
        for index, score in enumerate(neg_scores):
            if not is_number(score):
                errors.append(f"neg_scores[{index}] must be numeric")
    if not kd_required:
        warnings.append("score fields are present but --knowledge-distillation was not set; trainers ignore them")


def validate_record(record: Any, task: str, kd_required: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(record, dict):
        return ["line must be a JSON object"], warnings

    for key in ("query", "pos", "neg"):
        if key not in record:
            errors.append(f"missing required field: {key}")

    if "query" in record:
        require_string(errors, record["query"], "query")
    if "pos" in record:
        require_string_list(errors, record["pos"], "pos")
    if "neg" in record:
        require_string_list(errors, record["neg"], "neg")

    if isinstance(record.get("query"), str) and isinstance(record.get("neg"), list):
        if record["query"] in record["neg"]:
            errors.append("neg must not contain the query text")
    if isinstance(record.get("pos"), list) and isinstance(record.get("neg"), list):
        overlap = sorted(set(record["pos"]).intersection(record["neg"]))
        if overlap:
            sample = overlap[0]
            errors.append(f"neg must not contain positive text: {sample[:80]!r}")
        if len(set(record["neg"])) < len(record["neg"]):
            warnings.append("neg contains duplicate strings; training can run but negative diversity is lower")

    if "prompt" in record and not isinstance(record["prompt"], str):
        errors.append("prompt must be a string when present")
    if "type" in record and not isinstance(record["type"], str):
        errors.append("type must be a string when present")
    if task == "reranker":
        for key in ("query_prompt", "passage_prompt"):
            if key in record and not isinstance(record[key], str):
                errors.append(f"{key} must be a string when present")

    validate_scores(errors, warnings, record, kd_required)
    return errors, warnings


def validate_file(path: Path, task: str, kd_required: bool, max_errors: int) -> tuple[int, int, int]:
    errors_seen = 0
    warnings_seen = 0
    records_seen = 0
    if not path.exists():
        print(f"ERROR {path}: file does not exist", file=sys.stderr)
        return 1, 0, 0
    if not path.is_file():
        print(f"ERROR {path}: not a file", file=sys.stderr)
        return 1, 0, 0

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            records_seen += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"ERROR {path}:{line_number}: invalid JSON: {exc}", file=sys.stderr)
                errors_seen += 1
                if errors_seen >= max_errors:
                    return errors_seen, warnings_seen, records_seen
                continue

            errors, warnings = validate_record(record, task, kd_required)
            for message in errors:
                print(f"ERROR {path}:{line_number}: {message}", file=sys.stderr)
            for message in warnings:
                print(f"WARNING {path}:{line_number}: {message}", file=sys.stderr)
            errors_seen += len(errors)
            warnings_seen += len(warnings)
            if errors_seen >= max_errors:
                return errors_seen, warnings_seen, records_seen

    if records_seen == 0:
        print(f"ERROR {path}: no JSON records found", file=sys.stderr)
        errors_seen += 1
    return errors_seen, warnings_seen, records_seen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="JSONL files or directories containing .json/.jsonl files")
    parser.add_argument("--task", choices=["embedder", "reranker"], required=True, help="Training task schema to validate")
    parser.add_argument("--knowledge-distillation", action="store_true", help="Require valid pos_scores and neg_scores for KD training")
    parser.add_argument("--max-errors", type=int, default=50, help="Stop after this many errors across a file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = iter_json_files(args.paths)
    if not files:
        print("ERROR: no .json or .jsonl files found", file=sys.stderr)
        return 1

    total_errors = 0
    total_warnings = 0
    total_records = 0
    for path in files:
        errors, warnings, records = validate_file(path, args.task, args.knowledge_distillation, args.max_errors)
        total_errors += errors
        total_warnings += warnings
        total_records += records

    print(
        f"validated files={len(files)} records={total_records} errors={total_errors} warnings={total_warnings}",
        file=sys.stderr,
    )
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
