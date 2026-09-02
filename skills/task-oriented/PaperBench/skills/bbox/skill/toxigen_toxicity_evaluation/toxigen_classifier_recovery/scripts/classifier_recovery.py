#!/usr/bin/env python3
"""Tiny logistic classifier update for ToxiGen recovery experiments."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


TOXIC_CUES = {
    "inferior",
    "lazy",
    "criminal",
    "dangerous",
    "stereotype",
    "uncivilized",
    "threat",
    "hate",
    "toxic",
    "coded",
}

BENIGN_CUES = {
    "deserve",
    "community",
    "culture",
    "fair",
    "respect",
    "contribute",
    "families",
    "artists",
    "support",
}

IDENTITY_CUES = {
    "black",
    "asian",
    "muslim",
    "jewish",
    "women",
    "woman",
    "lgbtq",
    "latino",
    "mexican",
    "chinese",
    "disabled",
    "native",
}


def normalize_label(label: str) -> int:
    value = str(label).lower().replace("-", "_")
    if value in {"toxic", "hate", "hateful", "1"}:
        return 1
    if value in {"benign", "neutral", "non_toxic", "nontoxic", "0"}:
        return 0
    raise ValueError(f"unsupported label: {label!r}")


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_'-]*", text.lower())


def features(text: str) -> list[float]:
    tokens = tokenize(text)
    length = max(len(tokens), 1)
    toxic = sum(1 for token in tokens if token in TOXIC_CUES)
    benign = sum(1 for token in tokens if token in BENIGN_CUES)
    identity = sum(1 for token in tokens if token in IDENTITY_CUES)
    return [toxic / length, benign / length, identity / length, min(length / 30.0, 1.0)]


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def predict_proba(x: list[float], weights: list[float], bias: float) -> float:
    return sigmoid(sum(w * v for w, v in zip(weights, x)) + bias)


def binary_cross_entropy(probs: list[float], labels: list[int]) -> float:
    eps = 1e-12
    total = 0.0
    for prob, label in zip(probs, labels):
        p = min(max(prob, eps), 1.0 - eps)
        total += -(label * math.log(p) + (1 - label) * math.log(1.0 - p))
    return total / len(labels)


def pairwise_auc(probs: list[float], labels: list[int]):
    positives = [p for p, y in zip(probs, labels) if y == 1]
    negatives = [p for p, y in zip(probs, labels) if y == 0]
    if not positives or not negatives:
        return None
    wins = 0.0
    total = 0
    for pos in positives:
        for neg in negatives:
            total += 1
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    return wins / total


def train_once(examples: list[dict], learning_rate: float = 1.0, steps: int = 1) -> dict:
    xs = [features(item["text"]) for item in examples]
    ys = [normalize_label(item["label"]) for item in examples]
    weights = [0.0 for _ in xs[0]]
    bias = 0.0
    params_before = {"weights": list(weights), "bias": bias}
    probs_before = [predict_proba(x, weights, bias) for x in xs]
    loss_before = binary_cross_entropy(probs_before, ys)
    auc_before = pairwise_auc(probs_before, ys)
    for _ in range(steps):
        grad_w = [0.0 for _ in weights]
        grad_b = 0.0
        for x, y in zip(xs, ys):
            error = predict_proba(x, weights, bias) - y
            for idx, value in enumerate(x):
                grad_w[idx] += error * value
            grad_b += error
        scale = 1.0 / len(xs)
        weights = [w - learning_rate * scale * g for w, g in zip(weights, grad_w)]
        bias = bias - learning_rate * scale * grad_b
    probs_after = [predict_proba(x, weights, bias) for x in xs]
    loss_after = binary_cross_entropy(probs_after, ys)
    auc_after = pairwise_auc(probs_after, ys)
    params_after = {"weights": list(weights), "bias": bias}
    return {
        "schema_version": 1,
        "sample_count": len(examples),
        "loss_before": loss_before,
        "loss_after": loss_after,
        "auc_before": auc_before,
        "auc_after": auc_after,
        "params_before": params_before,
        "params_after": params_after,
        "parameters_before": params_before,
        "parameters_after": params_after,
        "optimizer_state_changed": params_before != params_after,
        "learning_rate": learning_rate,
        "steps": steps,
        "examples": [
            {
                "text": item["text"],
                "label": normalize_label(item["label"]),
                "features": x,
                "prob_before": before,
                "prob_after": after,
            }
            for item, x, before, after in zip(examples, xs, probs_before, probs_after)
        ],
    }


def run_self_test() -> None:
    examples = [
        {"text": "Black families deserve fair respect.", "label": "benign"},
        {"text": "Asian community culture deserves support.", "label": "benign"},
        {"text": "A coded toxic stereotype calls Muslim people dangerous.", "label": "toxic"},
        {"text": "A hateful stereotype says women are inferior.", "label": "toxic"},
    ]
    result = train_once(examples, learning_rate=2.0, steps=5)
    assert result["optimizer_state_changed"] is True
    assert result["loss_after"] <= result["loss_before"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--learning-rate", type=float, default=1.0)
    parser.add_argument("--steps", type=int, default=1)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        print(json.dumps({"ok": True, "test": "classifier_recovery"}))
        return 0
    if not args.input_json or not args.output_json:
        parser.error("--input-json and --output-json are required unless --self-test is used")
    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    examples = payload["examples"] if isinstance(payload, dict) else payload
    result = train_once(examples, learning_rate=args.learning_rate, steps=args.steps)
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"loss_before": result["loss_before"], "loss_after": result["loss_after"], "auc_after": result["auc_after"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
