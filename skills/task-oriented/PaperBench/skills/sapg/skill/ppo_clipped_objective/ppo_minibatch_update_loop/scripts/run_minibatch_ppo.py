#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path


def sigmoid(value):
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def action_log_prob(theta, action):
    prob_one = sigmoid(theta)
    prob = prob_one if int(action) == 1 else 1.0 - prob_one
    return math.log(max(prob, 1e-12))


def expected_reward(theta):
    return sigmoid(theta)


def clipped_terms(old_log_probs, new_log_probs, advantages, clip_epsilon):
    ratios = [math.exp(new - old) for old, new in zip(old_log_probs, new_log_probs)]
    lower = 1.0 - clip_epsilon
    upper = 1.0 + clip_epsilon
    clipped_ratios = [min(max(ratio, lower), upper) for ratio in ratios]
    unclipped = [ratio * adv for ratio, adv in zip(ratios, advantages)]
    clipped = [ratio * adv for ratio, adv in zip(clipped_ratios, advantages)]
    objective_terms = [min(raw, bounded) for raw, bounded in zip(unclipped, clipped)]
    return ratios, clipped_ratios, unclipped, clipped, objective_terms


def normalize(values):
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = math.sqrt(variance)
    if std < 1e-12:
        return [0.0 for _ in values]
    return [(value - mean) / std for value in values]


def run_reduced_ppo(batch=None, theta=0.0, learning_rate=0.12, epochs=6, clip_epsilon=0.2, normalize_advantages=True):
    if batch is None:
        old_theta = 0.0
        actions = [1, 1, 0, 1, 0, 1]
        raw_advantages = [1.4, 1.0, -0.9, 0.8, -0.7, 1.2]
        old_log_probs = [action_log_prob(old_theta, action) for action in actions]
    else:
        actions = [int(action) for action in batch["actions"]]
        raw_advantages = [float(value) for value in batch["advantages"]]
        old_log_probs = [float(value) for value in batch["old_log_probs"]]
    advantages = normalize(raw_advantages) if normalize_advantages else raw_advantages[:]
    theta_before = float(theta)
    old_log_probs_snapshot = old_log_probs[:]

    trace = []
    for epoch in range(int(epochs)):
        new_log_probs = [action_log_prob(theta, action) for action in actions]
        ratios, clipped_ratios, unclipped, clipped, objective_terms = clipped_terms(old_log_probs, new_log_probs, advantages, clip_epsilon)
        mean_objective = sum(objective_terms) / len(objective_terms)
        gradient_terms = []
        for action, advantage, ratio, clipped_ratio, raw, bounded in zip(actions, advantages, ratios, clipped_ratios, unclipped, clipped):
            use_unclipped = raw <= bounded + 1e-12
            if use_unclipped:
                grad_log_prob = (1.0 - sigmoid(theta)) if action == 1 else -sigmoid(theta)
                gradient_terms.append(ratio * advantage * grad_log_prob)
            else:
                gradient_terms.append(0.0)
        gradient = sum(gradient_terms) / len(gradient_terms)
        theta = theta + learning_rate * gradient
        trace.append({
            "epoch": epoch,
            "theta": theta,
            "mean_objective": mean_objective,
            "loss": -mean_objective,
            "gradient": gradient,
            "clip_fraction": sum(1 for ratio in ratios if abs(ratio - 1.0) > clip_epsilon) / len(ratios),
            "approx_kl": sum(old - new for old, new in zip(old_log_probs, new_log_probs)) / len(old_log_probs),
            "ratios": ratios,
        })

    final_log_probs = [action_log_prob(theta, action) for action in actions]
    final_ratios, final_clipped_ratios, final_unclipped, final_clipped, final_terms = clipped_terms(old_log_probs, final_log_probs, advantages, clip_epsilon)
    loss_after = -sum(final_terms) / len(final_terms)
    first_loss = trace[0]["loss"] if trace else None
    return {
        "schema_version": 1,
        "batch": {
            "actions": actions,
            "old_log_probs": old_log_probs,
            "raw_advantages": raw_advantages,
            "advantages": advantages,
            "sample_count": len(actions),
        },
        "params_before": {"theta": theta_before},
        "params_after": {"theta": theta},
        "parameters_before": {"theta": theta_before},
        "parameters_after": {"theta": theta},
        "loss_before": first_loss,
        "loss_after": loss_after,
        "expected_reward_before": expected_reward(theta_before),
        "expected_reward_after": expected_reward(theta),
        "expected_reward_improvement": expected_reward(theta) - expected_reward(theta_before),
        "optimizer_step_executed": abs(theta - theta_before) > 1e-12,
        "old_log_probs_frozen": old_log_probs == old_log_probs_snapshot,
        "minibatch_epochs_executed": int(epochs),
        "clip_epsilon": clip_epsilon,
        "trace": trace,
        "final_diagnostics": {
            "ratios": final_ratios,
            "clipped_ratios": final_clipped_ratios,
            "unclipped": final_unclipped,
            "clipped": final_clipped,
            "objective_terms": final_terms,
            "clip_fraction": sum(1 for ratio in final_ratios if abs(ratio - 1.0) > clip_epsilon) / len(final_ratios),
            "approx_kl": sum(old - new for old, new in zip(old_log_probs, final_log_probs)) / len(old_log_probs),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-json", default="")
    parser.add_argument("--theta", type=float, default=0.0)
    parser.add_argument("--learning-rate", type=float, default=0.12)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--clip-epsilon", type=float, default=0.2)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    batch = json.loads(Path(args.batch_json).read_text()) if args.batch_json else None
    result = run_reduced_ppo(batch, args.theta, args.learning_rate, args.epochs, args.clip_epsilon)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
