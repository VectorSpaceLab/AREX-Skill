from __future__ import annotations

import json
import math
from pathlib import Path

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def dump_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def greedy_policy(forward, z_vector, state_count, action_count):
    q_values = []
    policy = []
    ties = []
    for state in range(state_count):
        row = []
        for action in range(action_count):
            embedding = forward[state * action_count + action]
            row.append(sum(embedding[k] * z_vector[k] for k in range(len(z_vector))))
        best = max(row)
        action = row.index(best)
        q_values.append(row)
        policy.append(action)
        ties.append([idx for idx, value in enumerate(row) if abs(value - best) < 1e-12])
    return {"q_values": q_values, "policy": policy, "ties": ties}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        output = greedy_policy([[1, 0], [0, 1], [1, 1], [1, 1]], [0, 2], 2, 2)
        assert output["policy"] == [1, 0]
        assert output["ties"][1] == [0, 1]
        print("ok")
    elif args.input:
        data = load_json(args.input)
        dump_json(greedy_policy(data["F"], data["z_R"], data["state_count"], data["action_count"]), args.output)
