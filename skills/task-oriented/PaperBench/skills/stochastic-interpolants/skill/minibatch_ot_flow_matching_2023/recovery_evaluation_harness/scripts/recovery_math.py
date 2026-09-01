from __future__ import annotations


def linear_predictions(points, weight):
    return [[weight * value for value in row] for row in points]


def mse(predictions, targets):
    values = []
    for pred, tgt in zip(predictions, targets):
        values.extend((p - u) ** 2 for p, u in zip(pred, tgt))
    return sum(values) / len(values)


def gradient_for_scalar_weight(points, targets, weight):
    values = []
    for row, tgt in zip(points, targets):
        for x, u in zip(row, tgt):
            values.append(2.0 * (weight * x - u) * x)
    return sum(values) / len(values)
