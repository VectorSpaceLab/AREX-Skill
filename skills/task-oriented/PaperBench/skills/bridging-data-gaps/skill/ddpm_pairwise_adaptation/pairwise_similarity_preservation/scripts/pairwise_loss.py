#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import Any


def flatten(sample: Any) -> list[float]:
    if isinstance(sample, list):
        out: list[float] = []
        for item in sample:
            out.extend(flatten(item))
        return out
    return [float(sample)]


def cosine(a: list[float], b: list[float], eps: float = 1e-12) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / max(na * nb, eps)


def softmax(values: list[float], temperature: float = 1.0) -> list[float]:
    scaled = [v / temperature for v in values]
    max_v = max(scaled)
    exp_values = [math.exp(v - max_v) for v in scaled]
    total = sum(exp_values)
    return [v / total for v in exp_values]


def pairwise_distributions(batch: list[Any], temperature: float = 1.0) -> list[dict]:
    if len(batch) < 2:
        raise ValueError("batch size must be at least 2")
    vectors = [flatten(x) for x in batch]
    dim = len(vectors[0])
    if any(len(v) != dim for v in vectors):
        raise ValueError("all samples must flatten to the same dimension")
    rows = []
    for i, vec in enumerate(vectors):
        neighbors = [j for j in range(len(vectors)) if j != i]
        sims = [cosine(vec, vectors[j]) for j in neighbors]
        rows.append({"anchor": i, "neighbors": neighbors, "similarities": sims, "probabilities": softmax(sims, temperature)})
    return rows


def kl_divergence(p_adapted: list[float], p_source: list[float], eps: float = 1e-12) -> float:
    return sum(max(pa, eps) * math.log(max(pa, eps) / max(ps, eps)) for pa, ps in zip(p_adapted, p_source))


def pairwise_kl_loss(source_batch: list[Any], adapted_batch: list[Any], temperature: float = 1.0) -> dict:
    source = pairwise_distributions(source_batch, temperature)
    adapted = pairwise_distributions(adapted_batch, temperature)
    if len(source) != len(adapted):
        raise ValueError("source and adapted batch sizes differ")
    losses = [kl_divergence(a["probabilities"], s["probabilities"]) for s, a in zip(source, adapted)]
    return {"loss": sum(losses) / len(losses), "per_anchor_loss": losses, "source": source, "adapted": adapted}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        batch = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        print(json.dumps(pairwise_kl_loss(batch, batch), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
