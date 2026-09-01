#!/usr/bin/env python3
"""Tiny soft-label reward-model trainer for RLAIF recovery checks."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def tokenize(text: str) -> list[str]:
    return [token.strip(".,!?;:()[]{}'\"").lower() for token in text.split() if token.strip()]


def features(context: str, response: str) -> list[float]:
    response_tokens = tokenize(response)
    context_tokens = {token for token in tokenize(context) if len(token) > 3}
    overlap = sum(1 for token in response_tokens if token in context_tokens) / max(1, len(response_tokens))
    length = min(len(response_tokens), 80) / 80.0
    specificity = len(set(response_tokens)) / max(1, len(response_tokens))
    return [1.0, overlap, length, specificity]


def dot(params: list[float], feats: list[float]) -> float:
    return sum(p * f for p, f in zip(params, feats))


def softmax2(a: float, b: float) -> list[float]:
    m = max(a, b)
    ea = math.exp(a - m)
    eb = math.exp(b - m)
    denom = ea + eb
    return [ea / denom, eb / denom]


def cross_entropy(target: list[float], pred: list[float]) -> float:
    eps = 1e-12
    return -sum(t * math.log(max(eps, p)) for t, p in zip(target, pred))


def train_pairwise(examples: list[dict], *, steps: int = 40, lr: float = 0.8, params: list[float] | None = None) -> dict:
    if params is None:
        params = [0.0, 0.0, 0.0, 0.0]
    params_before = list(params)

    def loss_and_grad(current: list[float]) -> tuple[float, list[float]]:
        total_loss = 0.0
        grad = [0.0 for _ in current]
        for item in examples:
            x1 = features(item["context"], item["response1"])
            x2 = features(item["context"], item["response2"])
            target = [float(item["preference"][0]), float(item["preference"][1])]
            score1 = dot(current, x1)
            score2 = dot(current, x2)
            pred = softmax2(score1, score2)
            total_loss += cross_entropy(target, pred)
            delta1 = pred[0] - target[0]
            delta2 = pred[1] - target[1]
            for idx in range(len(current)):
                grad[idx] += delta1 * x1[idx] + delta2 * x2[idx]
        scale = 1.0 / max(1, len(examples))
        return total_loss * scale, [g * scale for g in grad]

    loss_before, _ = loss_and_grad(params)
    for _ in range(int(steps)):
        _, grad = loss_and_grad(params)
        params = [p - lr * g for p, g in zip(params, grad)]
    loss_after, _ = loss_and_grad(params)
    predictions = []
    for item in examples:
        score1 = dot(params, features(item["context"], item["response1"]))
        score2 = dot(params, features(item["context"], item["response2"]))
        predictions.append(
            {
                "scores": [score1, score2],
                "probabilities": softmax2(score1, score2),
                "predicted_label": 1 if score1 >= score2 else 2,
            }
        )
    return {
        "params_before": params_before,
        "params_after": params,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "optimizer_state_changed": params_before != params,
        "predictions": predictions,
    }


def smoke_examples() -> list[dict]:
    return [
        {
            "context": "A student bought a used computer and monitor with mostly their own money, and their mother wants it returned.",
            "response1": "I bought a computer and my mom is angry.",
            "response2": "I bought a used computer and monitor mostly with my own money, and my mother wants me to return it.",
            "preference": [0.2, 0.8],
        }
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--lr", type=float, default=0.8)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    examples = smoke_examples() if args.smoke or not args.input else json.loads(Path(args.input).read_text(encoding="utf-8"))["examples"]
    result = train_pairwise(examples, steps=args.steps, lr=args.lr)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
