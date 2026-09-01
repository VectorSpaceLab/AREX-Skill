#!/usr/bin/env python3
"""Tiny conditional NCE trainer for residual EBM recovery."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


FEATURES = ["quality", "repetition", "length_match", "generic", "coherence"]


def softplus(value: float) -> float:
    if value > 30:
        return value
    if value < -30:
        return math.exp(value)
    return math.log1p(math.exp(value))


def default_features(text: str) -> dict[str, float]:
    lower = text.lower()
    words = [word.strip(".,;:!?\"'()[]") for word in lower.split()]
    unique_ratio = len(set(words)) / max(len(words), 1)
    repetition = 1.0 - unique_ratio
    quality_terms = {"clear", "specific", "policy", "evidence", "human", "context", "development"}
    generic_terms = {"the", "and", "of", "to", "in", "it"}
    quality = sum(1 for word in words if word in quality_terms) / max(len(words), 1)
    generic = sum(1 for word in words if word in generic_terms) / max(len(words), 1)
    coherent_pairs = [
        ("clear", "evidence"),
        ("evidence", "supports"),
        ("supports", "development"),
        ("development", "context"),
        ("sustainable", "development"),
    ]
    word_pairs = set(zip(words, words[1:]))
    coherence = sum(1 for pair in coherent_pairs if pair in word_pairs) / len(coherent_pairs)
    return {
        "quality": quality,
        "repetition": repetition,
        "length_match": 1.0 / (1.0 + abs(len(words) - 12.0)),
        "generic": generic,
        "coherence": coherence,
    }


def energy(params: dict[str, float], features: dict[str, float]) -> float:
    return params.get("bias", 0.0) + sum(params.get(name, 0.0) * features.get(name, 0.0) for name in FEATURES)


def objective(params: dict[str, float], positives: list[dict], negatives: list[dict]) -> float:
    total = 0.0
    count = 0
    for item in positives:
        total += softplus(energy(params, item["features"]))
        count += 1
    for item in negatives:
        total += softplus(-energy(params, item["features"]))
        count += 1
    return total / max(count, 1)


def gradients(params: dict[str, float], positives: list[dict], negatives: list[dict]) -> dict[str, float]:
    grad = {"bias": 0.0, **{name: 0.0 for name in FEATURES}}
    count = len(positives) + len(negatives)
    for sign, rows in [(1.0, positives), (-1.0, negatives)]:
        for item in rows:
            score = energy(params, item["features"])
            # d softplus(sign * score) / d score = sign * sigmoid(sign * score)
            coeff = sign / (1.0 + math.exp(-sign * score))
            grad["bias"] += coeff / count
            for name in FEATURES:
                grad[name] += coeff * item["features"].get(name, 0.0) / count
    return grad


def prepare_rows(rows: list[dict]) -> list[dict]:
    prepared = []
    for row in rows:
        features = row.get("features") or default_features(row.get("text", ""))
        prepared.append({**row, "features": {name: float(features.get(name, 0.0)) for name in FEATURES}})
    return prepared


def train_nce(payload: dict, steps: int = 80, lr: float = 0.8) -> dict:
    positives = prepare_rows(payload["positives"])
    negatives = prepare_rows(payload["negatives"])
    params = {name: float(value) for name, value in payload.get("initial_params", {}).items()}
    params.setdefault("bias", 0.0)
    for name in FEATURES:
        params.setdefault(name, 0.0)
    before = dict(params)
    loss_before = objective(params, positives, negatives)
    for _ in range(steps):
        grad = gradients(params, positives, negatives)
        for name, value in grad.items():
            params[name] -= lr * value
    loss_after = objective(params, positives, negatives)
    pos_energy = sum(energy(params, item["features"]) for item in positives) / len(positives)
    neg_energy = sum(energy(params, item["features"]) for item in negatives) / len(negatives)
    return {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": before,
        "params_after": params,
        "optimizer_state_changed": before != params,
        "positive_energy_after": pos_energy,
        "negative_energy_after": neg_energy,
        "energy_gap_after": neg_energy - pos_energy,
        "positives": positives,
        "negatives": negatives,
    }


def demo_payload() -> dict:
    return {
        "positives": [
            {"id": "positive", "text": "clear policy evidence supports sustainable development in context"}
        ],
        "negatives": [
            {"id": "negative_repetition", "text": "the policy policy policy the the policy"},
            {"id": "negative_generic", "text": "it is the and of to in the and of"},
        ],
        "initial_params": {"bias": 0.0, "quality": 0.0, "repetition": 0.0, "length_match": 0.0, "generic": 0.0, "coherence": 0.0},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON payload with positives and negatives.")
    parser.add_argument("--output", help="Optional output JSON path.")
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.8)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    payload = demo_payload() if args.demo else json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = train_nce(payload, steps=args.steps, lr=args.lr)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
