import json
import math
from pathlib import Path


def matvec(matrix, vector):
    return [sum(weight * value for weight, value in zip(row, vector)) for row in matrix]


def squared_errors(observations, target_matrix, predictor_matrix):
    errors = []
    for obs in observations:
        target = matvec(target_matrix, obs)
        pred = matvec(predictor_matrix, obs)
        errors.append(sum((p - t) ** 2 for p, t in zip(pred, target)) / len(target))
    return errors


def mean(values):
    return sum(values) / len(values) if values else 0.0


def train_predictor(observations, target_matrix, predictor_matrix, lr=0.05, steps=100):
    params = [row[:] for row in predictor_matrix]
    losses = []
    n = len(observations)
    for _ in range(steps):
        gradients = [[0.0 for _ in row] for row in params]
        total = 0.0
        for obs in observations:
            target = matvec(target_matrix, obs)
            pred = matvec(params, obs)
            dim = len(target)
            for out_idx, (p, t) in enumerate(zip(pred, target)):
                diff = p - t
                total += diff * diff / dim
                for in_idx, value in enumerate(obs):
                    gradients[out_idx][in_idx] += (2.0 / dim) * diff * value / n
        losses.append(total / n)
        for out_idx, row in enumerate(params):
            for in_idx in range(len(row)):
                params[out_idx][in_idx] -= lr * gradients[out_idx][in_idx]
    return params, losses


def run_probe(train_observations, frequent_eval, rare_eval, target_matrix, predictor_matrix, lr=0.05, steps=100):
    trained, losses = train_predictor(train_observations, target_matrix, predictor_matrix, lr=lr, steps=steps)
    frequent_error = mean(squared_errors(frequent_eval, target_matrix, trained))
    rare_error = mean(squared_errors(rare_eval, target_matrix, trained))
    return {
        "loss_before": losses[0],
        "loss_after": losses[-1],
        "params_before": predictor_matrix,
        "params_after": trained,
        "frequent_error": frequent_error,
        "rare_error": rare_error,
        "novelty_margin": rare_error - frequent_error,
        "target_unchanged": True,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input_json).read_text())
    result = run_probe(**data)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
