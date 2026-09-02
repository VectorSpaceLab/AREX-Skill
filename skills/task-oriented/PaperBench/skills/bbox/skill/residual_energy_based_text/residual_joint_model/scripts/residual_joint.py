#!/usr/bin/env python3
"""Residual EBM candidate scoring utilities."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable


def logsumexp(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        raise ValueError("logsumexp requires at least one value")
    peak = max(values)
    if math.isinf(peak):
        return peak
    return peak + math.log(sum(math.exp(value - peak) for value in values))


def score_candidates(candidates: list[dict]) -> dict:
    if not candidates:
        raise ValueError("at least one candidate is required")
    energy_logits = []
    scored = []
    for item in candidates:
        if "energy" not in item:
            raise ValueError(f"candidate {item.get('id', '<unknown>')} lacks energy")
        energy = float(item["energy"])
        neg_energy = -energy
        energy_logits.append(neg_energy)
        lm_logprob = item.get("lm_logprob")
        joint_logscore = None if lm_logprob is None else float(lm_logprob) - energy
        scored.append(
            {
                **item,
                "energy": energy,
                "neg_energy": neg_energy,
                "joint_logscore": joint_logscore,
            }
        )
    normalizer = logsumexp(energy_logits)
    for item in scored:
        item["importance_weight"] = math.exp(item["neg_energy"] - normalizer)
    if all(item.get("joint_logscore") is not None for item in scored):
        selected = max(scored, key=lambda item: (item["joint_logscore"], item.get("id", "")))
        mode = "joint"
    else:
        selected = max(scored, key=lambda item: (item["importance_weight"], item.get("id", "")))
        mode = "energy"
    return {
        "mode": mode,
        "log_partition_sample_estimate": normalizer - math.log(len(scored)),
        "selected_id": selected.get("id"),
        "candidates": scored,
    }


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON file with a candidates list.")
    parser.add_argument("--output", help="Optional output JSON path.")
    parser.add_argument("--demo", action="store_true", help="Run a deterministic demo.")
    args = parser.parse_args()

    if args.demo:
        payload = {
            "candidates": [
                {"id": "positive", "text": "clear continuation", "lm_logprob": -2.0, "energy": -1.5},
                {"id": "negative", "text": "repetitive repetitive", "lm_logprob": -1.0, "energy": 1.2},
            ]
        }
    elif args.input:
        payload = read_json(args.input)
    else:
        raise SystemExit("--input or --demo is required")

    result = score_candidates(payload["candidates"])
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

