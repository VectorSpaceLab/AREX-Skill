#!/usr/bin/env python3
"""Generate tiny fixtures for the kaggle-linear-models helpers."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DENSE_TRAIN_ROWS = [
    [2.0, 1.8, 1.2, 0.8],
    [2.2, 1.6, 1.1, 1.0],
    [1.8, 1.7, 1.0, 0.9],
    [2.4, 1.9, 1.3, 1.1],
    [-2.0, -1.8, -1.2, -0.8],
    [-2.2, -1.6, -1.1, -1.0],
    [-1.8, -1.7, -1.0, -0.9],
    [-2.4, -1.9, -1.3, -1.1],
]
DENSE_TRAIN_LABELS = [1, 1, 1, 1, 0, 0, 0, 0]
DENSE_TEST_ROWS = [
    [2.1, 1.7, 1.1, 0.9],
    [-2.1, -1.7, -1.1, -0.9],
    [0.0, 0.0, 0.0, 0.0],
    [1.5, 1.2, 0.7, 0.6],
]

HASHED_HEADERS = ["Id", "Label", "I1", "I2", "C1", "C2", "C3"]
HASHED_TRAIN_ROWS = [
    {"Id": "1", "Label": "1", "I1": "357", "I2": "", "C1": "red", "C2": "small", "C3": "east"},
    {"Id": "2", "Label": "0", "I1": "128", "I2": "44", "C1": "blue", "C2": "medium", "C3": "west"},
    {"Id": "3", "Label": "1", "I1": "204", "I2": "18", "C1": "red", "C2": "large", "C3": "east"},
    {"Id": "4", "Label": "0", "I1": "", "I2": "99", "C1": "green", "C2": "small", "C3": "north"},
    {"Id": "5", "Label": "1", "I1": "512", "I2": "11", "C1": "blue", "C2": "medium", "C3": "south"},
    {"Id": "6", "Label": "0", "I1": "64", "I2": "", "C1": "yellow", "C2": "small", "C3": "west"},
    {"Id": "7", "Label": "1", "I1": "256", "I2": "23", "C1": "red", "C2": "medium", "C3": "east"},
    {"Id": "8", "Label": "0", "I1": "32", "I2": "77", "C1": "green", "C2": "large", "C3": "north"},
]
HASHED_TEST_ROWS = [
    {"Id": "101", "I1": "360", "I2": "", "C1": "purple", "C2": "small", "C3": "east"},
    {"Id": "102", "I1": "120", "I2": "50", "C1": "blue", "C2": "xlarge", "C3": "west"},
    {"Id": "103", "I1": "", "I2": "75", "C1": "red", "C2": "medium", "C3": "central"},
    {"Id": "104", "I1": "280", "I2": "15", "C1": "green", "C2": "small", "C3": "north"},
]

CATEGORICAL_HEADERS = ["id", "ACTION", "role", "department", "site", "grade"]
CATEGORICAL_TRAIN_ROWS = [
    {"id": "1", "ACTION": "1", "role": "analyst", "department": "sales", "site": "east", "grade": "G1"},
    {"id": "2", "ACTION": "0", "role": "analyst", "department": "ops", "site": "west", "grade": "G1"},
    {"id": "3", "ACTION": "1", "role": "manager", "department": "sales", "site": "east", "grade": "G2"},
    {"id": "4", "ACTION": "0", "role": "assistant", "department": "ops", "site": "north", "grade": "G1"},
    {"id": "5", "ACTION": "1", "role": "analyst", "department": "finance", "site": "south", "grade": "G2"},
    {"id": "6", "ACTION": "0", "role": "assistant", "department": "finance", "site": "west", "grade": "G1"},
    {"id": "7", "ACTION": "1", "role": "manager", "department": "sales", "site": "north", "grade": "G3"},
    {"id": "8", "ACTION": "0", "role": "assistant", "department": "ops", "site": "south", "grade": "G2"},
]
CATEGORICAL_TEST_ROWS = [
    {"id": "101", "role": "analyst", "department": "sales", "site": "remote", "grade": "G1"},
    {"id": "102", "role": "manager", "department": "support", "site": "west", "grade": "G2"},
    {"id": "103", "role": "assistant", "department": "ops", "site": "east", "grade": "G1"},
    {"id": "104", "role": "analyst", "department": "finance", "site": "north", "grade": "G3"},
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate tiny dense, hashed, and categorical CSV fixtures for smoke tests.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to write the fixture tree into.")
    return parser


def write_dense_fixture(root: Path) -> list[Path]:
    dense_dir = root / "dense"
    dense_dir.mkdir(parents=True, exist_ok=True)

    train_path = dense_dir / "train.csv"
    labels_path = dense_dir / "train_labels.csv"
    test_path = dense_dir / "test.csv"

    with train_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(DENSE_TRAIN_ROWS)

    with labels_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for label in DENSE_TRAIN_LABELS:
            writer.writerow([label])

    with test_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(DENSE_TEST_ROWS)

    return [train_path, labels_path, test_path]


def write_dict_fixture(root: Path, *, name: str, headers: list[str], train_rows: list[dict[str, str]], test_rows: list[dict[str, str]]) -> list[Path]:
    fixture_dir = root / name
    fixture_dir.mkdir(parents=True, exist_ok=True)

    train_path = fixture_dir / "train.csv"
    test_path = fixture_dir / "test.csv"

    with train_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(train_rows)

    with test_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[column for column in headers if column != "Label" and column != "ACTION"])
        writer.writeheader()
        writer.writerows(test_rows)

    return [train_path, test_path]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.output_dir
    root.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    created.extend(write_dense_fixture(root))
    created.extend(write_dict_fixture(root, name="hashed", headers=HASHED_HEADERS, train_rows=HASHED_TRAIN_ROWS, test_rows=HASHED_TEST_ROWS))
    created.extend(
        write_dict_fixture(
            root,
            name="categorical",
            headers=CATEGORICAL_HEADERS,
            train_rows=CATEGORICAL_TRAIN_ROWS,
            test_rows=CATEGORICAL_TEST_ROWS,
        )
    )

    for path in created:
        print(path)
    print(f"Wrote {len(created)} fixture files under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
