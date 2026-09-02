#!/usr/bin/env python3
"""Small deterministic Q-style update used by JSRL reduced recovery."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy


ACTIONS = (-1, 1)


def key(state: int, action: int) -> str:
    return f"s{int(state)}_a{int(action)}"


def q_value(params: dict[str, float], state: int, action: int) -> float:
    return float(params.get(key(state, action), 0.0))


def greedy_action(params: dict[str, float], state: int) -> int:
    values = [(q_value(params, state, action), action) for action in ACTIONS]
    values.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return int(values[0][1])


def transition_loss(params: dict[str, float], transition: dict, discount: float) -> float:
    state = int(transition["state"])
    action = int(transition["action"])
    reward = float(transition.get("reward", 0.0))
    next_state = int(transition.get("next_state", state))
    done = bool(transition.get("done", False))
    bootstrap = 0.0 if done else max(q_value(params, next_state, a) for a in ACTIONS)
    target = reward + discount * bootstrap
    error = target - q_value(params, state, action)
    return error * error


def mean_loss(params: dict[str, float], transitions: list[dict], discount: float = 0.95) -> float:
    if not transitions:
        return 0.0
    return sum(transition_loss(params, row, discount) for row in transitions) / len(transitions)


def update_q_values(params: dict[str, float], transitions: list[dict], learning_rate: float = 0.5, discount: float = 0.95) -> tuple[dict[str, float], dict]:
    params_before = deepcopy(params)
    loss_before = mean_loss(params_before, transitions, discount)
    updated = deepcopy(params)
    for row in transitions:
        state = int(row["state"])
        action = int(row["action"])
        reward = float(row.get("reward", 0.0))
        next_state = int(row.get("next_state", state))
        done = bool(row.get("done", False))
        bootstrap = 0.0 if done else max(q_value(updated, next_state, a) for a in ACTIONS)
        target = reward + discount * bootstrap
        current = q_value(updated, state, action)
        updated[key(state, action)] = current + learning_rate * (target - current)
    loss_after = mean_loss(updated, transitions, discount)
    trace = {
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": params_before,
        "params_after": updated,
        "parameters_before": params_before,
        "parameters_after": updated,
        "optimizer_state_changed": params_before != updated,
        "learning_rate": learning_rate,
        "discount": discount,
    }
    return updated, trace


def demo_transitions() -> list[dict]:
    return [
        {"state": 5, "action": 1, "reward": 1.0, "next_state": 6, "done": True, "controller": "exploration"},
        {"state": 4, "action": 1, "reward": 0.0, "next_state": 5, "done": False, "controller": "exploration"},
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    updated, trace = update_q_values({}, demo_transitions())
    print(json.dumps({"params": updated, "trace": trace}, indent=2))
    return 0 if trace["optimizer_state_changed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
