#!/usr/bin/env python3
"""Conditional Flow Matching loss helpers."""

import argparse
import json
import math
from typing import Iterable, List, Sequence

Vector = List[float]


def _vector(values: Iterable[float]) -> Vector:
    return [float(value) for value in values]


def _matrix(values: Iterable[Iterable[float]]) -> List[Vector]:
    return [_vector(row) for row in values]


def squared_errors(predictions: Sequence[Sequence[float]], targets: Sequence[Sequence[float]]) -> List[float]:
    if len(predictions) != len(targets):
        raise ValueError("predictions and targets must have the same batch size")
    errors = []
    for prediction, target in zip(predictions, targets):
        if len(prediction) != len(target):
            raise ValueError("prediction and target dimensions must match")
        row_error = 0.0
        for pred_value, target_value in zip(prediction, target):
            pred_value = float(pred_value)
            target_value = float(target_value)
            if not math.isfinite(pred_value) or not math.isfinite(target_value):
                raise ValueError("predictions and targets must be finite")
            row_error += (pred_value - target_value) ** 2
        errors.append(row_error)
    return errors


def mean_loss(predictions: Sequence[Sequence[float]], targets: Sequence[Sequence[float]], weights: Sequence[float] = None) -> dict:
    errors = squared_errors(predictions, targets)
    if not errors:
        raise ValueError("at least one sample is required")
    if weights is None:
        loss = sum(errors) / len(errors)
    else:
        if len(weights) != len(errors):
            raise ValueError("weights must match batch size")
        clean_weights = [float(weight) for weight in weights]
        if any((not math.isfinite(weight)) or weight < 0.0 for weight in clean_weights):
            raise ValueError("weights must be finite and nonnegative")
        total_weight = sum(clean_weights)
        if total_weight <= 0.0:
            raise ValueError("total weight must be positive")
        loss = sum(weight * error for weight, error in zip(clean_weights, errors)) / total_weight
    return {
        "loss": loss,
        "per_sample_squared_error": errors,
        "sample_count": len(errors),
        "finite": math.isfinite(loss),
    }


def scale_predictions(targets: Sequence[Sequence[float]], scale: float) -> List[Vector]:
    scale = float(scale)
    return [[scale * float(value) for value in row] for row in targets]


def one_parameter_update(targets: Sequence[Sequence[float]], scale: float, learning_rate: float) -> dict:
    predictions = scale_predictions(targets, scale)
    before = mean_loss(predictions, targets)["loss"]
    target_norm = sum(sum(float(value) ** 2 for value in row) for row in targets)
    batch_size = max(1, len(targets))
    gradient = 2.0 * (float(scale) - 1.0) * target_norm / batch_size
    new_scale = float(scale) - float(learning_rate) * gradient
    after = mean_loss(scale_predictions(targets, new_scale), targets)["loss"]
    return {
        "loss_before": before,
        "loss_after": after,
        "scale_before": float(scale),
        "scale_after": new_scale,
        "gradient": gradient,
        "updated": new_scale != float(scale),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", help="JSON matrix")
    parser.add_argument("--targets", required=True, help="JSON matrix")
    parser.add_argument("--weights", help="JSON vector")
    parser.add_argument("--scale", type=float, help="Create predictions by scaling targets")
    args = parser.parse_args()
    targets = _matrix(json.loads(args.targets))
    if args.predictions:
        predictions = _matrix(json.loads(args.predictions))
    elif args.scale is not None:
        predictions = scale_predictions(targets, args.scale)
    else:
        raise ValueError("provide --predictions or --scale")
    weights = json.loads(args.weights) if args.weights else None
    print(json.dumps(mean_loss(predictions, targets, weights), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
