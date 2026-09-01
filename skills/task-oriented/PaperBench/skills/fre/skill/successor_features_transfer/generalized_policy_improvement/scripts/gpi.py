#!/usr/bin/env python3
"""Generalized policy improvement for explicit value tables."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def generalized_policy_improvement(value_tables, states=None, actions=None):
    if not value_tables:
        raise ValueError("at least one source value table is required")
    source_names = sorted(value_tables)
    if states is None:
        states = sorted(next(iter(value_tables.values())).keys())
    if actions is None:
        first_state = states[0]
        actions = sorted(next(iter(value_tables.values()))[first_state].keys())
    policy = {}
    diagnostics = {"source_policy_count": len(source_names), "states": {}, "winning_sources": []}
    for state in states:
        action_candidates = []
        for action in actions:
            best_source = None
            best_value = None
            for source in source_names:
                value = float(value_tables[source][state][action])
                if best_value is None or value > best_value or (value == best_value and source < best_source):
                    best_value = value
                    best_source = source
            action_candidates.append((action, best_value, best_source))
        chosen_action, chosen_value, chosen_source = max(action_candidates, key=lambda item: (item[1], -actions.index(item[0])))
        sorted_values = sorted((item[1] for item in action_candidates), reverse=True)
        margin = sorted_values[0] - sorted_values[1] if len(sorted_values) > 1 else 0.0
        policy[state] = chosen_action
        diagnostics["states"][state] = {
            "chosen_action": chosen_action,
            "chosen_value": chosen_value,
            "winning_source": chosen_source,
            "margin_to_next_action": margin,
            "action_source_values": [
                {"action": action, "best_value": value, "source": source}
                for action, value, source in action_candidates
            ],
        }
        diagnostics["winning_sources"].append(chosen_source)
    diagnostics["unique_winning_sources"] = sorted(set(diagnostics["winning_sources"]))
    return {"policy": policy, "diagnostics": diagnostics}


def run_self_test():
    values = {
        "north_policy": {"s0": {"left": 5, "right": 1}, "s1": {"left": 0, "right": 2}},
        "east_policy": {"s0": {"left": 3, "right": 4}, "s1": {"left": 1, "right": 6}},
    }
    result = generalized_policy_improvement(values, states=["s0", "s1"], actions=["left", "right"])
    assert result["policy"] == {"s0": "left", "s1": "right"}
    assert len(result["diagnostics"]["unique_winning_sources"]) == 2
    return {"ok": True, "policy": result["policy"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--values")
    parser.add_argument("--states")
    parser.add_argument("--actions")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2))
        return
    if not (args.values and args.output):
        raise SystemExit("--values and --output are required unless --self-test is used")
    values = json.loads(Path(args.values).read_text())
    states = json.loads(Path(args.states).read_text()) if args.states else None
    actions = json.loads(Path(args.actions).read_text()) if args.actions else None
    result = generalized_policy_improvement(values, states=states, actions=actions)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
