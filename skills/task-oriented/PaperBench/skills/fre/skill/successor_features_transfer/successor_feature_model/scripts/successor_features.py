#!/usr/bin/env python3
"""Exact successor-feature utilities for small finite MDPs."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def _zeros(dim):
    return [0.0 for _ in range(dim)]


def _add_scaled(target, vector, scale=1.0):
    for index, value in enumerate(vector):
        target[index] += scale * value


def _dot(left, right):
    if len(left) != len(right):
        raise ValueError("feature and weight dimensions differ")
    return sum(a * b for a, b in zip(left, right))


def normalize_model(model):
    states = list(model["states"])
    actions = list(model["actions"])
    feature_dim = int(model["feature_dim"])
    transitions = model["transitions"]
    for state in states:
        if state not in transitions:
            raise ValueError(f"missing transitions for state {state}")
        for action in actions:
            if action not in transitions[state]:
                raise ValueError(f"missing transition for ({state}, {action})")
            entries = transitions[state][action]
            if not isinstance(entries, list):
                entries = [entries]
                transitions[state][action] = entries
            prob_sum = 0.0
            for entry in entries:
                prob_sum += float(entry.get("prob", 1.0))
                features = entry["features"]
                if len(features) != feature_dim:
                    raise ValueError("transition feature dimension mismatch")
                if entry["next_state"] not in states:
                    raise ValueError("transition points to unknown state")
            if not math.isclose(prob_sum, 1.0, rel_tol=1e-8, abs_tol=1e-8):
                raise ValueError(f"transition probabilities for ({state}, {action}) sum to {prob_sum}")
    return states, actions, feature_dim, transitions


def policy_action(policy, state):
    action = policy[state]
    if isinstance(action, dict):
        return max(sorted(action), key=lambda key: action[key])
    return action


def compute_successor_features(model, policy, gamma=0.9, tolerance=1e-10, max_iterations=10000):
    states, actions, feature_dim, transitions = normalize_model(model)
    psi = {state: {action: _zeros(feature_dim) for action in actions} for state in states}
    residual = float("inf")
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        residual = 0.0
        next_psi = {state: {action: _zeros(feature_dim) for action in actions} for state in states}
        for state in states:
            for action in actions:
                value = _zeros(feature_dim)
                for entry in transitions[state][action]:
                    prob = float(entry.get("prob", 1.0))
                    _add_scaled(value, entry["features"], prob)
                    if not entry.get("terminal", False):
                        next_action = policy_action(policy, entry["next_state"])
                        _add_scaled(value, psi[entry["next_state"]][next_action], prob * gamma)
                next_psi[state][action] = value
                residual = max(residual, max(abs(a - b) for a, b in zip(value, psi[state][action])))
        psi = next_psi
        iterations = iteration
        if residual <= tolerance:
            break
    return {"psi": psi, "iterations": iterations, "bellman_residual": residual, "converged": residual <= tolerance}


def values_from_successor_features(psi, weights):
    return {
        state: {action: _dot(features, weights) for action, features in action_values.items()}
        for state, action_values in psi.items()
    }


def load_json(path):
    return json.loads(Path(path).read_text())


def run_self_test():
    model = {
        "states": ["s0", "s1"],
        "actions": ["stay", "go"],
        "feature_dim": 2,
        "transitions": {
            "s0": {
                "stay": {"next_state": "s0", "features": [1.0, 0.0]},
                "go": {"next_state": "s1", "features": [0.0, 1.0], "terminal": True},
            },
            "s1": {
                "stay": {"next_state": "s1", "features": [0.0, 0.0], "terminal": True},
                "go": {"next_state": "s1", "features": [0.0, 0.0], "terminal": True},
            },
        },
    }
    result = compute_successor_features(model, {"s0": "go", "s1": "stay"}, gamma=0.5)
    assert result["converged"]
    assert result["psi"]["s0"]["go"] == [0.0, 1.0]
    values = values_from_successor_features(result["psi"], [2.0, 3.0])
    assert values["s0"]["go"] == 3.0
    return {"ok": True, "bellman_residual": result["bellman_residual"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model")
    parser.add_argument("--policy")
    parser.add_argument("--weights")
    parser.add_argument("--gamma", type=float, default=0.9)
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2))
        return
    if not (args.model and args.policy and args.output):
        raise SystemExit("--model, --policy, and --output are required unless --self-test is used")
    model = load_json(args.model)
    policy = load_json(args.policy)
    result = compute_successor_features(model, policy, gamma=args.gamma)
    if args.weights:
        result["values"] = values_from_successor_features(result["psi"], load_json(args.weights))
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
