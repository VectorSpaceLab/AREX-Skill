#!/usr/bin/env python3
"""Compose F-NPSE or PF-NPSE scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def add_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        raise ValueError("at least one score vector is required")
    dim = len(vectors[0])
    if any(len(vector) != dim for vector in vectors):
        raise ValueError("all score vectors must have the same dimension")
    return [sum(vector[i] for vector in vectors) for i in range(dim)]


def compose_score(theta: list[float], condition_scores: list[list[float]], progress: float, condition_count: int | None = None, prior_score: list[float] | None = None, mode: str = "f_npse") -> dict:
    if prior_score is None:
        prior_score = [-value for value in theta]
    if condition_count is None:
        condition_count = len(condition_scores)
    if not 0.0 <= progress <= 1.0:
        raise ValueError("progress must be in [0, 1]")
    score_sum = add_vectors(condition_scores)
    if len(prior_score) != len(score_sum):
        raise ValueError("prior score dimension must match condition score dimension")
    correction_scale = (1 - condition_count) * progress
    prior_correction = [correction_scale * value for value in prior_score]
    composed = [score_sum[i] + prior_correction[i] for i in range(len(score_sum))]
    return {
        "composed_score": composed,
        "score_sum": score_sum,
        "prior_correction": prior_correction,
        "condition_count": condition_count,
        "progress": progress,
        "mode": mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theta", required=True, help="JSON vector")
    parser.add_argument("--condition-scores", required=True, help="JSON list of score vectors")
    parser.add_argument("--progress", type=float, required=True)
    parser.add_argument("--condition-count", type=int, default=0)
    parser.add_argument("--mode", default="f_npse")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compose_score(json.loads(args.theta), json.loads(args.condition_scores), args.progress, args.condition_count or None, mode=args.mode)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": args.output}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
