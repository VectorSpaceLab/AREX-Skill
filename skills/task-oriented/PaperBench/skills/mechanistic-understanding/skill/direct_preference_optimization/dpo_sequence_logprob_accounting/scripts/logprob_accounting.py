#!/usr/bin/env python3
"""Response-only sequence log-probability accounting for DPO."""
from __future__ import annotations
import argparse, json, math

def log_softmax(row):
    m = max(row); z = sum(math.exp(x - m) for x in row)
    return [x - m - math.log(z) for x in row]

def sequence_logprob(log_probs, labels, average=False, already_shifted=True):
    if len(log_probs) != len(labels):
        raise ValueError("log_probs and labels must have the same sequence length")
    total = 0.0; count = 0; selected = []
    for pos, (dist, label) in enumerate(zip(log_probs, labels)):
        if label == -100:
            continue
        if not isinstance(label, int) or label < 0 or label >= len(dist):
            raise ValueError(f"invalid label at position {pos}: {label}")
        val = float(dist[label])
        total += val; count += 1; selected.append(val)
    if count == 0:
        raise ValueError("example has zero unmasked response tokens")
    return {"logprob": total / count if average else total, "token_count": count, "selected_logps": selected}

def batch_sequence_logprob(batch_log_probs, batch_labels, average=False):
    if len(batch_log_probs) != len(batch_labels):
        raise ValueError("batch sizes differ")
    return [sequence_logprob(lp, lab, average=average)["logprob"] for lp, lab in zip(batch_log_probs, batch_labels)]

def _self_test():
    lps = [[math.log(0.8), math.log(0.2)], [math.log(0.1), math.log(0.9)], [math.log(0.3), math.log(0.7)]]
    res = sequence_logprob(lps, [-100, 1, 0])
    assert abs(res["logprob"] - (math.log(0.9)+math.log(0.3))) < 1e-9
    try:
        sequence_logprob(lps, [-100,-100,-100]); raise AssertionError("expected failure")
    except ValueError: pass

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input", nargs="?"); ap.add_argument("--average", action="store_true"); ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test(); print(json.dumps({"ok": True})); return
    data = json.load(open(args.input, encoding="utf-8"))
    print(json.dumps(sequence_logprob(data["log_probs"], data["labels"], average=args.average), indent=2))
if __name__ == "__main__": main()
