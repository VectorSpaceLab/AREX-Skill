#!/usr/bin/env python3
"""Standard-library TeCoA contrastive objective utilities."""

from __future__ import annotations

import argparse
import json
import math
from typing import Sequence


def _as_matrix(name: str, value: Sequence[Sequence[float]]) -> list[list[float]]:
    matrix = [[float(cell) for cell in row] for row in value]
    if not matrix or not matrix[0]:
        raise ValueError(f"{name} must be a non-empty matrix")
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError(f"{name} rows must have equal length")
    return matrix


def _normalize_rows(matrix: list[list[float]]) -> list[list[float]]:
    normalized = []
    for row in matrix:
        norm = math.sqrt(sum(value * value for value in row))
        if norm <= 0.0:
            raise ValueError("embedding rows must be non-zero")
        normalized.append([value / norm for value in row])
    return normalized


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _logsumexp(values: Sequence[float]) -> float:
    peak = max(values)
    return peak + math.log(sum(math.exp(value - peak) for value in values))


def compute_tecoa_metrics(image_embeddings, text_embeddings, labels, temperature: float = 0.07) -> dict:
    images = _as_matrix("image_embeddings", image_embeddings)
    texts = _as_matrix("text_embeddings", text_embeddings)
    if len(images[0]) != len(texts[0]):
        raise ValueError("image and text embedding dimensions must match")
    labels = [int(label) for label in labels]
    if len(labels) != len(images):
        raise ValueError("labels length must equal image batch size")
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if any(label < 0 or label >= len(texts) for label in labels):
        raise ValueError("labels must index text embeddings")
    norm_images = _normalize_rows(images)
    norm_texts = _normalize_rows(texts)
    logits = [[_dot(image, text) / temperature for text in norm_texts] for image in norm_images]
    losses = []
    predictions = []
    margins = []
    for row, label in zip(logits, labels):
        losses.append(_logsumexp(row) - row[label])
        pred = max(range(len(row)), key=lambda idx: row[idx])
        predictions.append(pred)
        wrong = [score for idx, score in enumerate(row) if idx != label]
        margins.append(row[label] - max(wrong) if wrong else float("inf"))
    return {
        "logits": logits,
        "loss": sum(losses) / len(losses),
        "accuracy": sum(int(pred == label) for pred, label in zip(predictions, labels)) / len(labels),
        "predictions": predictions,
        "margins": margins,
        "mean_margin": sum(margins) / len(margins),
        "temperature": temperature,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON file with image_embeddings, text_embeddings, labels")
    parser.add_argument("--output", help="Optional JSON output path")
    parser.add_argument("--temperature", type=float, default=None)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    temperature = args.temperature if args.temperature is not None else payload.get("temperature", 0.07)
    result = compute_tecoa_metrics(payload["image_embeddings"], payload["text_embeddings"], payload["labels"], temperature)
    text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
