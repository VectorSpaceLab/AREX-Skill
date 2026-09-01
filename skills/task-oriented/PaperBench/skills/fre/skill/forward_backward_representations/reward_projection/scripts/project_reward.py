from __future__ import annotations

import json
import math
from pathlib import Path

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def dump_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def project_reward(backward, rewards):
    z_vector = [0.0] * len(backward[0])
    used = []
    for item in rewards:
        index = int(item["index"])
        reward = float(item["reward"])
        if index < 0 or index >= len(backward):
            raise IndexError("reward index outside B")
        used.append({"index": index, "reward": reward})
        for k, value in enumerate(backward[index]):
            z_vector[k] += reward * value
    return {"z_R": z_vector, "used_rewards": used, "reward_count": len(used)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        output = project_reward([[1, 0], [0, 1], [2, 3]], [{"index": 0, "reward": 2}, {"index": 2, "reward": 0.5}])
        assert output["z_R"] == [3.0, 1.5]
        print("ok")
    elif args.input:
        data = load_json(args.input)
        dump_json(project_reward(data["B"], data["rewards"]), args.output)
