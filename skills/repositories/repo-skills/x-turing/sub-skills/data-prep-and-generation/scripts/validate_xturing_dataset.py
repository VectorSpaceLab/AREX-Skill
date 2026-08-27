#!/usr/bin/env python3
"""Validate a candidate xTuring dataset.

The validator checks the supported schemas:
- text
- instruction
- preference

Inputs may be a saved Hugging Face dataset directory, a JSONL file, or a JSON
file that contains either a list of rows or a mapping of columns.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

try:
    from datasets import Dataset, DatasetDict, load_from_disk
except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
    raise ModuleNotFoundError(
        "The Hugging Face 'datasets' package is required for validate_xturing_dataset.py."
    ) from exc

SCHEMAS = ("auto", "text", "instruction", "preference")


def _load_json_like(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Malformed JSON on line {line_number} in {path}: {exc.msg}"
                    ) from exc
                if not isinstance(row, dict):
                    raise ValueError(
                        f"Line {line_number} in {path} is not a JSON object"
                    )
                rows.append(row)
        return DatasetDict({"train": Dataset.from_list(rows)})

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, list):
            if not all(isinstance(row, dict) for row in payload):
                raise ValueError("JSON array input must contain JSON objects only")
            return DatasetDict({"train": Dataset.from_list(payload)})

        if isinstance(payload, dict):
            if payload and all(isinstance(value, list) for value in payload.values()):
                if any(value and isinstance(value[0], dict) for value in payload.values()):
                    return DatasetDict(
                        {split: Dataset.from_list(rows) for split, rows in payload.items()}
                    )
                return DatasetDict({"train": Dataset.from_dict(payload)})

        raise ValueError(
            "JSON input must be either a list of rows or a mapping of columns"
        )

    raise ValueError("Unsupported file format. Use a directory, .json, or .jsonl file.")


def load_candidate_dataset(path: Path):
    if path.is_dir():
        return load_from_disk(str(path))
    return _load_json_like(path)


def _train_split(candidate):
    if isinstance(candidate, DatasetDict):
        if "train" not in candidate:
            raise AssertionError("The dataset should have a train split")
        return candidate["train"]
    return candidate


def _required_columns(schema: str, train_columns: Sequence[str]):
    column_names = list(train_columns)
    column_set = set(column_names)

    if schema == "text":
        if "text" not in column_set:
            raise AssertionError("The dataset should have a column named text")
        if len(column_names) > 1 and "target" not in column_set:
            raise AssertionError(
                "The dataset should have a column named target if there is more than one column"
            )
        if len(column_names) > 2:
            raise AssertionError(
                "The dataset should have only two columns, text and target"
            )
        return column_names

    if schema == "instruction":
        if "text" not in column_set:
            raise AssertionError("The dataset should have a column named text")
        if "target" not in column_set:
            raise AssertionError("The dataset should have a column named target")
        if "instruction" not in column_set:
            raise AssertionError("The dataset should have a column named instruction")
        if len(column_names) != 3:
            raise AssertionError(
                "The dataset should have only three columns, instruction, text and target"
            )
        return ["instruction", "text", "target"]

    if schema == "preference":
        if "prompt" not in column_set:
            raise AssertionError("The dataset should have a column named prompt")
        if "chosen" not in column_set:
            raise AssertionError("The dataset should have a column named chosen")
        if "rejected" not in column_set:
            raise AssertionError("The dataset should have a column named rejected")
        if len(column_names) != 3:
            raise AssertionError(
                "The dataset should have only three columns: prompt, chosen, and rejected"
            )
        return ["prompt", "chosen", "rejected"]

    raise ValueError(f"Unknown schema: {schema}")


def infer_schema(train_columns: Sequence[str]) -> str:
    column_names = list(train_columns)
    column_set = set(column_names)

    if column_set == {"prompt", "chosen", "rejected"} and len(column_names) == 3:
        return "preference"
    if column_set == {"instruction", "text", "target"} and len(column_names) == 3:
        return "instruction"
    if column_set == {"text"} and len(column_names) == 1:
        return "text"
    if column_set == {"text", "target"} and len(column_names) == 2:
        return "text"

    raise ValueError(
        "Could not infer a supported schema from the train split columns: "
        f"{column_names}"
    )


def _check_required_values(train_split, required_columns: Sequence[str]):
    for row_index, row in enumerate(train_split):
        for column in required_columns:
            if column not in row:
                raise ValueError(f"Row {row_index} is missing required field '{column}'")
            if row[column] is None:
                raise ValueError(f"Row {row_index} has a null '{column}' value")


def validate_dataset(candidate, schema: str = "auto"):
    train_split = _train_split(candidate)
    train_columns = list(train_split.column_names)

    if schema == "auto":
        schema = infer_schema(train_columns)

    required_columns = _required_columns(schema, train_columns)
    _check_required_values(train_split, required_columns)

    if schema not in {"text", "instruction", "preference"}:
        raise ValueError(f"Unknown schema: {schema}")

    return schema, len(train_split), train_columns


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate an xTuring dataset.")
    parser.add_argument(
        "--input-path",
        "--input-file",
        dest="input_path",
        required=True,
        help="Path to a saved dataset directory, JSON, or JSONL file.",
    )
    parser.add_argument(
        "--schema",
        choices=SCHEMAS,
        default="auto",
        help="Schema to validate, or auto-detect from the train split.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    candidate = load_candidate_dataset(input_path)
    schema, row_count, columns = validate_dataset(candidate, schema=args.schema)
    print(f"OK: schema={schema} rows={row_count} columns={columns}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
