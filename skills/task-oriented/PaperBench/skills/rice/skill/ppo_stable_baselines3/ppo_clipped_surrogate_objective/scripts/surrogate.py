from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable


def clipped_surrogate(new_log_probs: Iterable[float], old_log_probs: Iterable[float], advantages: Iterable[float], clip_epsilon: float = 0.2) -> dict:
    new_values = [float(x) for x in new_log_probs]
    old_values = [float(x) for x in old_log_probs]
    adv_values = [float(x) for x in advantages]
    if not (len(new_values) == len(old_values) == len(adv_values)):
        raise ValueError("new_log_probs, old_log_probs, and advantages must have equal length")
    if not new_values:
        raise ValueError("at least one sample is required")
    if clip_epsilon < 0:
        raise ValueError("clip_epsilon must be non-negative")
    ratios = []
    unclipped = []
    clipped_terms = []
    selected = []
    clipped_flags = []
    approx_kls = []
    low = 1.0 - clip_epsilon
    high = 1.0 + clip_epsilon
    for new_log_prob, old_log_prob, advantage in zip(new_values, old_values, adv_values):
        delta = max(min(new_log_prob - old_log_prob, 50.0), -50.0)
        ratio = math.exp(delta)
        clipped_ratio = min(max(ratio, low), high)
        raw_term = ratio * advantage
        clipped_term = clipped_ratio * advantage
        selected_term = min(raw_term, clipped_term)
        ratios.append(ratio)
        unclipped.append(raw_term)
        clipped_terms.append(clipped_term)
        selected.append(selected_term)
        clipped_flags.append(float(abs(ratio - clipped_ratio) > 1e-12))
        approx_kls.append((ratio - 1.0) - math.log(ratio))
    objective = sum(selected) / len(selected)
    return {
        "ratios": ratios,
        "unclipped_terms": unclipped,
        "clipped_terms": clipped_terms,
        "selected_terms": selected,
        "objective": objective,
        "loss": -objective,
        "clip_fraction": sum(clipped_flags) / len(clipped_flags),
        "approx_kl": sum(approx_kls) / len(approx_kls),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--clip-epsilon", type=float, default=0.2)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = clipped_surrogate(data["new_log_probs"], data["old_log_probs"], data["advantages"], args.clip_epsilon)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
