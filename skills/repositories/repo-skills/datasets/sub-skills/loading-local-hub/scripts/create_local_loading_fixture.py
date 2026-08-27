#!/usr/bin/env python3
"""Create a tiny offline fixture for testing Hugging Face Datasets local loading.

The script writes train/validation/test CSV files and can print a matching
`load_dataset("csv", ...)` example. It does not import datasets, use the
network, or depend on a source checkout.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROWS = {
    "train": [
        {"id": 0, "text": "great movie", "label": 1},
        {"id": 1, "text": "slow pacing", "label": 0},
        {"id": 2, "text": "excellent acting", "label": 1},
    ],
    "validation": [
        {"id": 100, "text": "mixed feelings", "label": 0},
        {"id": 101, "text": "pleasant surprise", "label": 1},
    ],
    "test": [
        {"id": 200, "text": "worth watching", "label": 1},
        {"id": 201, "text": "not for me", "label": 0},
    ],
}


def write_split_csv(output_dir: Path, split: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{split}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["id", "text", "label"])
        writer.writeheader()
        writer.writerows(ROWS[split])
    return csv_path


def write_readme(output_dir: Path) -> Path:
    readme_path = output_dir / "README.md"
    summary = {
        "description": "Offline local loading fixture for datasets load_dataset('csv', ...).",
        "splits": {split: len(rows) for split, rows in ROWS.items()},
        "columns": {"id": "int64", "text": "string", "label": "int64"},
    }
    readme_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return readme_path


def print_example(output_dir: Path) -> None:
    print(
        f'''from datasets import Features, Value, load_dataset

features = Features({{"id": Value("int64"), "text": Value("string"), "label": Value("int64")}})
data_files = {{
    "train": "{(output_dir / 'train.csv').as_posix()}",
    "validation": "{(output_dir / 'validation.csv').as_posix()}",
    "test": "{(output_dir / 'test.csv').as_posix()}",
}}

ds = load_dataset("csv", data_files=data_files, features=features)
train = load_dataset("csv", data_files=data_files, features=features, split="train")
print(ds)
print(train[0])'''
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a deterministic multi-split CSV fixture for offline datasets loading examples."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets-loading-fixture"),
        help="Directory where train.csv, validation.csv, test.csv, and README.md will be written.",
    )
    parser.add_argument(
        "--print-example",
        action="store_true",
        help="Print a self-contained load_dataset('csv', ...) example for the generated fixture.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output.expanduser().resolve()
    written = [write_split_csv(output_dir, split) for split in ("train", "validation", "test")]
    written.append(write_readme(output_dir))

    print(f"Wrote local loading fixture to: {output_dir}")
    for path in written:
        print(f"- {path.name}")

    if args.print_example:
        print()
        print_example(output_dir)


if __name__ == "__main__":
    main()
