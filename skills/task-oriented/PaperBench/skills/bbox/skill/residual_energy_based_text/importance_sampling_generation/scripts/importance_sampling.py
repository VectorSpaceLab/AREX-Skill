#!/usr/bin/env python3
"""Importance reweighting helpers for residual EBM proposal samples."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def logsumexp(values: list[float]) -> float:
    if not values:
        raise ValueError("values must not be empty")
    peak = max(values)
    return peak + math.log(sum(math.exp(value - peak) for value in values))


def importance_weights(candidates: list[dict]) -> dict:
    if not candidates:
        raise ValueError("at least one candidate is required")
    logits = [-float(item["energy"]) for item in candidates]
    log_total = logsumexp(logits)
    weighted = []
    for item, logit in zip(candidates, logits):
        weight = math.exp(logit - log_total)
        joint = None
        if "lm_logprob" in item:
            joint = float(item["lm_logprob"]) - float(item["energy"])
        weighted.append({**item, "importance_weight": weight, "joint_logscore": joint})
    ess = 1.0 / sum(item["importance_weight"] ** 2 for item in weighted)
    selected = max(
        weighted,
        key=lambda item: (
            item["importance_weight"],
            float(item["lm_logprob"]) if "lm_logprob" in item else float("-inf"),
            item.get("id", ""),
        ),
    )
    return {
        "mode": "energy_importance_generation",
        "log_z_estimate": log_total - math.log(len(weighted)),
        "effective_sample_size": ess,
        "selected_id": selected.get("id"),
        "candidates": weighted,
    }


def demo_payload() -> dict:
    return {
        "candidates": [
            {"id": "positive", "text": "specific and coherent continuation", "lm_logprob": -2.4, "energy": -1.8},
            {"id": "repetition", "text": "policy policy policy", "lm_logprob": -1.1, "energy": 2.0},
            {"id": "generic", "text": "it is the and of", "lm_logprob": -1.5, "energy": 1.2},
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Input JSON with candidates.")
    parser.add_argument("--output", help="Optional output JSON path.")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    payload = demo_payload() if args.demo else json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = importance_weights(payload["candidates"])
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
