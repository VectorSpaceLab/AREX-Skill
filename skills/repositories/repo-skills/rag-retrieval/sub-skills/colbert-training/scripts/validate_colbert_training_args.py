#!/usr/bin/env python3
"""Validate RAG-Retrieval ColBERT training data and common argument choices.

This helper is intentionally safe: it reads JSONL and inspects scalar arguments only.
It does not import transformers, load tokenizers, download models, or touch GPUs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


BGE_M3_NAMES = ("bge-m3", "bge_m3")
XLMR_HINTS = ("xlm-roberta", "xlmroberta", "bge-m3", "bge_m3")
BERT_HINTS = ("bert", "roberta")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight triplet JSONL and ColBERT training arguments without model downloads."
    )
    parser.add_argument("--data", required=True, help="Path to triplet JSONL training data.")
    parser.add_argument("--neg-nums", type=int, default=15, help="Requested negatives per query-positive pair.")
    parser.add_argument("--colbert-dim", type=int, default=768, help="ColBERT projection dimension.")
    parser.add_argument(
        "--model-name-or-path",
        default="",
        help="Hugging Face model id or local checkpoint path used for training.",
    )
    parser.add_argument("--query-max-len", type=int, default=128, help="Tokenizer max length for queries.")
    parser.add_argument("--passage-max-len", type=int, default=512, help="Tokenizer max length for passages.")
    return parser.parse_args()


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_text_list(value: Any) -> tuple[bool, str | None, int]:
    if not isinstance(value, list):
        return False, "must be a list", 0
    if not value:
        return False, "must not be empty", 0
    for index, item in enumerate(value):
        if not is_non_empty_string(item):
            return False, f"item {index} must be a non-empty string", len(value)
    return True, None, len(value)


def model_hint(model_name_or_path: str) -> str:
    lowered = model_name_or_path.lower()
    if any(name in lowered for name in BGE_M3_NAMES):
        return "bge-m3"
    if any(name in lowered for name in XLMR_HINTS):
        return "xlm-roberta-like"
    if any(name in lowered for name in BERT_HINTS):
        return "bert-like"
    return "unknown"


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    data_path = Path(args.data)
    if not data_path.is_file():
        errors.append(f"data file not found: {data_path}")
    if args.neg_nums <= 0:
        errors.append("--neg-nums must be a positive integer")
    if args.colbert_dim <= 0:
        errors.append("--colbert-dim must be a positive integer")
    if args.query_max_len <= 0:
        errors.append("--query-max-len must be a positive integer")
    if args.passage_max_len <= 0:
        errors.append("--passage-max-len must be a positive integer")
    if args.query_max_len > args.passage_max_len:
        warnings.append("query max length is larger than passage max length; confirm this is intentional")

    line_count = 0
    valid_rows = 0
    expanded_examples = 0
    min_negatives: int | None = None
    rows_with_resampled_negatives = 0
    rows_with_extra_fields = 0
    sample_neg_counts: list[int] = []

    if data_path.is_file():
        with data_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    warnings.append(f"line {line_number}: blank line ignored by validator but not expected by training")
                    continue
                line_count += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"line {line_number}: invalid JSON ({exc.msg})")
                    continue
                if not isinstance(row, dict):
                    errors.append(f"line {line_number}: JSON value must be an object")
                    continue

                expected_keys = {"query", "pos", "neg"}
                if not expected_keys.issubset(row):
                    missing = ", ".join(sorted(expected_keys - set(row)))
                    errors.append(f"line {line_number}: missing required key(s): {missing}")
                    continue
                if set(row) - expected_keys:
                    rows_with_extra_fields += 1

                if not is_non_empty_string(row.get("query")):
                    errors.append(f"line {line_number}: query must be a non-empty string")
                    continue

                pos_ok, pos_error, pos_count = validate_text_list(row.get("pos"))
                neg_ok, neg_error, neg_count = validate_text_list(row.get("neg"))
                if not pos_ok:
                    errors.append(f"line {line_number}: pos {pos_error}")
                    continue
                if not neg_ok:
                    errors.append(f"line {line_number}: neg {neg_error}")
                    continue

                valid_rows += 1
                expanded_examples += pos_count
                min_negatives = neg_count if min_negatives is None else min(min_negatives, neg_count)
                sample_neg_counts.append(neg_count)
                if neg_count < args.neg_nums:
                    rows_with_resampled_negatives += 1

    if line_count == 0 and data_path.is_file():
        errors.append("data file contains no non-blank JSONL rows")
    if valid_rows == 0 and data_path.is_file():
        errors.append("data file contains no valid training rows")

    hint = model_hint(args.model_name_or_path)
    if hint == "bge-m3" and args.colbert_dim != 1024:
        warnings.append(
            "BAAI/bge-m3 ColBERT commonly uses --colbert-dim 1024; "
            f"received {args.colbert_dim}. Use 1024 unless intentionally training a new projection size."
        )
    if hint == "bge-m3":
        warnings.append("BAAI/bge-m3 is XLM-RoBERTa-like; use an FSDP config that wraps XLMRobertaLayer")
    elif hint == "bert-like":
        warnings.append("BERT-like model detected; use an FSDP config that wraps BertLayer")
    elif hint == "xlm-roberta-like":
        warnings.append("XLM-RoBERTa-like model detected; use an FSDP config that wraps XLMRobertaLayer")
    elif args.model_name_or_path:
        warnings.append("could not infer backbone family; verify the FSDP transformer layer class manually")

    if valid_rows and rows_with_resampled_negatives:
        ratio = rows_with_resampled_negatives / valid_rows
        warnings.append(
            f"{rows_with_resampled_negatives}/{valid_rows} valid rows have fewer negatives than --neg-nums; "
            "the training dataset will repeat and resample those negatives"
        )
        if ratio >= 0.5:
            warnings.append("most rows will resample negatives; consider lowering --neg-nums or mining more negatives")
    if rows_with_extra_fields:
        warnings.append(f"{rows_with_extra_fields} row(s) contain extra fields; the source dataset ignores them")

    print("ColBERT training preflight")
    print(f"  data: {data_path}")
    print(f"  non_blank_rows: {line_count}")
    print(f"  valid_rows: {valid_rows}")
    print(f"  expanded_query_positive_examples: {expanded_examples}")
    if min_negatives is not None:
        print(f"  min_negatives_per_valid_row: {min_negatives}")
    if sample_neg_counts:
        sorted_counts = sorted(sample_neg_counts)
        median_count = sorted_counts[len(sorted_counts) // 2]
        print(f"  median_negatives_per_valid_row: {median_count}")
    print(f"  requested_neg_nums: {args.neg_nums}")
    print(f"  colbert_dim: {args.colbert_dim}")
    if args.model_name_or_path:
        print(f"  model_hint: {hint}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nOK: data and scalar arguments passed preflight checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
