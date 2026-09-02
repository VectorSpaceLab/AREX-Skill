import json
from pathlib import Path


def discounted_returns(rewards, dones, gamma, episodic=True):
    returns = [0.0 for _ in rewards]
    running = 0.0
    for idx in range(len(rewards) - 1, -1, -1):
        if episodic and dones[idx]:
            running = 0.0
        running = rewards[idx] + gamma * running
        returns[idx] = running
    return returns


def combine_advantages(extrinsic_rewards, intrinsic_rewards, dones, gamma_e, gamma_i, values_e=None, values_i=None, intrinsic_non_episodic=True):
    values_e = values_e or [0.0 for _ in extrinsic_rewards]
    values_i = values_i or [0.0 for _ in intrinsic_rewards]
    returns_e = discounted_returns(extrinsic_rewards, dones, gamma_e, episodic=True)
    returns_i = discounted_returns(intrinsic_rewards, dones, gamma_i, episodic=not intrinsic_non_episodic)
    advantages_e = [ret - val for ret, val in zip(returns_e, values_e)]
    advantages_i = [ret - val for ret, val in zip(returns_i, values_i)]
    combined = [left + right for left, right in zip(advantages_e, advantages_i)]
    return {
        "extrinsic_returns": returns_e,
        "intrinsic_returns": returns_i,
        "extrinsic_advantages": advantages_e,
        "intrinsic_advantages": advantages_i,
        "combined_advantages": combined,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text())
    result = combine_advantages(**data)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
