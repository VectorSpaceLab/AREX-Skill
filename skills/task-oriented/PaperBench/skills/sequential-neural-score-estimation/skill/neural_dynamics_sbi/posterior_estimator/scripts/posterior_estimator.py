#!/usr/bin/env python3
import argparse
import json
import random


def transpose(matrix):
    return [list(column) for column in zip(*matrix)]


def solve_linear(system, values):
    n = len(values)
    aug = [list(system[i]) + [values[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular system")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [value / scale for value in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [current - factor * base for current, base in zip(aug[row], aug[col])]
    return [aug[row][-1] for row in range(n)]


def fit_conditional_gaussian(summaries, parameters, ridge=1e-3):
    if len(summaries) != len(parameters) or len(summaries) < 2:
        raise ValueError("need at least two paired summaries and parameters")
    features = [[1.0] + list(summary) for summary in summaries]
    xt = transpose(features)
    xtx = [[sum(row[i] * row[j] for row in features) for j in range(len(xt))] for i in range(len(xt))]
    for index in range(len(xtx)):
        xtx[index][index] += ridge
    param_dim = len(parameters[0])
    weights = []
    for dim in range(param_dim):
        target = [theta[dim] for theta in parameters]
        xty = [sum(row[i] * y for row, y in zip(features, target)) for i in range(len(xt))]
        weights.append(solve_linear(xtx, xty))
    residuals = []
    for summary, theta in zip(summaries, parameters):
        pred = predict_mean(weights, summary)
        residuals.extend((a - b) ** 2 for a, b in zip(theta, pred))
    variance = sum(residuals) / max(1, len(residuals))
    return {"weights": weights, "variance": variance, "simulation_count": len(summaries), "likelihood_evaluated": False}


def predict_mean(model, observed_summary):
    weights = model["weights"] if isinstance(model, dict) else model
    features = [1.0] + list(observed_summary)
    return [sum(weight * feature for weight, feature in zip(row, features)) for row in weights]


def posterior_samples(model, observed_summary, count=16, seed=0):
    rng = random.Random(seed)
    mean = predict_mean(model, observed_summary)
    scale = max(model.get("variance", 0.0), 0.0) ** 0.5 if isinstance(model, dict) else 0.0
    return [[value + rng.gauss(0.0, scale) for value in mean] for _ in range(count)]


def infer_posterior(summaries, parameters, observed_summary, ridge=1e-3, sample_count=16, seed=0):
    model = fit_conditional_gaussian(summaries, parameters, ridge=ridge)
    mean = predict_mean(model, observed_summary)
    return {
        "posterior_mean": mean,
        "posterior_samples": posterior_samples(model, observed_summary, sample_count, seed),
        "uncertainty_variance": model["variance"],
        "diagnostics": {"simulation_count": model["simulation_count"], "likelihood_evaluated": False},
        "model": model,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result = infer_posterior(payload["summaries"], payload["parameters"], payload["observed_summary"], sample_count=payload.get("sample_count", 16), seed=payload.get("seed", 0))
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)


if __name__ == "__main__":
    main()
