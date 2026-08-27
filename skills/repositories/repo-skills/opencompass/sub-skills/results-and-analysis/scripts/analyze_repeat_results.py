#!/usr/bin/env python3
"""Analyze repeated prediction text in small OpenCompass-like fixtures.

This helper is intentionally self-contained. It reads JSON, JSONL, or CSV files
that contain prediction records and reports duplicate predictions, repeated
lines, repeated n-grams, and long-text outliers. It is for lightweight diagnosis,
not a replacement for OpenCompass native repeat analysis on full work dirs.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

PREDICTION_KEYS = (
    "prediction",
    "pred",
    "output",
    "response",
    "text",
    "answer",
)
TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def load_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue
                value = json.loads(line)
                records.append(normalize_record(value, line_number - 1))
        return records
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as file:
            return [normalize_record(row, index) for index, row in enumerate(csv.DictReader(file))]
    if suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        return list(iter_json_records(value))
    raise ValueError(f"Unsupported file extension: {suffix}. Use .json, .jsonl, or .csv")


def iter_json_records(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield normalize_record(item, index)
        return
    if isinstance(value, dict):
        if "predictions" in value and isinstance(value["predictions"], list):
            for index, item in enumerate(value["predictions"]):
                yield normalize_record(item, index)
            return
        if all(isinstance(item, dict) for item in value.values()):
            for key, item in value.items():
                record = normalize_record(item, key)
                record.setdefault("sample_id", key)
                yield record
            return
        yield normalize_record(value, 0)
        return
    yield normalize_record({"prediction": str(value)}, 0)


def normalize_record(value: Any, fallback_id: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        record = dict(value)
    else:
        record = {"prediction": value}
    record.setdefault("sample_id", fallback_id)
    prediction = find_prediction(record)
    record["_prediction_text"] = prediction
    return record


def find_prediction(record: dict[str, Any]) -> str:
    for key in PREDICTION_KEYS:
        if key in record:
            return stringify_prediction(record[key])
    for key, value in record.items():
        if key.lower() in PREDICTION_KEYS:
            return stringify_prediction(value)
    return stringify_prediction(record)


def stringify_prediction(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def repeated_ngram_stats(tokens: list[str], ngram_size: int) -> tuple[str | None, int, float]:
    if len(tokens) < ngram_size:
        return None, 0, 0.0
    ngrams = [tuple(tokens[index:index + ngram_size]) for index in range(len(tokens) - ngram_size + 1)]
    counts = Counter(ngrams)
    ngram, count = counts.most_common(1)[0]
    return " ".join(ngram), count, count / max(len(ngrams), 1)


def repeated_line_ratio(text: str) -> float:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    counts = Counter(lines)
    repeated = sum(count for count in counts.values() if count > 1)
    return repeated / len(lines)


def analyze(records: list[dict[str, Any]], ngram_size: int, top_k: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    lengths: list[int] = []
    prediction_counter: Counter[str] = Counter()

    for record in records:
        text = record["_prediction_text"]
        tokens = tokenize(text)
        lengths.append(len(tokens))
        prediction_counter[text.strip()] += 1
        ngram, ngram_count, ngram_ratio = repeated_ngram_stats(tokens, ngram_size)
        rows.append({
            "sample_id": record.get("sample_id"),
            "token_length": len(tokens),
            "char_length": len(text),
            "line_repeat_ratio": repeated_line_ratio(text),
            "top_ngram": ngram,
            "top_ngram_count": ngram_count,
            "top_ngram_ratio": ngram_ratio,
            "preview": text.replace("\n", " ")[:160],
        })

    if lengths:
        mean_length = statistics.mean(lengths)
        median_length = statistics.median(lengths)
        p90_length = percentile(lengths, 90)
        long_threshold = max(p90_length, mean_length * 2)
    else:
        mean_length = median_length = p90_length = long_threshold = 0

    duplicates = [
        {"count": count, "preview": text[:160]}
        for text, count in prediction_counter.most_common(top_k)
        if text and count > 1
    ]

    suspicious = sorted(
        [
            row for row in rows
            if row["top_ngram_count"] >= 4
            or row["top_ngram_ratio"] >= 0.20
            or row["line_repeat_ratio"] >= 0.35
            or row["token_length"] > long_threshold
        ],
        key=lambda row: (
            row["top_ngram_ratio"],
            row["line_repeat_ratio"],
            row["token_length"],
        ),
        reverse=True,
    )[:top_k]

    return {
        "num_records": len(records),
        "lengths": {
            "mean_tokens": round(mean_length, 2),
            "median_tokens": median_length,
            "p90_tokens": p90_length,
            "long_text_threshold_tokens": round(long_threshold, 2),
        },
        "duplicate_predictions": duplicates,
        "suspicious_samples": suspicious,
    }


def percentile(values: list[int], percent: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze repeated prediction text in JSON/JSONL/CSV fixtures.")
    parser.add_argument("input", type=Path, help="Prediction fixture path (.json, .jsonl, or .csv).")
    parser.add_argument("--ngram-size", type=int, default=8, help="N-gram size for repetition checks.")
    parser.add_argument("--top-k", type=int, default=10, help="Maximum duplicate/suspicious rows to report.")
    parser.add_argument("--out", type=Path, help="Optional JSON report output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.ngram_size < 1:
        raise ValueError("--ngram-size must be positive")
    records = load_records(args.input)
    report = analyze(records, args.ngram_size, args.top_k)
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
