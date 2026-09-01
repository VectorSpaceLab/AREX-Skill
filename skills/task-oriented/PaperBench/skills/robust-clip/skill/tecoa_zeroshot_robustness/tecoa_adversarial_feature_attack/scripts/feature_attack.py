#!/usr/bin/env python3
"""Feature-level projected attack for TeCoA reduced recovery."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OBJECTIVE = SCRIPT_DIR.parent.parent / "tecoa_text_contrastive_objective" / "scripts"
if DEFAULT_OBJECTIVE.exists():
    sys.path.insert(0, str(DEFAULT_OBJECTIVE))

from contrastive_objective import compute_tecoa_metrics


def _project_linf(delta, epsilon: float):
    return [[max(-epsilon, min(epsilon, value)) for value in row] for row in delta]


def _add(left, right):
    return [[a + b for a, b in zip(row_a, row_b)] for row_a, row_b in zip(left, right)]


def _loss(images, texts, labels, temperature):
    return compute_tecoa_metrics(images, texts, labels, temperature)["loss"]


def generate_feature_attack(image_embeddings, text_embeddings, labels, epsilon=0.2, step_size=0.1, steps=3, temperature=0.07, fd_eps=1e-4):
    if epsilon < 0:
        raise ValueError("epsilon must be non-negative")
    if step_size <= 0:
        raise ValueError("step_size must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")
    clean = copy.deepcopy([[float(value) for value in row] for row in image_embeddings])
    delta = [[0.0 for _ in row] for row in clean]
    loss_trace = []
    for _ in range(int(steps)):
        current = _add(clean, delta)
        grad_sign = [[0.0 for _ in row] for row in clean]
        for row_idx, row in enumerate(current):
            for col_idx, _ in enumerate(row):
                plus = copy.deepcopy(current)
                minus = copy.deepcopy(current)
                plus[row_idx][col_idx] += fd_eps
                minus[row_idx][col_idx] -= fd_eps
                diff = _loss(plus, text_embeddings, labels, temperature) - _loss(minus, text_embeddings, labels, temperature)
                grad_sign[row_idx][col_idx] = 1.0 if diff >= 0 else -1.0
        delta = [[value + step_size * sign for value, sign in zip(row_delta, row_sign)] for row_delta, row_sign in zip(delta, grad_sign)]
        delta = _project_linf(delta, epsilon)
        loss_trace.append(_loss(_add(clean, delta), text_embeddings, labels, temperature))
    adversarial = _add(clean, delta)
    max_abs_delta = max(abs(value) for row in delta for value in row) if delta else 0.0
    return {
        "adversarial_embeddings": adversarial,
        "delta": delta,
        "loss_trace": loss_trace,
        "bound_checks": {
            "norm": "linf",
            "epsilon": epsilon,
            "max_abs_delta": max_abs_delta,
            "passed": max_abs_delta <= epsilon + 1e-9,
            "clean_input_preserved": clean == [[float(value) for value in row] for row in image_embeddings],
        },
        "proxy_level": "feature",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = generate_feature_attack(
        payload["image_embeddings"],
        payload["text_embeddings"],
        payload["labels"],
        payload.get("epsilon", 0.2),
        payload.get("step_size", 0.1),
        payload.get("steps", 3),
        payload.get("temperature", 0.07),
    )
    text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
