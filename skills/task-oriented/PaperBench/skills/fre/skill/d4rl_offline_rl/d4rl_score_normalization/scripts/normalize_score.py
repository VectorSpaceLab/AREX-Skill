#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any


def normalize_score(score: float, random_score: float, expert_score: float) -> dict[str, Any]:
    score = float(score)
    random_score = float(random_score)
    expert_score = float(expert_score)
    denominator = expert_score - random_score
    if denominator == 0:
        raise ValueError("expert_score and random_score must differ")
    normalized = 100.0 * (score - random_score) / denominator
    return {
        "normalized_score": normalized,
        "score": score,
        "random_score": random_score,
        "expert_score": expert_score,
        "diagnostics": {
            "denominator": denominator,
            "below_random": normalized < 0.0,
            "above_expert": normalized > 100.0,
            "in_reference_range": 0.0 <= normalized <= 100.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=float, required=True)
    parser.add_argument("--random-score", type=float, required=True)
    parser.add_argument("--expert-score", type=float, required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = normalize_score(args.score, args.random_score, args.expert_score)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        from pathlib import Path
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
