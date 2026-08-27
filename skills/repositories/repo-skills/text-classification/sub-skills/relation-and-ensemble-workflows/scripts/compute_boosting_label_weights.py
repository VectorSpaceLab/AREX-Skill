#!/usr/bin/env python3
"""Compute validation label accuracies and optional boosting batch weights.

This is a safe, TensorFlow-free adaptation of the repo's boosting idea:
collect per-label validation accuracy from logits, then weight low-accuracy
labels more heavily with ``min(max_weight, 1 / (accuracy + epsilon))``.
"""

import argparse
import json
import math
import sys
from typing import Any, Dict, Iterable, List, Tuple


def _fail(message: str) -> None:
    raise SystemExit("error: " + message)


def _load_json_arg(value: str, name: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        _fail("{} is not valid JSON: {}".format(name, exc))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _parse_label(value: Any, name: str) -> int:
    if isinstance(value, bool):
        _fail("{} contains boolean label {!r}; sparse labels must be class indices".format(name, value))
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and (stripped.isdigit() or (stripped[0] in "+-" and stripped[1:].isdigit())):
            return int(stripped)
    _fail("{} contains non-integer sparse label {!r}".format(name, value))
    raise AssertionError("unreachable")


def _parse_logits(raw: Any) -> List[List[float]]:
    if not isinstance(raw, list) or not raw:
        _fail("--logits-json must be a non-empty list of examples")
    rows: List[List[float]] = []
    width = None
    for row_index, row in enumerate(raw):
        if not isinstance(row, list) or not row:
            _fail("logits row {} must be a non-empty list of class scores".format(row_index))
        parsed: List[float] = []
        for col_index, value in enumerate(row):
            if not _is_number(value):
                _fail("logits[{}][{}] is not a finite number: {!r}".format(row_index, col_index, value))
            parsed.append(float(value))
        if width is None:
            width = len(parsed)
        elif len(parsed) != width:
            _fail("all logits rows must have the same class count")
        rows.append(parsed)
    return rows


def _argmax(row: List[float]) -> int:
    best_index = 0
    best_value = row[0]
    for index, value in enumerate(row[1:], start=1):
        if value > best_value:
            best_index = index
            best_value = value
    return best_index


def _compute_stats(logits: List[List[float]], labels: List[int]) -> Tuple[Dict[int, Dict[str, int]], List[int]]:
    if len(logits) != len(labels):
        _fail("logits example count ({}) must match labels count ({})".format(len(logits), len(labels)))
    num_classes = len(logits[0])
    stats: Dict[int, Dict[str, int]] = {}
    predictions: List[int] = []
    for index, (row, label) in enumerate(zip(logits, labels)):
        if label < 0 or label >= num_classes:
            _fail("labels[{}]={} is outside class range [0, {})".format(index, label, num_classes))
        pred = _argmax(row)
        predictions.append(pred)
        item = stats.setdefault(label, {"count": 0, "correct": 0})
        item["count"] += 1
        if pred == label:
            item["correct"] += 1
    return stats, predictions


def _accuracy_map(stats: Dict[int, Dict[str, int]]) -> Dict[int, float]:
    accuracies: Dict[int, float] = {}
    for label, item in stats.items():
        accuracies[label] = float(item["correct"]) / float(item["count"])
    return accuracies


def _batch_weights(answer_list: Iterable[int], accuracies: Dict[int, float], max_weight: float, epsilon: float,
                   missing_accuracy: float) -> List[float]:
    weights: List[float] = []
    for index, label in enumerate(answer_list):
        if label in accuracies:
            accuracy = accuracies[label]
        elif missing_accuracy is not None:
            accuracy = missing_accuracy
        else:
            _fail("answer-list label {} at position {} was not observed in validation; pass --missing-accuracy to use a fallback".format(label, index))
        weights.append(min(max_weight, 1.0 / (accuracy + epsilon)))
    return weights


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Compute per-label validation accuracy and optional capped boosting batch weights from JSON logits."
    )
    parser.add_argument("--logits-json", required=True,
                        help="JSON array shaped [examples][classes] containing validation logits or additive scores.")
    parser.add_argument("--labels-json", required=True,
                        help="JSON array shaped [examples] containing sparse integer validation labels.")
    parser.add_argument("--answer-list-json",
                        help="Optional JSON array of sparse labels for the current training batch; emits batch_weights.")
    parser.add_argument("--max-weight", type=float, default=1.5,
                        help="Cap for each example weight (default: 1.5, matching the source pattern).")
    parser.add_argument("--epsilon", type=float, default=0.001,
                        help="Small positive value added to label accuracy before inversion (default: 0.001).")
    parser.add_argument("--missing-accuracy", type=float, default=None,
                        help="Fallback accuracy for answer-list labels absent from validation. By default this is an error.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.max_weight <= 0:
        _fail("--max-weight must be positive")
    if args.epsilon <= 0:
        _fail("--epsilon must be positive")
    if args.missing_accuracy is not None and not (0.0 <= args.missing_accuracy <= 1.0):
        _fail("--missing-accuracy must be between 0 and 1")

    logits = _parse_logits(_load_json_arg(args.logits_json, "--logits-json"))
    labels_raw = _load_json_arg(args.labels_json, "--labels-json")
    if not isinstance(labels_raw, list) or not labels_raw:
        _fail("--labels-json must be a non-empty list")
    labels = [_parse_label(value, "--labels-json") for value in labels_raw]

    stats, predictions = _compute_stats(logits, labels)
    accuracies = _accuracy_map(stats)

    output: Dict[str, Any] = {
        "label_accuracy": {str(label): accuracies[label] for label in sorted(accuracies)},
        "label_stats": {str(label): stats[label] for label in sorted(stats)},
        "predictions": predictions,
        "parameters": {"max_weight": args.max_weight, "epsilon": args.epsilon},
    }

    if args.answer_list_json is not None:
        answers_raw = _load_json_arg(args.answer_list_json, "--answer-list-json")
        if not isinstance(answers_raw, list):
            _fail("--answer-list-json must be a list when provided")
        answers = [_parse_label(value, "--answer-list-json") for value in answers_raw]
        output["batch_weights"] = _batch_weights(
            answers, accuracies, args.max_weight, args.epsilon, args.missing_accuracy
        )

    json.dump(output, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
