#!/usr/bin/env python3
"""Online hashed logistic regression for Criteo-like CSV rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Iterable


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def parse_binary_label(raw: str) -> float:
    value = str(raw).strip().lower()
    if value in {"1", "true", "yes", "y"}:
        return 1.0
    if value in {"0", "false", "no", "n"}:
        return 0.0
    try:
        return 1.0 if float(value) > 0 else 0.0
    except ValueError as exc:
        raise ValueError(f"Label value {raw!r} is not binary-like") from exc


def normalize_value(value: object, missing_token: str) -> str:
    if value is None:
        return missing_token
    text = str(value).strip()
    return text if text else missing_token


def stable_hash(token: str, bits: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") & ((1 << bits) - 1)


def feature_indices(
    row: dict[str | None, str],
    *,
    bits: int,
    label_column: str,
    id_column: str,
    missing_token: str,
) -> list[int]:
    if None in row:
        raise ValueError("Malformed CSV row has more values than header fields")

    indices = [0]  # bias term
    ignored = {label_column, id_column}
    for field, value in row.items():
        if field in ignored:
            continue
        token = f"{field}={normalize_value(value, missing_token)}"
        indices.append(stable_hash(token, bits))
    return indices


def sigmoid(score: float) -> float:
    bounded = max(min(score, 35.0), -35.0)
    return 1.0 / (1.0 + math.exp(-bounded))


def logloss(probability: float, label: float) -> float:
    clipped = max(min(probability, 1.0 - 1e-15), 1e-15)
    return -math.log(clipped) if label == 1.0 else -math.log(1.0 - clipped)


def predict_probability(indices: Iterable[int], weights: DefaultDict[int, float]) -> float:
    return sigmoid(sum(weights.get(i, 0.0) for i in indices))


def update_weights(
    weights: DefaultDict[int, float],
    counts: DefaultDict[int, float],
    indices: Iterable[int],
    probability: float,
    label: float,
    alpha: float,
) -> None:
    gradient = probability - label
    for index in indices:
        weights[index] -= gradient * alpha / (math.sqrt(counts[index]) + 1.0)
        counts[index] += 1.0


def validate_training_header(fieldnames: list[str] | None, label_column: str, id_column: str) -> None:
    if not fieldnames:
        raise ValueError("CSV file has no header row")
    missing = [name for name in (label_column, id_column) if name not in fieldnames]
    if missing:
        raise ValueError(f"Training CSV is missing required column(s): {', '.join(missing)}")


def validate_test_header(fieldnames: list[str] | None, id_column: str) -> None:
    if not fieldnames:
        raise ValueError("CSV file has no header row")
    if id_column not in fieldnames:
        raise ValueError(f"Test CSV is missing required id column: {id_column}")


def train_one_epoch(
    train_path: Path,
    *,
    weights: DefaultDict[int, float],
    counts: DefaultDict[int, float],
    bits: int,
    alpha: float,
    label_column: str,
    id_column: str,
    missing_token: str,
) -> tuple[int, float]:
    rows_seen = 0
    total_loss = 0.0
    with train_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        validate_training_header(reader.fieldnames, label_column, id_column)
        for row in reader:
            if not any(row.values()):
                continue
            label = parse_binary_label(row[label_column])
            indices = feature_indices(
                row,
                bits=bits,
                label_column=label_column,
                id_column=id_column,
                missing_token=missing_token,
            )
            probability = predict_probability(indices, weights)
            total_loss += logloss(probability, label)
            update_weights(weights, counts, indices, probability, label, alpha)
            rows_seen += 1
    return rows_seen, total_loss


def write_predictions(
    test_path: Path,
    output_path: Path,
    *,
    weights: DefaultDict[int, float],
    bits: int,
    label_column: str,
    id_column: str,
    missing_token: str,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    with test_path.open(newline="", encoding="utf-8") as input_handle, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as output_handle:
        reader = csv.DictReader(input_handle)
        validate_test_header(reader.fieldnames, id_column)
        writer = csv.writer(output_handle)
        writer.writerow([id_column, "Predicted"])
        for row in reader:
            if not any(row.values()):
                continue
            row_id = row[id_column]
            indices = feature_indices(
                row,
                bits=bits,
                label_column=label_column,
                id_column=id_column,
                missing_token=missing_token,
            )
            probability = predict_probability(indices, weights)
            writer.writerow([row_id, f"{probability:.6f}"])
            rows_written += 1
    return rows_written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train an online hashed logistic model on Criteo-like CSVs and write probabilities.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train", required=True, type=Path, help="Training CSV with Label/Id columns.")
    parser.add_argument("--test", required=True, type=Path, help="Test CSV with an Id column.")
    parser.add_argument("--output", required=True, type=Path, help="Output submission CSV.")
    parser.add_argument("--bits", type=positive_int, default=20, help="Log2 feature hash space size.")
    parser.add_argument("--alpha", type=positive_float, default=0.1, help="SGD learning rate.")
    parser.add_argument("--epochs", type=positive_int, default=1, help="Number of passes over the training CSV.")
    parser.add_argument("--label-column", default="Label", help="Training label column name.")
    parser.add_argument("--id-column", default="Id", help="Row id column name.")
    parser.add_argument("--missing-token", default="__missing__", help="Token used for blank feature values.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    weights: DefaultDict[int, float] = defaultdict(float)
    counts: DefaultDict[int, float] = defaultdict(float)

    for epoch in range(1, args.epochs + 1):
        rows_seen, total_loss = train_one_epoch(
            args.train,
            weights=weights,
            counts=counts,
            bits=args.bits,
            alpha=args.alpha,
            label_column=args.label_column,
            id_column=args.id_column,
            missing_token=args.missing_token,
        )
        if rows_seen == 0:
            raise ValueError(f"No training rows read from {args.train}")
        print(f"epoch {epoch}/{args.epochs}: rows={rows_seen} mean_logloss={total_loss / rows_seen:.6f}")

    rows_written = write_predictions(
        args.test,
        args.output,
        weights=weights,
        bits=args.bits,
        label_column=args.label_column,
        id_column=args.id_column,
        missing_token=args.missing_token,
    )
    print(f"Wrote {rows_written} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
