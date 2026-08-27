#!/usr/bin/env python3
"""Validate local AutoTrain text/LLM/tabular CSV or JSONL schemas.

This helper checks column presence and a few lightweight value-shape rules. It does
not import AutoTrain trainer code, upload data, or launch training.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except Exception as exc:  # pragma: no cover - environment triage
    print(f"ERROR: pandas is required for this helper: {exc!r}", file=sys.stderr)
    raise SystemExit(1)


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix in {".jsonl", ".ndjson"}:
        return pd.read_json(path, lines=True)
    if suffix == ".json":
        return pd.read_json(path)
    raise ValueError(f"unsupported file type for {path}; use csv, tsv, jsonl, ndjson, or json")


def normalize_task(task: str, trainer: str | None) -> tuple[str, str | None]:
    raw = task.strip().lower().replace("_", "-")
    if raw.startswith("st:"):
        return "sentence-transformers", raw.split(":", 1)[1]
    if raw.startswith("sentence-transformers:"):
        return "sentence-transformers", raw.split(":", 1)[1]
    if raw.startswith("llm:"):
        return "llm", raw.split(":", 1)[1]
    if raw.startswith("llm-"):
        return "llm", raw.split("-", 1)[1]

    aliases = {
        "text-binary-classification": "text-classification",
        "text-multi-class-classification": "text-classification",
        "text-classification": "text-classification",
        "text-single-column-regression": "text-regression",
        "text-regression": "text-regression",
        "token-classification": "token-classification",
        "seq2seq": "seq2seq",
        "extractive-question-answering": "extractive-qa",
        "extractive-qa": "extractive-qa",
        "ext-qa": "extractive-qa",
        "sentence-transformers": "sentence-transformers",
        "st": "sentence-transformers",
        "tabular": "tabular",
        "llm": "llm",
    }
    normalized = aliases.get(raw)
    if normalized is None:
        raise ValueError(f"unsupported task: {task}")
    return normalized, trainer


def split_columns(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_literal(value: Any) -> Any:
    if isinstance(value, str):
        return ast.literal_eval(value)
    return value


def first_non_null(df: pd.DataFrame, column: str, limit: int = 5) -> list[tuple[Any, Any]]:
    rows: list[tuple[Any, Any]] = []
    for idx, value in df[column].dropna().head(limit).items():
        rows.append((idx, value))
    return rows


def check_listlike(df: pd.DataFrame, column: str, label: str, errors: list[str]) -> None:
    for idx, value in first_non_null(df, column):
        try:
            parsed = parse_literal(value)
        except Exception as exc:
            errors.append(f"{label}.{column} row {idx}: cannot parse list literal: {exc}")
            continue
        if not isinstance(parsed, (list, tuple)):
            errors.append(f"{label}.{column} row {idx}: expected list/tuple, got {type(parsed).__name__}")


def check_token_alignment(df: pd.DataFrame, text_col: str, target_col: str, label: str, errors: list[str]) -> None:
    for idx, row in df[[text_col, target_col]].dropna().head(5).iterrows():
        try:
            tokens = parse_literal(row[text_col])
            tags = parse_literal(row[target_col])
        except Exception as exc:
            errors.append(f"{label} row {idx}: cannot parse token/tag list: {exc}")
            continue
        if isinstance(tokens, (list, tuple)) and isinstance(tags, (list, tuple)) and len(tokens) != len(tags):
            errors.append(f"{label} row {idx}: token/tag length mismatch ({len(tokens)} != {len(tags)})")


def check_dictlike(df: pd.DataFrame, column: str, label: str, errors: list[str]) -> None:
    for idx, value in first_non_null(df, column):
        try:
            parsed = parse_literal(value)
        except Exception as exc:
            errors.append(f"{label}.{column} row {idx}: cannot parse dict literal: {exc}")
            continue
        if not isinstance(parsed, dict):
            errors.append(f"{label}.{column} row {idx}: expected dict, got {type(parsed).__name__}")


def required_columns(args: argparse.Namespace, task: str, trainer: str | None, warnings: list[str]) -> list[str]:
    if task in {"text-classification", "text-regression", "seq2seq"}:
        return [args.text_column, args.target_column]
    if task == "token-classification":
        return [args.text_column, args.target_column]
    if task == "extractive-qa":
        return [args.text_column, args.question_column, args.answer_column]
    if task == "sentence-transformers":
        subtype = (trainer or args.trainer or "pair").lower()
        if subtype in {"pair", "qa"}:
            return [args.sentence1_column, args.sentence2_column]
        if subtype in {"pair-class", "pair_class", "pair-score", "pair_score"}:
            return [args.sentence1_column, args.sentence2_column, args.target_column]
        if subtype == "triplet":
            return [args.sentence1_column, args.sentence2_column, args.sentence3_column]
        raise ValueError(f"unsupported sentence-transformers trainer: {subtype}")
    if task == "tabular":
        targets = split_columns(args.target_columns) or [args.target_column]
        return [args.id_column, *targets]
    if task == "llm":
        subtype = (trainer or args.trainer or "sft").lower()
        cols = [args.text_column]
        if subtype in {"dpo", "orpo", "reward"}:
            if args.rejected_text_column:
                cols.append(args.rejected_text_column)
            else:
                warnings.append("preference trainer selected but --rejected-text-column was not provided")
            if args.prompt_text_column:
                cols.append(args.prompt_text_column)
            else:
                warnings.append("preference trainer selected but --prompt-text-column was not provided")
        return cols
    raise ValueError(f"unsupported normalized task: {task}")


def validate_frame(df: pd.DataFrame, label: str, required: list[str], args: argparse.Namespace, task: str, errors: list[str]) -> dict[str, Any]:
    missing = [col for col in required if col not in df.columns]
    if missing:
        errors.append(f"{label}: missing columns: {missing}")
    else:
        if task == "token-classification":
            check_listlike(df, args.text_column, label, errors)
            check_listlike(df, args.target_column, label, errors)
            check_token_alignment(df, args.text_column, args.target_column, label, errors)
        if task == "extractive-qa":
            check_dictlike(df, args.answer_column, label, errors)
    return {
        "label": label,
        "rows": int(len(df)),
        "columns": list(map(str, df.columns.tolist())),
        "required_columns": required,
        "missing_columns": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Train CSV/TSV/JSON/JSONL file")
    parser.add_argument("--valid-path", type=Path, help="Optional validation CSV/TSV/JSON/JSONL file")
    parser.add_argument("--task", required=True, help="AutoTrain task alias, e.g. text-classification, st:triplet, llm-dpo")
    parser.add_argument("--trainer", help="Optional subtype for sentence-transformers or llm")
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--target-column", default="target")
    parser.add_argument("--target-columns", help="Comma-separated tabular target columns")
    parser.add_argument("--question-column", default="question")
    parser.add_argument("--answer-column", default="answer")
    parser.add_argument("--id-column", default="id")
    parser.add_argument("--sentence1-column", default="sentence1")
    parser.add_argument("--sentence2-column", default="sentence2")
    parser.add_argument("--sentence3-column", default="sentence3")
    parser.add_argument("--prompt-text-column")
    parser.add_argument("--rejected-text-column")
    args = parser.parse_args()

    warnings: list[str] = []
    errors: list[str] = []
    try:
        task, trainer = normalize_task(args.task, args.trainer)
        required = required_columns(args, task, trainer, warnings)
        frames = [("train", read_table(args.path))]
        if args.valid_path:
            frames.append(("validation", read_table(args.valid_path)))
        summaries = [validate_frame(df, label, required, args, task, errors) for label, df in frames]
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = {
        "task": task,
        "trainer": trainer or args.trainer,
        "ok": not errors,
        "warnings": warnings,
        "errors": errors,
        "files": summaries,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
