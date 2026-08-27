#!/usr/bin/env python3
"""Offline validator for RAGatouille training raw_data JSON.

This script intentionally uses only the Python standard library. It validates the
shape of JSON examples before a caller initializes RAGTrainer, downloads models,
or launches hard-negative mining/training.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


VALID_MODES = ("auto", "pairs", "labeled_pairs", "triplets")


class ValidationIssue:
    def __init__(self, severity: str, message: str) -> None:
        self.severity = severity
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "message": self.message}


class Validator:
    def __init__(
        self,
        raw_data: Any,
        mode: str,
        positive_label: Any,
        negative_label: Any,
        num_new_negatives: int,
        allow_content_dict_pairs: bool,
    ) -> None:
        self.raw_data = raw_data
        self.requested_mode = mode
        self.positive_label = positive_label
        self.negative_label = negative_label
        self.num_new_negatives = num_new_negatives
        self.allow_content_dict_pairs = allow_content_dict_pairs
        self.issues: list[ValidationIssue] = []
        self.mode = mode
        self.queries: set[str] = set()
        self.collection: set[str] = set()
        self.positives_by_query: dict[str, set[str]] = defaultdict(set)
        self.negatives_by_query: dict[str, set[str]] = defaultdict(set)

    def error(self, message: str) -> None:
        self.issues.append(ValidationIssue("error", message))

    def warning(self, message: str) -> None:
        self.issues.append(ValidationIssue("warning", message))

    def validate(self) -> dict[str, Any]:
        if not isinstance(self.raw_data, list):
            self.error("top-level JSON value must be a list of raw_data rows")
            return self.summary()
        if not self.raw_data:
            self.error("raw_data must contain at least one row")
            return self.summary()

        self.mode = self.detect_mode()
        if self.mode not in ("pairs", "labeled_pairs", "triplets"):
            return self.summary()

        for index, row in enumerate(self.raw_data):
            self.validate_row(index, row)

        if not self.has_errors():
            self.post_validate()
        return self.summary()

    def detect_mode(self) -> str:
        first = self.raw_data[0]
        if not isinstance(first, list):
            self.error("row 0 must be a JSON array; Python tuples should be encoded as arrays")
            return "invalid"

        first_len = len(first)
        arities = {len(row) for row in self.raw_data if isinstance(row, list)}
        non_arrays = [i for i, row in enumerate(self.raw_data) if not isinstance(row, list)]
        if non_arrays:
            self.error(f"rows must be arrays; non-array rows at indexes {non_arrays[:10]}")

        if self.requested_mode == "auto":
            if first_len == 2:
                mode = "pairs"
            elif first_len == 3:
                self.error(
                    "auto mode cannot distinguish labeled_pairs from triplets for length-3 rows; pass --mode labeled_pairs or --mode triplets"
                )
                return "invalid"
            else:
                self.error("row 0 must have length 2 for pairs or length 3 for labeled_pairs/triplets")
                return "invalid"
        else:
            mode = self.requested_mode

        expected_len = 2 if mode == "pairs" else 3
        if any(length != expected_len for length in arities):
            self.error(
                f"mixed row arities {sorted(arities)} do not match mode {mode!r} expected length {expected_len}"
            )
        return mode

    def validate_row(self, index: int, row: Any) -> None:
        if not isinstance(row, list):
            return
        expected_len = 2 if self.mode == "pairs" else 3
        if len(row) != expected_len:
            return

        query = row[0]
        if not isinstance(query, str):
            self.error(f"row {index} query must be a string")
            return
        if not query.strip():
            self.warning(f"row {index} query is empty or whitespace")
        self.queries.add(query)

        if self.mode == "pairs":
            positives = self.extract_passages(row[1], index, "positive", allow_content_dict=self.allow_content_dict_pairs)
            self.add_positives(query, positives)
        elif self.mode == "labeled_pairs":
            passages = self.extract_passages(row[1], index, "passage", allow_content_dict=False)
            label = row[2]
            if label == self.positive_label:
                self.add_positives(query, passages)
            elif label == self.negative_label:
                self.add_negatives(query, passages)
            else:
                self.error(
                    f"row {index} label {label!r} does not match positive_label={self.positive_label!r} or negative_label={self.negative_label!r}"
                )
        elif self.mode == "triplets":
            positives = self.extract_passages(row[1], index, "positive", allow_content_dict=False)
            negatives = self.extract_passages(row[2], index, "negative", allow_content_dict=False)
            self.add_positives(query, positives)
            self.add_negatives(query, negatives)

    def extract_passages(
        self,
        value: Any,
        index: int,
        field_name: str,
        allow_content_dict: bool,
    ) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            passages: list[str] = []
            for item_index, item in enumerate(value):
                if isinstance(item, str):
                    passages.append(item)
                else:
                    self.error(
                        f"row {index} {field_name}[{item_index}] must be a string; got {type(item).__name__}"
                    )
            if not value:
                self.warning(f"row {index} {field_name} list is empty")
            return passages
        if allow_content_dict and isinstance(value, dict):
            content = value.get("content")
            if isinstance(content, str):
                return [content]
            self.error(f"row {index} {field_name} dict must contain string key 'content'")
            return []
        if isinstance(value, dict):
            self.error(
                f"row {index} {field_name} uses a dict; RAGatouille only handles content dicts reliably for unlabeled pairs"
            )
            return []
        self.error(f"row {index} {field_name} must be a string or list of strings")
        return []

    def add_positives(self, query: str, passages: list[str]) -> None:
        for passage in passages:
            self.collection.add(passage)
            self.positives_by_query[query].add(passage)

    def add_negatives(self, query: str, passages: list[str]) -> None:
        for passage in passages:
            self.collection.add(passage)
            self.negatives_by_query[query].add(passage)

    def post_validate(self) -> None:
        for query in sorted(self.queries):
            positives = self.positives_by_query[query]
            negatives = self.negatives_by_query[query]
            if not positives:
                self.error(f"query {query!r} has no positive passages")
            if self.mode in ("labeled_pairs", "triplets") and not negatives and self.num_new_negatives == 0:
                self.error(
                    f"query {query!r} has no negative passages and --num-new-negatives is 0; no triplets can be produced"
                )
            available_random_negatives = self.collection - positives - negatives
            if self.mode == "pairs" and self.num_new_negatives == 0:
                self.error(
                    f"query {query!r} is in pairs mode with --num-new-negatives 0; no negatives will be created"
                )
            if self.num_new_negatives > 0 and not available_random_negatives:
                self.warning(
                    f"query {query!r} has no distinct collection passages available for sampled negatives"
                )
            if positives & negatives:
                overlap_count = len(positives & negatives)
                self.warning(
                    f"query {query!r} has {overlap_count} passage(s) marked as both positive and negative"
                )

    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def summary(self) -> dict[str, Any]:
        errors = sum(1 for issue in self.issues if issue.severity == "error")
        warnings = sum(1 for issue in self.issues if issue.severity == "warning")
        return {
            "ok": errors == 0,
            "mode": self.mode,
            "rows": len(self.raw_data) if isinstance(self.raw_data, list) else None,
            "queries": len(self.queries),
            "collection_passages": len(self.collection),
            "errors": errors,
            "warnings": warnings,
            "issues": [issue.as_dict() for issue in self.issues],
        }


def parse_label(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate RAGatouille training raw_data JSON without importing RAGatouille or downloading models."
    )
    parser.add_argument("json_path", type=Path, help="Path to a JSON file containing a top-level raw_data list.")
    parser.add_argument(
        "--mode",
        choices=VALID_MODES,
        default="auto",
        help="Raw data mode. Use explicit labeled_pairs or triplets for length-3 rows.",
    )
    parser.add_argument(
        "--positive-label",
        default="1",
        help="Positive label for labeled_pairs. Parsed as JSON when possible, so 1 remains an integer.",
    )
    parser.add_argument(
        "--negative-label",
        default="0",
        help="Negative label for labeled_pairs. Parsed as JSON when possible, so 0 remains an integer.",
    )
    parser.add_argument(
        "--num-new-negatives",
        type=int,
        default=10,
        help="Planned num_new_negatives value; used to detect likely zero-triplet cases.",
    )
    parser.add_argument(
        "--no-content-dict-pairs",
        action="store_true",
        help="Reject {'content': text} passages even for unlabeled pairs.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        raw_data = json.loads(args.json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: file not found: {args.json_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 2

    if args.num_new_negatives < 0:
        print("error: --num-new-negatives must be non-negative", file=sys.stderr)
        return 2

    validator = Validator(
        raw_data=raw_data,
        mode=args.mode,
        positive_label=parse_label(args.positive_label),
        negative_label=parse_label(args.negative_label),
        num_new_negatives=args.num_new_negatives,
        allow_content_dict_pairs=not args.no_content_dict_pairs,
    )
    summary = validator.validate()
    print(json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
