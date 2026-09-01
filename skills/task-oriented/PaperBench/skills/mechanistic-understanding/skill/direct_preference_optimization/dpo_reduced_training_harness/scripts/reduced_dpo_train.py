#!/usr/bin/env python3
"""Reduced scalar DPO training harness."""
from __future__ import annotations
import argparse, json, math

def logsigmoid(x):
    return -math.log1p(math.exp(-x)) if x >= 0 else x - math.log1p(math.exp(x))

def loss_for_margin(margin, beta):
    return -logsigmoid(beta * margin)

def run_reduced_training(examples, beta=0.5, lr=0.8, steps=20):
    n = len(examples)
    if n == 0: raise ValueError("at least one example is required")
    pc = [float(e.get("policy_chosen", -1.2)) for e in examples]
    pr = [float(e.get("policy_rejected", -1.0)) for e in examples]
    rc = [float(e.get("reference_chosen", -1.0)) for e in examples]
    rr = [float(e.get("reference_rejected", -1.0)) for e in examples]
    before = {"policy_chosen": pc[:], "policy_rejected": pr[:]}
    def stats():
        margins = [(pc[i]-pr[i]) - (rc[i]-rr[i]) for i in range(n)]
        losses = [loss_for_margin(m, beta) for m in margins]
        acc = sum(1 for i in range(n) if pc[i] > pr[i]) / n
        return sum(losses)/n, margins, acc
    loss_before, margins_before, acc_before = stats()
    history = []
    for step in range(steps):
        for i in range(n):
            margin = (pc[i]-pr[i]) - (rc[i]-rr[i])
            # d/dmargin -log sigmoid(beta*m) = -beta * sigmoid(-beta*m)
            grad_m = -beta / (1.0 + math.exp(beta * margin))
            pc[i] -= lr * grad_m / n
            pr[i] += lr * grad_m / n
        if step in {0, steps-1}:
            l, m, a = stats(); history.append({"step": step+1, "loss": l, "accuracy": a, "margins": m})
    loss_after, margins_after, acc_after = stats()
    after = {"policy_chosen": pc[:], "policy_rejected": pr[:]}
    return {"loss_before": loss_before, "loss_after": loss_after,
            "preference_accuracy_before": acc_before, "preference_accuracy_after_update": acc_after,
            "margins_before": margins_before, "margins_after": margins_after,
            "params_before": before, "params_after": after,
            "parameters_before": before, "parameters_after": after,
            "optimizer_state_changed": before != after, "history": history,
            "mechanism_checks": {"preference_data_constructed": True, "dpo_loss_computed": True,
                "reference_logratios_fixed": True, "optimizer_step_executed": before != after,
                "reduced_training_executed": True, "training_step_executed": False,
                "qwen3_model_loaded": False}}

def _self_test():
    examples = [{"prompt":"p","chosen":"a","rejected":"b"} for _ in range(3)]
    out = run_reduced_training(examples)
    assert out["loss_after"] < out["loss_before"]
    assert out["params_before"] != out["params_after"]
    assert out["preference_accuracy_after_update"] == 1.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input", nargs="?"); ap.add_argument("--output", default=""); ap.add_argument("--beta", type=float, default=0.5); ap.add_argument("--lr", type=float, default=0.8); ap.add_argument("--steps", type=int, default=20); ap.add_argument("--self-test", action="store_true")
    args=ap.parse_args()
    if args.self_test:
        _self_test(); print(json.dumps({"ok": True})); return
    data=json.load(open(args.input, encoding="utf-8")); examples=data.get("examples", data if isinstance(data, list) else [])
    out=run_reduced_training(examples, beta=args.beta, lr=args.lr, steps=args.steps)
    text=json.dumps(out, indent=2)
    if args.output: open(args.output,"w",encoding="utf-8").write(text+"\n")
    else: print(text)
if __name__ == "__main__": main()
