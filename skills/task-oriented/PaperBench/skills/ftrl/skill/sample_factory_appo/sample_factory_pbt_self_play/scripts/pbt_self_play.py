#!/usr/bin/env python3
import json
import random


def assign_policies(agent_ids, policy_ids, seed=0):
    if not agent_ids:
        raise ValueError("agent_ids must be non-empty")
    if not policy_ids:
        raise ValueError("policy_ids must be non-empty")
    rng = random.Random(seed)
    return [{"agent_id": agent, "policy_id": rng.choice(policy_ids)} for agent in agent_ids]


def rank_population(scores):
    if not scores:
        raise ValueError("scores must be non-empty")
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def mutate_hyperparameters(hyperparameters, factor=1.2, bounds=None):
    if bounds is None:
        bounds = {}
    mutated = {}
    for key, value in hyperparameters.items():
        if value <= 0:
            raise ValueError(f"hyperparameter {key} must be positive")
        lower, upper = bounds.get(key, (0.0, float("inf")))
        candidate = value * factor
        mutated[key] = min(upper, max(lower, candidate))
    return mutated


def pbt_decisions(scores, hyperparameters, threshold_fraction=0.5, mutation_factor=1.2, bounds=None):
    ranking = rank_population(scores)
    best_policy, best_score = ranking[0]
    decisions = []
    for policy_id, score in ranking:
        if policy_id == best_policy:
            decisions.append({"policy_id": policy_id, "action": "keep", "score": score})
            continue
        if best_score > 0 and score < threshold_fraction * best_score:
            decisions.append({
                "policy_id": policy_id,
                "action": "replace_and_mutate",
                "source_policy_id": best_policy,
                "score": score,
                "new_hyperparameters": mutate_hyperparameters(hyperparameters[best_policy], mutation_factor, bounds),
            })
        else:
            decisions.append({"policy_id": policy_id, "action": "keep", "score": score})
    return {"best_policy_id": best_policy, "best_score": best_score, "decisions": decisions}


def demo():
    policies = ["p0", "p1", "p2", "p3"]
    scores = {"p0": 0.8, "p1": 0.3, "p2": 0.6, "p3": 0.1}
    hyper = {policy: {"learning_rate": 0.001, "entropy_coef": 0.01} for policy in policies}
    bounds = {"learning_rate": (1e-5, 0.01), "entropy_coef": (0.0, 0.1)}
    return {"assignments": assign_policies(["agent_a", "agent_b"], policies), "pbt": pbt_decisions(scores, hyper, bounds=bounds)}


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, sort_keys=True))
