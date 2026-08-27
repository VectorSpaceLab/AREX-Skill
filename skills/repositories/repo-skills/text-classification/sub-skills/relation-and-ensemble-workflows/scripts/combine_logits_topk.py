#!/usr/bin/env python3
"""Combine exported logits with a weighted sum and emit top-k labels.

This helper intentionally avoids TensorFlow and original checkpoint directories.
It expects logits that have already been exported by compatible models.
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _fail(message: str) -> None:
    raise SystemExit("error: " + message)


def _load_json_text(text: str, name: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        _fail("{} is not valid JSON: {}".format(name, exc))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _is_number_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_number(item) for item in value)


def _parse_logits(raw: Any) -> List[List[List[float]]]:
    """Return logits shaped [models][examples][classes]."""
    if not isinstance(raw, list) or not raw:
        _fail("logits must be a non-empty JSON list")

    # Accept [examples][classes] as a single-model convenience.
    if _is_number_list(raw[0]):
        raw_models = [raw]
    elif isinstance(raw[0], list) and raw[0] and _is_number_list(raw[0][0]):
        raw_models = raw
    else:
        _fail("logits must be shaped [models][examples][classes] or [examples][classes]")

    parsed_models: List[List[List[float]]] = []
    expected_examples: Optional[int] = None
    expected_classes: Optional[int] = None

    for model_index, model in enumerate(raw_models):
        if not isinstance(model, list) or not model:
            _fail("model {} logits must be a non-empty list of examples".format(model_index))
        parsed_examples: List[List[float]] = []
        for example_index, row in enumerate(model):
            if not isinstance(row, list) or not row:
                _fail("model {} example {} must be a non-empty list of class scores".format(model_index, example_index))
            parsed_row: List[float] = []
            for class_index, value in enumerate(row):
                if not _is_number(value):
                    _fail("logits[{}][{}][{}] is not a finite number: {!r}".format(
                        model_index, example_index, class_index, value
                    ))
                parsed_row.append(float(value))
            if expected_classes is None:
                expected_classes = len(parsed_row)
            elif len(parsed_row) != expected_classes:
                _fail("all logits rows must have the same number of classes")
            parsed_examples.append(parsed_row)
        if expected_examples is None:
            expected_examples = len(parsed_examples)
        elif len(parsed_examples) != expected_examples:
            _fail("all models must have the same number of examples")
        parsed_models.append(parsed_examples)

    return parsed_models


def _parse_weights(value: Optional[str], num_models: int) -> List[float]:
    if value is None:
        return [1.0 for _ in range(num_models)]
    text = value.strip()
    if text.startswith("["):
        raw = _load_json_text(text, "--weights")
    else:
        raw = [part.strip() for part in text.split(",") if part.strip()]
    if not isinstance(raw, list):
        _fail("--weights must be a JSON list or comma-separated list")
    weights: List[float] = []
    for index, item in enumerate(raw):
        try:
            weight = float(item)
        except (TypeError, ValueError):
            _fail("weight {} is not numeric: {!r}".format(index, item))
        if not math.isfinite(weight):
            _fail("weight {} is not finite".format(index))
        weights.append(weight)
    if len(weights) != num_models:
        _fail("weights count ({}) must match model count ({})".format(len(weights), num_models))
    return weights


def _parse_index(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and (stripped.isdigit() or (stripped[0] in "+-" and stripped[1:].isdigit())):
            return int(stripped)
    return None


def _parse_label_map(value: Optional[str], num_classes: int) -> Dict[int, str]:
    if value is None:
        return {index: str(index) for index in range(num_classes)}
    raw = _load_json_text(value, "--label-map-json")
    label_map: Dict[int, str] = {}
    if isinstance(raw, list):
        for index, label in enumerate(raw):
            label_map[index] = str(label)
    elif isinstance(raw, dict):
        # Prefer index -> label dictionaries, but also accept label -> index.
        for key, label in raw.items():
            key_index = _parse_index(key)
            if key_index is not None:
                label_map[key_index] = str(label)
            else:
                value_index = _parse_index(label)
                if value_index is None:
                    _fail("label map item {!r}: {!r} is neither index->label nor label->index".format(key, label))
                label_map[value_index] = str(key)
    else:
        _fail("--label-map-json must be a list or object")
    for index in label_map:
        if index < 0 or index >= num_classes:
            _fail("label map index {} is outside class range [0, {})".format(index, num_classes))
    for index in range(num_classes):
        label_map.setdefault(index, str(index))
    return label_map


def _combine(models: List[List[List[float]]], weights: List[float]) -> List[List[float]]:
    num_examples = len(models[0])
    num_classes = len(models[0][0])
    combined: List[List[float]] = []
    for example_index in range(num_examples):
        row: List[float] = []
        for class_index in range(num_classes):
            score = 0.0
            for model_index, model in enumerate(models):
                score += weights[model_index] * model[example_index][class_index]
            row.append(score)
        combined.append(row)
    return combined


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Combine compatible exported logits with a weighted sum and output top-k labels as JSON."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--logits-json", help="JSON logits shaped [models][examples][classes] or [examples][classes].")
    group.add_argument("--logits-file", help="Path to a JSON file containing logits with the same accepted shapes.")
    parser.add_argument("--weights", help="Optional model weights as comma-separated values or a JSON list. Defaults to 1.0 per model.")
    parser.add_argument("--label-map-json", help="Optional index-to-label JSON object/list, or label-to-index object.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top classes per example to emit (default: 5).")
    parser.add_argument("--include-combined-logits", action="store_true", help="Include combined logits rows in the JSON output.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.logits_file:
        try:
            raw_text = Path(args.logits_file).read_text(encoding="utf-8")
        except OSError as exc:
            _fail("cannot read --logits-file: {}".format(exc))
        raw_logits = _load_json_text(raw_text, "--logits-file")
    else:
        raw_logits = _load_json_text(args.logits_json, "--logits-json")

    models = _parse_logits(raw_logits)
    num_models = len(models)
    num_examples = len(models[0])
    num_classes = len(models[0][0])
    if args.top_k <= 0:
        _fail("--top-k must be positive")
    if args.top_k > num_classes:
        _fail("--top-k ({}) cannot exceed number of classes ({})".format(args.top_k, num_classes))

    weights = _parse_weights(args.weights, num_models)
    label_map = _parse_label_map(args.label_map_json, num_classes)
    combined = _combine(models, weights)

    examples: List[Dict[str, Any]] = []
    for example_index, row in enumerate(combined):
        top_indices = sorted(range(num_classes), key=lambda idx: (-row[idx], idx))[:args.top_k]
        item: Dict[str, Any] = {
            "example_index": example_index,
            "top_k": [
                {"class_index": idx, "label": label_map[idx], "score": row[idx]}
                for idx in top_indices
            ],
        }
        if args.include_combined_logits:
            item["combined_logits"] = row
        examples.append(item)

    output: Dict[str, Any] = {
        "num_models": num_models,
        "num_examples": num_examples,
        "num_classes": num_classes,
        "weights": weights,
        "examples": examples,
    }
    json.dump(output, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
