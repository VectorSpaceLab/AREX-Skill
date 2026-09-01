import copy, json, math
from pathlib import Path


def _load_loss():
    import sys
    skill_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(skill_root / "dual_contrastive_loss" / "scripts"))
    from dual_contrastive_loss import dcl_loss
    return dcl_loss


def flatten_targets(batch):
    return [float(v) for pair in batch["pairs"] for v in pair["target_features"]]


def apply_params(batch, params):
    out = copy.deepcopy(batch)
    idx = 0
    for pair in out["pairs"]:
        n = len(pair["target_features"])
        pair["target_features"] = [float(v) for v in params[idx:idx+n]]
        idx += n
    return out


def one_step(batch, learning_rate=0.15, epsilon=1e-4):
    dcl_loss = _load_loss()
    params_before = flatten_targets(batch)
    def loss_for(params):
        return dcl_loss(apply_params(batch, params))["loss"]
    loss_before = loss_for(params_before)
    grads = []
    for i in range(len(params_before)):
        plus = list(params_before); minus = list(params_before)
        plus[i] += epsilon; minus[i] -= epsilon
        grads.append((loss_for(plus) - loss_for(minus))/(2*epsilon))
    params_after = [p - learning_rate*g for p, g in zip(params_before, grads)]
    loss_after = loss_for(params_after)
    return {"loss_before": loss_before, "loss_after": loss_after, "params_before": params_before, "params_after": params_after, "gradients": grads, "optimizer_state_changed": params_before != params_after, "updated_batch": apply_params(batch, params_after)}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("batch_json")
    parser.add_argument("trace_json")
    args = parser.parse_args()
    batch = json.load(open(args.batch_json, encoding="utf-8"))
    json.dump(one_step(batch), open(args.trace_json, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
