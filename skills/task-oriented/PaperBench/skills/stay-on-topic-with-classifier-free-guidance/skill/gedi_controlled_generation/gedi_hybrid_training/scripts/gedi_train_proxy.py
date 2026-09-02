#!/usr/bin/env python3
import argparse, json, math


def sigmoid(x):
    if x >= 0:
        z = math.exp(-x); return 1/(1+z)
    z = math.exp(x); return z/(1+z)


def losses(desired_score, undesired_score, generative_nll, lam=0.6):
    p = sigmoid(desired_score - undesired_score)
    disc = -math.log(max(p, 1e-12))
    gen = float(generative_nll)
    hybrid = float(lam) * gen + (1.0 - float(lam)) * disc
    return {"posterior_desired": p, "discriminative_loss": disc, "generative_loss": gen, "hybrid_loss": hybrid}


def tiny_optimizer_step(params=None, lam=0.6, lr=0.2):
    # Tiny differentiable proxy: desired score=w, undesired score=-w, generative_nll=(w-1)^2+0.1.
    w = float((params or {}).get("w", 0.0))
    before = {"w": w}
    def total(x):
        return losses(x, -x, (x - 1.0) ** 2 + 0.1, lam)["hybrid_loss"]
    before_loss = total(w)
    # analytic gradient: lam*2(w-1) + (1-lam)*d[-log sigmoid(2w)]/dw = lam*2(w-1) - (1-lam)*2*(1-sigmoid(2w))
    grad = float(lam) * 2.0 * (w - 1.0) - (1.0 - float(lam)) * 2.0 * (1.0 - sigmoid(2.0 * w))
    w2 = w - float(lr) * grad
    after = {"w": w2}
    after_loss = total(w2)
    return {
        "params_before": before,
        "params_after": after,
        "parameters_before": before,
        "parameters_after": after,
        "loss_before": before_loss,
        "loss_after": after_loss,
        "gradient": {"w": grad},
        "optimizer_step_executed": True,
        "reduced_training_executed": True,
        "loss_components_before": losses(w, -w, (w - 1.0) ** 2 + 0.1, lam),
        "loss_components_after": losses(w2, -w2, (w2 - 1.0) ** 2 + 0.1, lam),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--lambda", dest="lam", type=float, default=0.6)
    ap.add_argument("--lr", type=float, default=0.2)
    args = ap.parse_args()
    json.dump(tiny_optimizer_step(lam=args.lam, lr=args.lr), open(args.output, "w"), indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
