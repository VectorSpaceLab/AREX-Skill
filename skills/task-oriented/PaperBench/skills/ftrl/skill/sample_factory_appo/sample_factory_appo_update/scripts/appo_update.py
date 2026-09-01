#!/usr/bin/env python3
import json
import math


def _check_lengths(*series):
    lengths = {len(item) for item in series}
    if len(lengths) != 1:
        raise ValueError("trajectory series must have matching lengths")
    if not lengths or next(iter(lengths)) == 0:
        raise ValueError("trajectory must be non-empty")


def importance_ratios(behavior_log_probs, target_log_probs):
    _check_lengths(behavior_log_probs, target_log_probs)
    return [math.exp(target - behavior) for behavior, target in zip(behavior_log_probs, target_log_probs)]


def vtrace_targets(rewards, discounts, values, bootstrap_value, behavior_log_probs, target_log_probs, rho_bar=1.0, c_bar=1.0):
    _check_lengths(rewards, discounts, values, behavior_log_probs, target_log_probs)
    ratios = importance_ratios(behavior_log_probs, target_log_probs)
    rhos = [min(rho_bar, ratio) for ratio in ratios]
    cs = [min(c_bar, ratio) for ratio in ratios]
    next_values = values[1:] + [bootstrap_value]
    deltas = [rho * (reward + discount * next_value - value) for rho, reward, discount, next_value, value in zip(rhos, rewards, discounts, next_values, values)]
    targets = [0.0] * len(rewards)
    accumulator = bootstrap_value
    for index in reversed(range(len(rewards))):
        if index == len(rewards) - 1:
            accumulator = values[index] + deltas[index]
        else:
            accumulator = values[index] + deltas[index] + discounts[index] * cs[index] * (accumulator - next_values[index])
        targets[index] = accumulator
    return {"ratios": ratios, "rhos": rhos, "cs": cs, "value_targets": targets}


def ppo_policy_loss(advantages, behavior_log_probs, target_log_probs, clip=0.2):
    _check_lengths(advantages, behavior_log_probs, target_log_probs)
    ratios = importance_ratios(behavior_log_probs, target_log_probs)
    clipped = [min(1.0 + clip, max(1.0 - clip, ratio)) for ratio in ratios]
    surrogate = [min(ratio * adv, clipped_ratio * adv) for ratio, clipped_ratio, adv in zip(ratios, clipped, advantages)]
    return {"ratios": ratios, "clipped_ratios": clipped, "policy_loss": -sum(surrogate) / len(surrogate)}


def value_loss(values, targets):
    _check_lengths(values, targets)
    return sum((value - target) ** 2 for value, target in zip(values, targets)) / len(values)


def scalar_optimizer_step(parameter, observation, action, advantage, learning_rate=0.1, clip=0.2):
    logit = parameter * observation
    probability = 1.0 / (1.0 + math.exp(-logit))
    chosen_probability = probability if action == 1 else 1.0 - probability
    unclipped_gradient = (action - probability) * observation * advantage
    clipped_gradient = max(-clip, min(clip, unclipped_gradient))
    before_loss = -math.log(max(chosen_probability, 1e-8)) * advantage
    new_parameter = parameter + learning_rate * clipped_gradient
    new_logit = new_parameter * observation
    new_probability = 1.0 / (1.0 + math.exp(-new_logit))
    new_chosen_probability = new_probability if action == 1 else 1.0 - new_probability
    after_loss = -math.log(max(new_chosen_probability, 1e-8)) * advantage
    return {
        "params_before": {"policy_weight": parameter},
        "params_after": {"policy_weight": new_parameter},
        "loss_before": before_loss,
        "loss_after": after_loss,
        "gradient": clipped_gradient,
        "optimizer_step_executed": new_parameter != parameter,
    }


def demo_update():
    rewards = [1.0, 0.5, -0.1]
    discounts = [0.99, 0.99, 0.0]
    values = [0.2, 0.1, -0.05]
    behavior = [-0.7, -0.6, -0.8]
    target = [-0.6, -0.7, -0.75]
    vtrace = vtrace_targets(rewards, discounts, values, 0.0, behavior, target)
    advantages = [target_value - value for target_value, value in zip(vtrace["value_targets"], values)]
    ppo = ppo_policy_loss(advantages, behavior, target)
    trace = scalar_optimizer_step(0.1, 1.0, 1, advantages[0])
    return {"vtrace": vtrace, "advantages": advantages, "ppo": ppo, "value_loss": value_loss(values, vtrace["value_targets"]), "optimizer_trace": trace}


if __name__ == "__main__":
    print(json.dumps(demo_update(), indent=2, sort_keys=True))
