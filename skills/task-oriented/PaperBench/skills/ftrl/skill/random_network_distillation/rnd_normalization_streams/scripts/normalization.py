import json
import math
from pathlib import Path


def flatten(batch):
    return [row[:] for row in batch]


def running_stats(batch):
    rows = flatten(batch)
    count = len(rows)
    dims = len(rows[0]) if rows else 0
    mean = [sum(row[i] for row in rows) / count for i in range(dims)]
    var = [sum((row[i] - mean[i]) ** 2 for row in rows) / count for i in range(dims)]
    return {"mean": mean, "var": var, "count": count}


def normalize_observations(batch, stats, clip=5.0, eps=1e-8):
    output = []
    for row in batch:
        norm = []
        for i, value in enumerate(row):
            scaled = (value - stats["mean"][i]) / math.sqrt(stats["var"][i] + eps)
            norm.append(max(-clip, min(clip, scaled)))
        output.append(norm)
    return output


def scale_rewards(rewards, return_std, eps=1e-8):
    denom = math.sqrt(return_std * return_std + eps)
    return [reward / denom for reward in rewards]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text())
    stats = running_stats(data["observations"])
    result = {
        "stats": stats,
        "normalized_observations": normalize_observations(data["observations"], stats, data.get("clip", 5.0)),
        "scaled_rewards": scale_rewards(data.get("rewards", []), data.get("return_std", 1.0)),
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
