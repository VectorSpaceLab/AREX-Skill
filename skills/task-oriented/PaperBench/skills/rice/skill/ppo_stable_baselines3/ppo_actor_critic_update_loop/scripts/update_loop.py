from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

try:
    from advantage import compute_gae
    from surrogate import clipped_surrogate
except Exception:  # imports are supplied by PYTHONPATH in tests/recovery
    compute_gae = None
    clipped_surrogate = None


def _loss(params: dict, batch: dict, clip_epsilon: float, value_coef: float, entropy_coef: float) -> dict:
    old_log_probs = batch["old_log_probs"]
    features = batch["features"]
    advantages = batch["advantages"]
    returns = batch["returns"]
    new_log_probs = [old + params["policy_weight"] * feature for old, feature in zip(old_log_probs, features)]
    surrogate = clipped_surrogate(new_log_probs, old_log_probs, advantages, clip_epsilon)
    values = [params["value_bias"] for _ in returns]
    value_loss = sum((value - target) ** 2 for value, target in zip(values, returns)) / len(returns)
    entropy_proxy = -sum(log_prob * log_prob for log_prob in new_log_probs) / len(new_log_probs)
    total = surrogate["loss"] + value_coef * value_loss - entropy_coef * entropy_proxy
    return {
        "total_loss": total,
        "policy_loss": surrogate["loss"],
        "value_loss": value_loss,
        "entropy_proxy": entropy_proxy,
        "surrogate": surrogate,
    }


def _finite_difference(params: dict, loss_fn: Callable[[dict], float], epsilon: float = 1e-5) -> dict:
    gradients = {}
    for name in params:
        plus = dict(params)
        minus = dict(params)
        plus[name] += epsilon
        minus[name] -= epsilon
        gradients[name] = (loss_fn(plus) - loss_fn(minus)) / (2.0 * epsilon)
    return gradients


def run_reduced_update(config: dict) -> dict:
    if compute_gae is None or clipped_surrogate is None:
        raise RuntimeError("advantage and surrogate helpers must be importable")
    gae = compute_gae(config["steps"], config.get("last_value", 0.0), config.get("gamma", 0.99), config.get("gae_lambda", 0.95))
    batch = {
        "old_log_probs": [float(x) for x in config["old_log_probs"]],
        "features": [float(x) for x in config["features"]],
        "advantages": gae["advantages"],
        "returns": gae["returns"],
    }
    params_before = {
        "policy_weight": float(config.get("policy_weight", 0.0)),
        "value_bias": float(config.get("value_bias", 0.0)),
    }
    clip_epsilon = float(config.get("clip_epsilon", 0.2))
    value_coef = float(config.get("value_coef", 0.5))
    entropy_coef = float(config.get("entropy_coef", 0.0))
    learning_rate = float(config.get("learning_rate", 0.05))
    before = _loss(params_before, batch, clip_epsilon, value_coef, entropy_coef)
    gradients = _finite_difference(params_before, lambda p: _loss(p, batch, clip_epsilon, value_coef, entropy_coef)["total_loss"])
    params_after = {name: value - learning_rate * gradients[name] for name, value in params_before.items()}
    after = _loss(params_after, batch, clip_epsilon, value_coef, entropy_coef)
    return {
        "loss_before": before["total_loss"],
        "loss_after": after["total_loss"],
        "params_before": params_before,
        "params_after": params_after,
        "gradients": gradients,
        "optimizer_state_changed": params_before != params_after,
        "advantage_result": gae,
        "surrogate_before": before["surrogate"],
        "surrogate_after": after["surrogate"],
        "mechanism_checks": {
            "gae_executed": True,
            "clipped_surrogate_executed": True,
            "value_loss_executed": True,
            "optimizer_step_executed": params_before != params_after,
            "parameters_changed": params_before != params_after,
        },
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = run_reduced_update(config)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
