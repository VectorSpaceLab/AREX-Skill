#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def feature_value(observation: Any, action: Any) -> float:
    if isinstance(observation, list) and observation:
        obs = float(observation[0])
    else:
        obs = float(observation)
    return obs + 1.0 + float(action)


def mean_squared_td_loss(transitions: list[dict[str, Any]], weight: float, gamma: float = 0.9) -> float:
    total = 0.0
    for transition in transitions:
        current = weight * feature_value(transition["observation"], transition["action"])
        next_action = transition.get("next_action", transition["action"])
        bootstrap = 0.0 if transition.get("terminal") else weight * feature_value(transition["next_observation"], next_action)
        target = float(transition["reward"]) + gamma * bootstrap
        total += (current - target) ** 2
    return total / len(transitions)


def one_gradient_step(transitions: list[dict[str, Any]], weight: float = 0.0, learning_rate: float = 0.05, gamma: float = 0.9) -> dict[str, Any]:
    gradient = 0.0
    for transition in transitions:
        feature = feature_value(transition["observation"], transition["action"])
        current = weight * feature
        next_action = transition.get("next_action", transition["action"])
        next_feature = feature_value(transition["next_observation"], next_action)
        bootstrap = 0.0 if transition.get("terminal") else weight * next_feature
        target = float(transition["reward"]) + gamma * bootstrap
        gradient += 2.0 * (current - target) * feature / len(transitions)
    new_weight = weight - learning_rate * gradient
    return {
        "params_before": {"weight": weight},
        "params_after": {"weight": new_weight},
        "loss_before": mean_squared_td_loss(transitions, weight, gamma),
        "loss_after": mean_squared_td_loss(transitions, new_weight, gamma),
        "gradient": gradient,
        "learning_rate": learning_rate,
        "gamma": gamma,
        "optimizer_state_changed": new_weight != weight,
    }
