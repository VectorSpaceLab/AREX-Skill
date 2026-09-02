#!/usr/bin/env python3
"""Standard-library DPO loss formulas."""
from __future__ import annotations
import argparse, json, math

def logsigmoid(x):
    if x >= 0:
        return -math.log1p(math.exp(-x))
    return x - math.log1p(math.exp(x))

def dpo_example(policy_chosen, policy_rejected, reference_chosen, reference_rejected, beta=0.1, label_smoothing=0.0, reference_free=False, ipo=False):
    if beta <= 0:
        raise ValueError("beta must be positive")
    pi_lr = policy_chosen - policy_rejected
    ref_lr = 0.0 if reference_free else reference_chosen - reference_rejected
    logit = pi_lr - ref_lr
    if ipo:
        loss = (logit - 1.0/(2.0*beta)) ** 2
    else:
        loss = -logsigmoid(beta * logit) * (1.0 - label_smoothing) - logsigmoid(-beta * logit) * label_smoothing
    return {"loss": loss, "chosen_reward": beta * (policy_chosen - reference_chosen),
            "rejected_reward": beta * (policy_rejected - reference_rejected),
            "policy_logratio": pi_lr, "reference_logratio": ref_lr, "logit": logit}

def dpo_batch(policy_chosen, policy_rejected, reference_chosen, reference_rejected, beta=0.1, **kw):
    rows = [dpo_example(a,b,c,d,beta=beta,**kw) for a,b,c,d in zip(policy_chosen, policy_rejected, reference_chosen, reference_rejected)]
    return {"examples": rows, "mean_loss": sum(r["loss"] for r in rows)/len(rows)}

def _self_test():
    bad = dpo_example(-2, -1, -1, -1, beta=0.5)["loss"]
    good = dpo_example(-1, -2, -1, -1, beta=0.5)["loss"]
    assert good < bad
    assert dpo_example(-1,-2,-5,-5,beta=1.0,reference_free=True)["reference_logratio"] == 0.0

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input", nargs="?"); ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        _self_test(); print(json.dumps({"ok": True})); return
    data = json.load(open(args.input, encoding="utf-8"))
    print(json.dumps(dpo_batch(**data), indent=2))
if __name__ == "__main__": main()
