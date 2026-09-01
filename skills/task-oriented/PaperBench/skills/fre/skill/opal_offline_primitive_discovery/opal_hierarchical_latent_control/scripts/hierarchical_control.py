#!/usr/bin/env python3
"""Reduced high-level latent controller for OPAL recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_latent_dataset(segments, assignments):
    items = []
    for segment, latent in zip(segments, assignments):
        items.append({
            "initial_state": segment.get("initial_state"),
            "latent": latent,
            "reward_sum": segment.get("reward_sum", 0.0),
            "horizon": segment.get("horizon", len(segment.get("actions", []))),
        })
    return items


def rollout_latent_controller(objective_result, start=0.0, goal=6.0, horizon=3, max_latent_decisions=4):
    prototypes = objective_result["params_after"]
    positive_latent = max(prototypes, key=lambda key: prototypes[key])
    negative_latent = min(prototypes, key=lambda key: prototypes[key])
    state = float(start)
    trace = []
    for decision in range(max_latent_decisions):
        latent = positive_latent if goal >= state else negative_latent
        action = float(prototypes[latent])
        primitive_actions = []
        for _ in range(horizon):
            state += action
            primitive_actions.append(action)
        trace.append({"decision": decision, "latent": int(latent), "decoded_action": action, "primitive_actions": primitive_actions, "state_after": state})
        if (goal >= start and state >= goal) or (goal < start and state <= goal):
            break
    success = (goal >= start and state >= goal) or (goal < start and state <= goal)
    return {
        "success": success,
        "success_rate": 1.0 if success else 0.0,
        "start": start,
        "goal": goal,
        "final_state": state,
        "latent_decision_count": len(trace),
        "primitive_action_count": sum(len(item["primitive_actions"]) for item in trace),
        "effective_horizon_reduction": horizon,
        "trace": trace,
    }


def evaluate_hierarchical_control(segment_payload, objective_result, goal=6.0):
    segments = segment_payload.get("segments", segment_payload)
    assignments = objective_result["assignments"]
    horizon = segments[0].get("horizon", len(segments[0].get("actions", []))) if segments else 1
    latent_dataset = build_latent_dataset(segments, assignments)
    rollout = rollout_latent_controller(objective_result, start=0.0, goal=goal, horizon=horizon)
    return {"latent_dataset": latent_dataset, "rollout": rollout}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segments_json")
    parser.add_argument("objective_json")
    parser.add_argument("--goal", type=float, default=6.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    segments = json.loads(Path(args.segments_json).read_text(encoding="utf-8"))
    objective = json.loads(Path(args.objective_json).read_text(encoding="utf-8"))
    result = evaluate_hierarchical_control(segments, objective, goal=args.goal)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["rollout"], indent=2))


if __name__ == "__main__":
    main()
