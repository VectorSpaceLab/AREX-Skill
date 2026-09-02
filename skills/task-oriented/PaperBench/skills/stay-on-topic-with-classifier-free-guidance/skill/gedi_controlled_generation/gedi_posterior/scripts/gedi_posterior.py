#!/usr/bin/env python3
"""Stable GeDi posterior utilities."""
import argparse, json, math
from typing import Dict, Iterable, List, Mapping, Sequence


def _sum_log_probs(value):
    if isinstance(value, (int, float)):
        return float(value)
    return float(sum(value))


def log_softmax(logits: Sequence[float]) -> List[float]:
    m = max(logits)
    total = sum(math.exp(x - m) for x in logits)
    return [x - m - math.log(total) for x in logits]


def gedi_posteriors(class_log_probs: Mapping[str, object], length: int, biases=None, alpha: float = 1.0) -> Dict[str, object]:
    if length <= 0:
        raise ValueError("length must be positive")
    biases = biases or {}
    labels = list(class_log_probs.keys())
    logits = []
    for label in labels:
        ll = _sum_log_probs(class_log_probs[label])
        logits.append(float(biases.get(label, 0.0)) + float(alpha) * ll / float(length))
    log_posts = log_softmax(logits)
    return {
        "labels": labels,
        "logits": dict(zip(labels, logits)),
        "log_posteriors": dict(zip(labels, log_posts)),
        "posteriors": dict(zip(labels, [math.exp(x) for x in log_posts])),
    }


def binary_desired_posterior(desired_log_prob, undesired_log_prob, length: int, desired_bias=0.0, undesired_bias=0.0, alpha: float = 1.0) -> float:
    out = gedi_posteriors({"desired": desired_log_prob, "undesired": undesired_log_prob}, length, {"desired": desired_bias, "undesired": undesired_bias}, alpha)
    return out["posteriors"]["desired"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="JSON with class_log_probs, length, optional biases and alpha")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    data = json.load(open(args.input))
    out = gedi_posteriors(data["class_log_probs"], int(data["length"]), data.get("biases"), float(data.get("alpha", 1.0)))
    json.dump(out, open(args.output, "w"), indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
