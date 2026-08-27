#!/usr/bin/env python3
"""Convert Alpaca JSON into a saved xTuring-compatible dataset.

The input must be a JSON array with records that contain:
- instruction
- input
- output

The output is a Hugging Face dataset directory with a single train split and
columns:
- instruction
- text
- target
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Sequence

try:
    from datasets import Dataset, DatasetDict
except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
    raise ModuleNotFoundError(
        "The Hugging Face 'datasets' package is required for convert_alpaca_json.py."
    ) from exc


REQUIRED_FIELDS = ("instruction", "input", "output")
OUTPUT_COLUMNS = ("instruction", "text", "target")


def _stringify(value, field_name: str, row_index: int) -> str:
    if value is None:
        raise ValueError(f"Row {row_index} has a null {field_name} field")
    if isinstance(value, str):
        return value
    return str(value)


def load_alpaca_rows(input_file: Path) -> List[dict]:
    with input_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError("Alpaca input must be a JSON array of records")

    rows: List[dict] = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} is not a JSON object")
        rows.append(row)
    return rows


def convert_alpaca_rows(rows: Sequence[dict], limit: int | None = None) -> DatasetDict:
    if limit is not None:
        rows = list(rows[:limit])

    instructions: List[str] = []
    inputs: List[str] = []
    outputs: List[str] = []

    for index, row in enumerate(rows):
        for field in REQUIRED_FIELDS:
            if field not in row:
                raise ValueError(f"Row {index} is missing required field '{field}'")

        instructions.append(_stringify(row["instruction"], "instruction", index))
        inputs.append(_stringify(row["input"], "input", index))
        outputs.append(_stringify(row["output"], "output", index))

    dataset = DatasetDict(
        {
            "train": Dataset.from_dict(
                {
                    "instruction": instructions,
                    "text": inputs,
                    "target": outputs,
                }
            )
        }
    )
    return dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Alpaca JSON into a saved xTuring-compatible dataset."
    )
    parser.add_argument(
        "--input-file",
        required=True,
        help="Path to the Alpaca JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the Hugging Face dataset will be saved.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of rows to convert.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")
    if args.limit is not None and args.limit < 0:
        raise ValueError("--limit must be non-negative")
    if output_dir.exists():
        if not output_dir.is_dir():
            raise FileExistsError(f"Output path exists and is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise FileExistsError(
                f"Output directory already exists and is not empty: {output_dir}"
            )

    rows = load_alpaca_rows(input_file)
    dataset = convert_alpaca_rows(rows, limit=args.limit)
    dataset.save_to_disk(str(output_dir))

    print(
        f"Saved {len(dataset['train'])} rows to {output_dir} with columns {list(OUTPUT_COLUMNS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
