#!/usr/bin/env python3
"""Validate minimal Tuna probabilistic/contextual ranking JSON schemas."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


class IssueCollector:
    def __init__(self, max_items: int):
        self.max_items = max_items
        self.count = 0
        self.items: List[str] = []

    def add(self, message: str) -> None:
        self.count += 1
        if len(self.items) < self.max_items:
            self.items.append(message)

    def exported(self) -> List[str]:
        if self.count <= len(self.items):
            return list(self.items)
        omitted = self.count - len(self.items)
        return list(self.items) + [f"... {omitted} additional issue(s) omitted"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate minimal Tuna ranking JSON. 'probabilistic' checks the "
            "formatted training schema shared by probabilistic and contextual "
            "ranking finetuning. 'contextual' checks raw GPT-4 ranking provenance."
        )
    )
    parser.add_argument("path", help="JSON array, JSON object, or JSONL file to validate.")
    parser.add_argument(
        "--schema",
        choices=["auto", "probabilistic", "contextual", "formatted"],
        default="auto",
        help="Schema to validate. 'formatted' is an alias for 'probabilistic'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Validate only the first N records after loading.",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="Maximum number of error/warning messages to include in output.",
    )
    return parser.parse_args()


def load_records(path: Path) -> Tuple[List[Any], str]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        records: List[Any] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no} is not valid JSON: {exc}") from exc
        return records, "jsonl"

    if isinstance(data, list):
        return data, "json-array"
    if isinstance(data, dict):
        return [data], "json-object"
    raise ValueError(f"top-level JSON must be an object or array, got {type(data).__name__}")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def require_keys(record: Dict[str, Any], keys: Iterable[str], idx: int, errors: IssueCollector) -> None:
    for key in keys:
        if key not in record:
            errors.add(f"record {idx}: missing required key {key!r}")


def check_probabilistic(record: Dict[str, Any], idx: int, errors: IssueCollector, warnings: IssueCollector) -> None:
    require_keys(record, ["id", "instruction", "output", "score"], idx, errors)
    if "instruction" in record and not isinstance(record["instruction"], str):
        errors.add(f"record {idx}: 'instruction' must be a string")

    outputs = record.get("output")
    scores = record.get("score")

    if not isinstance(outputs, list):
        errors.add(f"record {idx}: 'output' must be a list of candidate strings")
        outputs = []
    if not isinstance(scores, list):
        errors.add(f"record {idx}: 'score' must be a list of numeric candidate scores")
        scores = []

    if isinstance(outputs, list):
        if len(outputs) < 2:
            errors.add(f"record {idx}: ranking training needs at least two candidate outputs")
        for cand_idx, candidate in enumerate(outputs):
            if not isinstance(candidate, str):
                errors.add(f"record {idx}: output[{cand_idx}] must be a string")

    if isinstance(scores, list):
        for score_idx, score in enumerate(scores):
            if not is_number(score):
                errors.add(f"record {idx}: score[{score_idx}] must be a finite number")

    if isinstance(outputs, list) and isinstance(scores, list) and len(outputs) != len(scores):
        errors.add(
            f"record {idx}: 'output' and 'score' length mismatch "
            f"({len(outputs)} vs {len(scores)})"
        )

    if isinstance(scores, list) and scores and all(is_number(score) for score in scores):
        if len(set(float(score) for score in scores)) == 1:
            warnings.add(f"record {idx}: all scores are equal; ranking signal may be degenerate")


def get_rank_list(record: Dict[str, Any]) -> Tuple[Any, str | None]:
    if "ranks" in record:
        return record["ranks"], "ranks"
    if "rank" in record:
        return record["rank"], "rank"
    return None, None


def check_contextual(record: Dict[str, Any], idx: int, errors: IssueCollector, warnings: IssueCollector) -> None:
    require_keys(record, ["prompt", "instruct", "generation", "id", "gpt_eval", "rank_str", "response_4"], idx, errors)
    rank_values, rank_key = get_rank_list(record)
    if rank_key is None:
        errors.add(f"record {idx}: missing required rank list key 'rank' or 'ranks'")
    elif "rank" in record and "ranks" in record and record["rank"] != record["ranks"]:
        warnings.add(f"record {idx}: both 'rank' and 'ranks' are present with different values")

    for key in ["prompt", "instruct", "gpt_eval", "rank_str", "response_4"]:
        if key in record and not isinstance(record[key], str):
            errors.add(f"record {idx}: {key!r} must be a string")

    generation = record.get("generation")
    if not isinstance(generation, list):
        errors.add(f"record {idx}: 'generation' must be a list of four candidate strings")
        generation = []
    else:
        if len(generation) != 4:
            errors.add(f"record {idx}: 'generation' should contain exactly 4 candidate responses")
        for cand_idx, candidate in enumerate(generation):
            if not isinstance(candidate, str):
                errors.add(f"record {idx}: generation[{cand_idx}] must be a string")

    if not isinstance(rank_values, list):
        if rank_key is not None:
            errors.add(f"record {idx}: {rank_key!r} must be a list of integer ranks")
        rank_values = []
    else:
        for rank_idx, value in enumerate(rank_values):
            if not isinstance(value, int) or isinstance(value, bool):
                errors.add(f"record {idx}: {rank_key}[{rank_idx}] must be an integer")

    if isinstance(generation, list) and isinstance(rank_values, list) and generation and rank_values:
        # Source prompts ask the judge to drop duplicate responses before ranking,
        # so a raw contextual rank may be a proper subset of response ids rather
        # than a full permutation of generation plus response_4.
        max_rank_id = len(generation)
        if len(rank_values) < 1 or len(rank_values) > max_rank_id + 1:
            errors.add(
                f"record {idx}: {rank_key!r} length should be between 1 and "
                f"len(generation)+1 ({max_rank_id + 1}), got {len(rank_values)}"
            )
        valid_id_set = set(range(max_rank_id + 1))
        integer_values = [value for value in rank_values if isinstance(value, int) and not isinstance(value, bool)]
        invalid_values = [value for value in integer_values if value not in valid_id_set]
        if invalid_values:
            errors.add(
                f"record {idx}: {rank_key!r} contains response ids outside "
                f"0..{max_rank_id}: {invalid_values}"
            )
        if len(integer_values) != len(set(integer_values)):
            errors.add(f"record {idx}: {rank_key!r} contains duplicate response ids")

    if isinstance(record.get("response_4"), str) and not record["response_4"].strip():
        warnings.add(f"record {idx}: 'response_4' is empty; GPT-4 provenance is incomplete")
    if isinstance(record.get("gpt_eval"), str) and not record["gpt_eval"].strip():
        warnings.add(f"record {idx}: 'gpt_eval' is empty; GPT-4 provenance is incomplete")


def detect_schema(record: Dict[str, Any]) -> str:
    contextual_keys = {"prompt", "generation", "gpt_eval", "rank_str", "response_4"}
    probabilistic_keys = {"instruction", "output", "score"}
    if contextual_keys.issubset(record.keys()) and ("rank" in record or "ranks" in record):
        return "contextual"
    if probabilistic_keys.issubset(record.keys()):
        return "probabilistic"
    return "unknown"


def validate(records: List[Any], schema: str, limit: int | None, max_errors: int) -> Dict[str, Any]:
    errors = IssueCollector(max_errors)
    warnings = IssueCollector(max_errors)

    if schema == "formatted":
        schema = "probabilistic"

    if not records:
        errors.add("file contains no records")
        resolved_schema = schema if schema != "auto" else "unknown"
        return {
            "status": "error",
            "schema": resolved_schema,
            "records": 0,
            "validated_records": 0,
            "errors": errors.exported(),
            "warnings": warnings.exported(),
            "error_count": errors.count,
            "warning_count": warnings.count,
        }

    if schema == "auto":
        first_dict = records[0] if isinstance(records[0], dict) else {}
        schema = detect_schema(first_dict)
        if schema == "unknown":
            errors.add("could not auto-detect schema from the first record")

    selected = records if limit is None else records[: max(limit, 0)]
    for idx, record in enumerate(selected):
        if not isinstance(record, dict):
            errors.add(f"record {idx}: expected object, got {type(record).__name__}")
            continue
        if schema == "probabilistic":
            check_probabilistic(record, idx, errors, warnings)
        elif schema == "contextual":
            check_contextual(record, idx, errors, warnings)
        else:
            errors.add(f"record {idx}: unknown schema {schema!r}")
            break

    if limit is not None and limit < len(records):
        warnings.add(f"validation limited to first {max(limit, 0)} of {len(records)} records")

    return {
        "status": "error" if errors.count else "ok",
        "schema": schema,
        "records": len(records),
        "validated_records": len(selected),
        "errors": errors.exported(),
        "warnings": warnings.exported(),
        "error_count": errors.count,
        "warning_count": warnings.count,
    }


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    result: Dict[str, Any]
    if not path.exists():
        result = {
            "status": "error",
            "path": args.path,
            "errors": [f"path does not exist: {args.path}"],
            "warnings": [],
            "error_count": 1,
            "warning_count": 0,
        }
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 2

    try:
        records, file_format = load_records(path)
        result = validate(records, args.schema, args.limit, args.max_errors)
        result["path"] = args.path
        result["file_format"] = file_format
    except Exception as exc:  # validation utility should be explicit for callers
        result = {
            "status": "error",
            "path": args.path,
            "errors": [str(exc)],
            "warnings": [],
            "error_count": 1,
            "warning_count": 0,
        }

    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result.get("status") == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
