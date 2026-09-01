#!/usr/bin/env python3
"""Reduced successor-feature transfer recovery experiment."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path

ACTIONS = ["up", "down", "left", "right"]
GAMMA = 0.9
GRID_SIZE = 3
START = "1,1"
FEATURE_GOALS = {"0,2": [1.0, 0.0, 0.0], "2,2": [0.0, 1.0, 0.0], "2,0": [0.0, 0.0, 1.0]}
SOURCE_WEIGHTS = {"red": [1.0, 0.0, 0.0], "blue": [0.0, 1.0, 0.0], "green": [0.0, 0.0, 1.0]}
TRANSFER_WEIGHTS = {"red_blue": [0.55, 1.0, -0.1], "blue_green": [-0.1, 0.55, 1.0]}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_states():
    return [f"{row},{col}" for row in range(GRID_SIZE) for col in range(GRID_SIZE)]


def step(state, action):
    row, col = [int(part) for part in state.split(",")]
    if action == "up":
        row = max(0, row - 1)
    elif action == "down":
        row = min(GRID_SIZE - 1, row + 1)
    elif action == "left":
        col = max(0, col - 1)
    elif action == "right":
        col = min(GRID_SIZE - 1, col + 1)
    next_state = f"{row},{col}"
    features = FEATURE_GOALS.get(next_state, [0.0, 0.0, 0.0])
    terminal = next_state in FEATURE_GOALS
    return next_state, features, terminal


def build_model():
    transitions = {}
    for state in all_states():
        transitions[state] = {}
        for action in ACTIONS:
            next_state, features, terminal = step(state, action)
            transitions[state][action] = {"next_state": next_state, "features": features, "terminal": terminal}
    return {"states": all_states(), "actions": ACTIONS, "feature_dim": 3, "transitions": transitions}


def reward(features, weights):
    return sum(f * w for f, w in zip(features, weights))


def value_iteration(model, weights, gamma=GAMMA, iterations=200):
    values = {state: 0.0 for state in model["states"]}
    for _ in range(iterations):
        next_values = {}
        for state in model["states"]:
            candidates = []
            for action in ACTIONS:
                entry = model["transitions"][state][action]
                value = reward(entry["features"], weights)
                if not entry.get("terminal", False):
                    value += gamma * values[entry["next_state"]]
                candidates.append(value)
            next_values[state] = max(candidates)
        values = next_values
    policy = {}
    q_values = {}
    for state in model["states"]:
        q_values[state] = {}
        for action in ACTIONS:
            entry = model["transitions"][state][action]
            value = reward(entry["features"], weights)
            if not entry.get("terminal", False):
                value += gamma * values[entry["next_state"]]
            q_values[state][action] = value
        policy[state] = max(ACTIONS, key=lambda action: (q_values[state][action], -ACTIONS.index(action)))
    return policy, q_values


def evaluate_policy(model, policy, weights, start=START, max_steps=10):
    state = start
    total = 0.0
    discount = 1.0
    trajectory = []
    for _ in range(max_steps):
        action = policy[state]
        entry = model["transitions"][state][action]
        immediate = reward(entry["features"], weights)
        total += discount * immediate
        trajectory.append({"state": state, "action": action, "next_state": entry["next_state"], "reward": immediate, "features": entry["features"]})
        if entry.get("terminal", False):
            break
        state = entry["next_state"]
        discount *= GAMMA
    return total, trajectory


def run_experiment(attempt_dir, skills_root):
    sf_module = load_module(skills_root / "successor_feature_model" / "scripts" / "successor_features.py", "successor_features")
    gpi_module = load_module(skills_root / "generalized_policy_improvement" / "scripts" / "gpi.py", "gpi")
    model = build_model()
    source_policies = {}
    source_q_values = {}
    source_psi = {}
    source_values_by_transfer = {}
    sf_residuals = []
    for source_name, weights in SOURCE_WEIGHTS.items():
        policy, q_values = value_iteration(model, weights)
        source_policies[source_name] = policy
        source_q_values[source_name] = q_values
        sf_result = sf_module.compute_successor_features(copy.deepcopy(model), policy, gamma=GAMMA)
        source_psi[source_name] = sf_result["psi"]
        sf_residuals.append(sf_result["bellman_residual"])
    task_results = []
    for task_name, weights in TRANSFER_WEIGHTS.items():
        value_tables = {}
        for source_name, psi in source_psi.items():
            value_tables[source_name] = sf_module.values_from_successor_features(psi, weights)
        source_values_by_transfer[task_name] = value_tables
        gpi_result = gpi_module.generalized_policy_improvement(value_tables, states=model["states"], actions=ACTIONS)
        gpi_return, gpi_trajectory = evaluate_policy(model, gpi_result["policy"], weights)
        baseline_name = sorted(SOURCE_WEIGHTS)[0]
        baseline_return, baseline_trajectory = evaluate_policy(model, source_policies[baseline_name], weights)
        oracle_policy, _ = value_iteration(model, weights)
        oracle_return, _ = evaluate_policy(model, oracle_policy, weights)
        task_results.append({
            "task": task_name,
            "weights": weights,
            "gpi_return": gpi_return,
            "baseline": baseline_name,
            "baseline_return": baseline_return,
            "oracle_return": oracle_return,
            "transfer_advantage": gpi_return - baseline_return,
            "gpi_policy_start_action": gpi_result["policy"][START],
            "gpi_unique_winning_sources": gpi_result["diagnostics"]["unique_winning_sources"],
            "gpi_trajectory": gpi_trajectory,
            "baseline_trajectory": baseline_trajectory,
        })
    mean_advantage = sum(item["transfer_advantage"] for item in task_results) / len(task_results)
    mechanism_checks = {
        "linear_reward_weights_used": True,
        "successor_features_computed": len(source_psi) == len(SOURCE_WEIGHTS),
        "successor_feature_bellman_residual_max": max(sf_residuals),
        "successor_feature_bellman_residual_ok": max(sf_residuals) < 1e-7,
        "gpi_policy_selected_from_multiple_sources": any(len(item["gpi_unique_winning_sources"]) > 1 for item in task_results),
        "held_out_rewards_reweighted_without_retraining": True,
        "source_policy_count": len(SOURCE_WEIGHTS),
        "transfer_task_count": len(TRANSFER_WEIGHTS),
        "optimizer_step_executed": False,
        "reduced_training_executed": False,
        "original_repo_used": False,
    }
    result = {
        "schema_version": 1,
        "paper_id": "successor_features_transfer",
        "experiment": "deterministic_linear_reward_gridworld",
        "is_proxy": True,
        "sample_count": len(task_results),
        "metrics": {"mean_transfer_advantage": mean_advantage, "mean_gpi_return": sum(x["gpi_return"] for x in task_results) / len(task_results)},
        "paper_target": json.loads((attempt_dir / "module_plan.json").read_text())["fast_recovery_target"],
        "commands": [],
        "artifacts": ["recovery/logs/generated_data_item.json", "recovery/logs/training_trace.json"],
        "mechanism_checks": mechanism_checks,
        "task_results": task_results,
        "notes": "Reduced/proxy gridworld recovery preserving shared dynamics, linear reward reweighting, successor-feature evaluation, and GPI transfer."
    }
    return result, {"model": model, "source_weights": SOURCE_WEIGHTS, "transfer_weights": TRANSFER_WEIGHTS, "start_state": START}, {"source_policies": source_policies, "source_q_values": source_q_values, "sf_residuals": sf_residuals}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    args = parser.parse_args()
    attempt_dir = Path(args.attempt_dir)
    skills_root = Path(args.skills_root)
    recovery_dir = attempt_dir / "recovery"
    logs_dir = recovery_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    result, data_item, trace = run_experiment(attempt_dir, skills_root)
    result["commands"] = ["python recovery/run_recovery.py"]
    (logs_dir / "generated_data_item.json").write_text(json.dumps(data_item, indent=2) + "\n")
    (logs_dir / "training_trace.json").write_text(json.dumps(trace, indent=2) + "\n")
    (recovery_dir / "recovery_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"ok": True, "metrics": result["metrics"], "mechanism_checks": result["mechanism_checks"]}, indent=2))


if __name__ == "__main__":
    main()
