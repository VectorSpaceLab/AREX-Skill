#!/usr/bin/env python3
import argparse, json, math
from typing import List, Sequence


def _softmax(logits: Sequence[float]) -> List[float]:
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps)
    return [x / s for x in exps]


def guided_distribution(tokens, base_log_probs, posteriors, omega=30.0, rho=0.2, eps=1e-12):
    if not (len(tokens) == len(base_log_probs) == len(posteriors)) or not tokens:
        raise ValueError("tokens, base_log_probs, and posteriors must be nonempty and same length")
    guided_logits = [float(b) + float(omega) * math.log(max(min(float(p), 1.0), eps)) for b, p in zip(base_log_probs, posteriors)]
    probs = _softmax(guided_logits)
    order = sorted(range(len(tokens)), key=lambda i: (-float(posteriors[i]), i))
    keep = [False] * len(tokens)
    cumulative = 0.0
    threshold = min(max(float(rho), 0.0), 1.0)
    for i in order:
        keep[i] = True
        cumulative += probs[i]
        if cumulative >= threshold:
            break
    kept_mass = sum(p for p, k in zip(probs, keep) if k)
    filtered = [p / kept_mass if k else 0.0 for p, k in zip(probs, keep)]
    selected_idx = max(range(len(tokens)), key=lambda i: (filtered[i], -i))
    return {
        "tokens": list(tokens),
        "guided_probabilities": dict(zip(tokens, probs)),
        "keep_mask": dict(zip(tokens, keep)),
        "filtered_probabilities": dict(zip(tokens, filtered)),
        "selected_token": tokens[selected_idx],
        "retained_mass_before_renormalization": kept_mass,
        "omega": float(omega),
        "rho": float(rho),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    data = json.load(open(args.input))
    out = guided_distribution(data["tokens"], data["base_log_probs"], data["posteriors"], data.get("omega", 30.0), data.get("rho", 0.2))
    json.dump(out, open(args.output, "w"), indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
