#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


def _is_one_hot_row(row):
    return all(value in (0, 1) for value in row) and sum(row) == 1


def validate_probabilities(probabilities, tolerance=1e-6):
    if not probabilities or not isinstance(probabilities, list):
        raise ValueError("probabilities must be a non-empty list of rows")
    width = len(probabilities[0])
    if width < 2:
        raise ValueError("probability rows must contain at least two classes")
    for row_index, row in enumerate(probabilities):
        if len(row) != width:
            raise ValueError(f"row {row_index} has inconsistent class count")
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in row):
            raise ValueError(f"row {row_index} contains non-finite values")
        if any(value < -tolerance for value in row):
            raise ValueError(f"row {row_index} contains negative probabilities")
        if abs(sum(row) - 1.0) > tolerance:
            raise ValueError(f"row {row_index} probabilities sum to {sum(row)}")
    return width


def labels_to_one_hot(labels, class_count):
    if len(labels) == 0:
        raise ValueError("labels must be non-empty")
    one_hot = []
    for index, label in enumerate(labels):
        if isinstance(label, int):
            if label < 0 or label >= class_count:
                raise ValueError(f"label {index} out of range")
            row = [0.0] * class_count
            row[label] = 1.0
            one_hot.append(row)
        elif isinstance(label, list):
            if len(label) != class_count or not _is_one_hot_row(label):
                raise ValueError(f"label row {index} is not one-hot")
            one_hot.append([float(value) for value in label])
        else:
            raise ValueError(f"label {index} must be int or one-hot row")
    return one_hot


def compute_el2n(probabilities, labels):
    class_count = validate_probabilities(probabilities)
    if len(probabilities) != len(labels):
        raise ValueError("probability and label counts differ")
    one_hot = labels_to_one_hot(labels, class_count)
    scores = []
    for probs, target in zip(probabilities, one_hot):
        squared = [(prob - truth) ** 2 for prob, truth in zip(probs, target)]
        scores.append(math.sqrt(sum(squared)))
    return scores


def average_el2n(probability_runs, labels):
    if not probability_runs:
        raise ValueError("probability_runs must be non-empty")
    per_run = [compute_el2n(run, labels) for run in probability_runs]
    example_count = len(per_run[0])
    if any(len(run_scores) != example_count for run_scores in per_run):
        raise ValueError("runs contain different example counts")
    return [sum(run_scores[i] for run_scores in per_run) / len(per_run) for i in range(example_count)]


def compute_grand(gradient_vectors):
    if not gradient_vectors:
        raise ValueError("gradient_vectors must be non-empty")
    scores = []
    for index, vector in enumerate(gradient_vectors):
        if not vector or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector):
            raise ValueError(f"gradient vector {index} is invalid")
        scores.append(math.sqrt(sum(value * value for value in vector)))
    return scores


def fixture_payload():
    return {
        "probabilities": [[0.8, 0.2], [0.45, 0.55], [0.1, 0.9]],
        "labels": [0, 0, 1],
        "gradient_vectors": [[3, 4], [1, 2, 2], [0, 0, 0]],
    }


def run_payload(payload):
    if "probability_runs" in payload:
        el2n = average_el2n(payload["probability_runs"], payload["labels"])
        run_count = len(payload["probability_runs"])
    else:
        el2n = compute_el2n(payload["probabilities"], payload["labels"])
        run_count = 1
    result = {"ok": True, "el2n_scores": el2n, "run_count": run_count}
    if "gradient_vectors" in payload:
        result["grand_scores"] = compute_grand(payload["gradient_vectors"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    payload = fixture_payload() if args.fixture else json.loads(args.input.read_text())
    result = run_payload(payload)
    text = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
