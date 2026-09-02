#!/usr/bin/env python3
"""Train a tiny deterministic verifier for GSM8K candidate solutions."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def candidate_features(candidate: dict) -> list[float]:
    solution = candidate.get("solution", "")
    checks = candidate.get("calculator_checks", [])
    valid_checks = sum(1 for item in checks if item.get("ok") is True)
    invalid_checks = sum(1 for item in checks if item.get("ok") is False)
    has_final = 1.0 if "####" in solution else 0.0
    numeric_mentions = len(re.findall(r"[-+]?[0-9]+(?:\.[0-9]+)?", solution))
    is_gold_source = 1.0 if candidate.get("source") == "gold_solution" else 0.0
    length_bucket = min(len(solution) / 400.0, 2.0)
    return [1.0, has_final, float(valid_checks), -float(invalid_checks), min(numeric_mentions / 10.0, 2.0), is_gold_source, length_bucket]


def predict(params: list[float], features: list[float]) -> float:
    return sigmoid(sum(weight * value for weight, value in zip(params, features)))


def loss(params: list[float], candidates: list[dict]) -> float:
    total = 0.0
    for candidate in candidates:
        y = float(candidate["label"])
        p = min(max(predict(params, candidate_features(candidate)), 1e-9), 1.0 - 1e-9)
        total += -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))
    return total / max(len(candidates), 1)


def gradient(params: list[float], candidates: list[dict]) -> list[float]:
    grad = [0.0 for _ in params]
    for candidate in candidates:
        features = candidate_features(candidate)
        error = predict(params, features) - float(candidate["label"])
        for idx, value in enumerate(features):
            grad[idx] += error * value
    count = max(len(candidates), 1)
    return [value / count for value in grad]


def train_verifier(candidates: list[dict], learning_rate: float = 0.8, steps: int = 8) -> dict:
    labels = {candidate.get("label") for candidate in candidates}
    if labels != {0, 1}:
        raise ValueError("verifier training requires both positive and negative labels")
    params = [0.0] * len(candidate_features(candidates[0]))
    params_before = list(params)
    loss_before = loss(params, candidates)
    trace_steps = []
    for step in range(steps):
        grad = gradient(params, candidates)
        params = [weight - learning_rate * delta for weight, delta in zip(params, grad)]
        trace_steps.append({"step": step + 1, "loss": loss(params, candidates), "grad": grad})
    loss_after = loss(params, candidates)
    scored = []
    for candidate in candidates:
        enriched = dict(candidate)
        enriched["verifier_score"] = predict(params, candidate_features(candidate))
        scored.append(enriched)
    return {
        "params_before": params_before,
        "params_after": params,
        "parameters_before": params_before,
        "parameters_after": params,
        "loss_before": loss_before,
        "loss_after": loss_after,
        "optimizer_state_changed": params_before != params,
        "steps": trace_steps,
        "scored_candidates": scored,
    }


def train_file(candidates_path: str, trace_path: str, scored_path: str, learning_rate: float, steps: int) -> dict:
    candidates = json.loads(Path(candidates_path).read_text(encoding="utf-8"))
    result = train_verifier(candidates, learning_rate=learning_rate, steps=steps)
    trace = {key: value for key, value in result.items() if key != "scored_candidates"}
    Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
    Path(trace_path).write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    Path(scored_path).write_text(json.dumps(result["scored_candidates"], indent=2) + "\n", encoding="utf-8")
    return trace


def self_test() -> None:
    candidates = [
        {"solution": "Good <<1+1=2>>\n#### 2", "label": 1, "source": "gold_solution", "calculator_checks": [{"ok": True}]},
        {"solution": "Bad <<1+1=3>>\n#### 3", "label": 0, "source": "perturbed_final_answer_1", "calculator_checks": [{"ok": False}]},
    ]
    result = train_verifier(candidates, steps=4)
    assert result["params_before"] != result["params_after"]
    assert result["loss_after"] < result["loss_before"]
    assert len(result["scored_candidates"]) == 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_train = sub.add_parser("train")
    p_train.add_argument("--candidates", required=True)
    p_train.add_argument("--trace", required=True)
    p_train.add_argument("--scored", required=True)
    p_train.add_argument("--learning-rate", type=float, default=0.8)
    p_train.add_argument("--steps", type=int, default=8)
    sub.add_parser("self-test")
    args = parser.parse_args(argv)
    if args.cmd == "train":
        result = train_file(args.candidates, args.trace, args.scored, args.learning_rate, args.steps)
        print(json.dumps(result, indent=2))
    elif args.cmd == "self-test":
        self_test()
        print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
