from __future__ import annotations

import math
from typing import Mapping, Sequence


def normalize(probs: Sequence[float], eps: float = 1e-12) -> list[float]:
    values = [max(float(value), eps) for value in probs]
    total = sum(values)
    if total <= 0.0:
        raise ValueError("probability vector must have positive mass")
    return [value / total for value in values]


def kl_divergence(p: Sequence[float], q: Sequence[float]) -> float:
    p_norm = normalize(p)
    q_norm = normalize(q)
    if len(p_norm) != len(q_norm):
        raise ValueError("probability vectors must have equal length")
    return sum(pi * math.log(pi / qi) for pi, qi in zip(p_norm, q_norm))


def entropy(p: Sequence[float]) -> float:
    p_norm = normalize(p)
    return -sum(pi * math.log(pi) for pi in p_norm)


def distance(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("latent vectors must have equal length")
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def rank_latent_candidates(candidates: Sequence[Mapping[str, object]], entropy_weight: float = 0.0) -> list[dict]:
    ranked = []
    for candidate in candidates:
        pre = candidate["pre_probs"]
        post = candidate["virtual_probs"]
        kl_value = kl_divergence(pre, post)
        entropy_value = entropy(pre)
        ranked.append({
            "candidate_id": str(candidate.get("candidate_id", "")),
            "latent": [float(value) for value in candidate["latent"]],
            "kl": kl_value,
            "entropy": entropy_value,
            "score": kl_value - float(entropy_weight) * entropy_value,
            "candidate": dict(candidate),
        })
    ranked.sort(key=lambda item: (-float(item["score"]), item["candidate_id"]))
    return ranked


def select_diverse_latents(candidates: Sequence[Mapping[str, object]], budget: int, entropy_weight: float = 0.0, min_distance: float = 0.0) -> dict:
    ranked = rank_latent_candidates(candidates, entropy_weight)
    selected = []
    for item in ranked:
        if len(selected) >= max(0, int(budget)):
            break
        if all(distance(item["latent"], other["latent"]) >= float(min_distance) for other in selected):
            selected.append(item)
    return {
        "ranked": ranked,
        "selected": selected,
        "mechanism_checks": {
            "kl_drift_evaluated": bool(candidates),
            "entropy_penalty_evaluated": True,
            "diversity_filter_evaluated": min_distance > 0.0,
        },
    }
