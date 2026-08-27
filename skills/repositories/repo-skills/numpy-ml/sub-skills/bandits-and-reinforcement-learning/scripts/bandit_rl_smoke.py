#!/usr/bin/env python3
"""Run a tiny plotting-free numpy-ml bandit/RL utility smoke."""
import argparse
import json
import warnings


def run():
    warnings.filterwarnings("ignore")
    from numpy_ml.bandits import BernoulliBandit
    from numpy_ml.bandits.policies import EpsilonGreedy, UCB1
    from numpy_ml.rl_models.rl_utils import EnvModel

    bandit = BernoulliBandit([0.2, 0.8])
    results = {}
    for policy in [EpsilonGreedy(epsilon=0.1), UCB1(C=1)]:
        policy.reset()
        rewards = []
        actions = []
        for _ in range(5):
            reward, arm_id = policy.act(bandit)
            rewards.append(int(reward))
            actions.append(int(arm_id))
        results[policy.hyperparameters["id"]] = {
            "reward_sum": int(sum(rewards)),
            "actions": actions,
            "estimate_keys": sorted([int(k) for k in policy.parameters.get("ev_estimates", {}).keys()]),
        }

    env_model = EnvModel()
    env_model[(0, 1, 1, 2)] += 1
    outcomes = env_model.outcome_probs(0, 1)
    return {"bandits": results, "env_model_pairs": env_model.state_action_pairs(), "env_model_outcomes": outcomes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("numpy-ml bandit/RL smoke passed")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
