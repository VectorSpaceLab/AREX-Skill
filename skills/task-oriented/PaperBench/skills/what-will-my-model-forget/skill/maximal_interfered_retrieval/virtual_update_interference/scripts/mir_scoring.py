from __future__ import annotations

import math
from typing import Mapping, Sequence

Vector = list[float]
Example = Mapping[str, object]


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def dot(weights: Sequence[float], features: Sequence[float]) -> float:
    return sum(float(w) * float(x) for w, x in zip(weights, features))


def logistic_loss(params: Mapping[str, object], example: Example) -> float:
    weights = [float(value) for value in params["weights"]]
    bias = float(params.get("bias", 0.0))
    features = [float(value) for value in example["features"]]
    label = int(example["label"])
    probability = min(max(sigmoid(dot(weights, features) + bias), 1e-12), 1.0 - 1e-12)
    return -(label * math.log(probability) + (1 - label) * math.log(1.0 - probability))


def batch_gradient(params: Mapping[str, object], batch: Sequence[Example]) -> dict:
    weights = [float(value) for value in params["weights"]]
    if not batch:
        return {"weights": [0.0 for _ in weights], "bias": 0.0}
    grad_weights = [0.0 for _ in weights]
    grad_bias = 0.0
    for example in batch:
        features = [float(value) for value in example["features"]]
        label = int(example["label"])
        prediction = sigmoid(dot(weights, features) + float(params.get("bias", 0.0)))
        error = prediction - label
        for index, feature in enumerate(features):
            grad_weights[index] += error * feature
        grad_bias += error
    scale = 1.0 / len(batch)
    return {"weights": [value * scale for value in grad_weights], "bias": grad_bias * scale}


def virtual_update(params: Mapping[str, object], incoming_batch: Sequence[Example], learning_rate: float) -> dict:
    gradient = batch_gradient(params, incoming_batch)
    weights = [float(value) for value in params["weights"]]
    return {
        "weights": [weight - learning_rate * grad for weight, grad in zip(weights, gradient["weights"])],
        "bias": float(params.get("bias", 0.0)) - learning_rate * float(gradient["bias"]),
    }


def score_candidates(params: Mapping[str, object], incoming_batch: Sequence[Example], candidates: Sequence[Example], learning_rate: float, variant: str = "smi_1") -> dict:
    if variant not in {"smi_1", "smi_2"}:
        raise ValueError("variant must be smi_1 or smi_2")
    virtual_params = virtual_update(params, incoming_batch, learning_rate)
    scores = []
    for candidate in candidates:
        current_loss = logistic_loss(params, candidate)
        virtual_loss = logistic_loss(virtual_params, candidate)
        baseline_loss = current_loss
        if variant == "smi_2":
            baseline_loss = min(current_loss, float(candidate.get("best_loss", current_loss)))
        scores.append({
            "example_id": str(candidate.get("example_id", "")),
            "current_loss": current_loss,
            "virtual_loss": virtual_loss,
            "score": virtual_loss - baseline_loss,
            "candidate": dict(candidate),
        })
    scores.sort(key=lambda item: (-float(item["score"]), item["example_id"]))
    return {"virtual_params": virtual_params, "scores": scores}


def select_top_interfered(params: Mapping[str, object], incoming_batch: Sequence[Example], candidates: Sequence[Example], learning_rate: float, budget: int, variant: str = "smi_1") -> dict:
    scored = score_candidates(params, incoming_batch, candidates, learning_rate, variant)
    selected = scored["scores"][: max(0, int(budget))]
    scored["selected"] = selected
    return scored
