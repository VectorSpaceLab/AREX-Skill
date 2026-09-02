import argparse
import json
import math
import random
from pathlib import Path


def logsumexp(values):
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def normal_logpdf(value, mean, sigma):
    return -0.5 * math.log(2.0 * math.pi * sigma * sigma) - 0.5 * ((value - mean) / sigma) ** 2


def generate_observations(seed=0, n_observations=80, theta_true=(1.0, -2.0), sigma_x=2.5, mix_prob=0.5):
    rng = random.Random(seed)
    observations = []
    labels = []
    for _ in range(n_observations):
        label = 0 if rng.random() < mix_prob else 1
        mean = theta_true[0] if label == 0 else theta_true[0] + theta_true[1]
        observations.append(rng.gauss(mean, sigma_x))
        labels.append(label)
    return observations, labels


def log_prior(theta, sigma1=1.0, sigma2=1.0):
    return normal_logpdf(theta[0], 0.0, sigma1) + normal_logpdf(theta[1], 0.0, sigma2)


def log_likelihood(theta, x, sigma_x=2.5, mix_prob=0.5):
    first = math.log(mix_prob) + normal_logpdf(x, theta[0], sigma_x)
    second = math.log(1.0 - mix_prob) + normal_logpdf(x, theta[0] + theta[1], sigma_x)
    return logsumexp([first, second])


def log_likelihood_dataset(theta, observations, sigma_x=2.5, mix_prob=0.5):
    return sum(log_likelihood(theta, x, sigma_x=sigma_x, mix_prob=mix_prob) for x in observations)


def log_posterior(theta, observations, sigma1=1.0, sigma2=1.0, sigma_x=2.5, mix_prob=0.5):
    return log_prior(theta, sigma1=sigma1, sigma2=sigma2) + log_likelihood_dataset(theta, observations, sigma_x=sigma_x, mix_prob=mix_prob)


def posterior_grid(observations, grid_min=-4.0, grid_max=4.0, grid_size=41, sigma1=1.0, sigma2=1.0, sigma_x=2.5, mix_prob=0.5):
    axis = [grid_min + (grid_max - grid_min) * i / (grid_size - 1) for i in range(grid_size)]
    log_values = []
    for theta1 in axis:
        row = []
        for theta2 in axis:
            row.append(log_posterior((theta1, theta2), observations, sigma1=sigma1, sigma2=sigma2, sigma_x=sigma_x, mix_prob=mix_prob))
        log_values.append(row)
    max_log = max(max(row) for row in log_values)
    cell_area = ((axis[1] - axis[0]) ** 2) if grid_size > 1 else 1.0
    density = [[math.exp(value - max_log) for value in row] for row in log_values]
    normalizer = sum(sum(row) for row in density) * cell_area
    density = [[value / normalizer for value in row] for row in density]
    return {"theta1": axis, "theta2": axis, "density": density, "cell_area": cell_area}


def build_protocol(seed=0, n_observations=80, grid_size=41):
    observations, labels = generate_observations(seed=seed, n_observations=n_observations)
    grid = posterior_grid(observations, grid_size=grid_size)
    return {
        "seed": seed,
        "n_observations": n_observations,
        "theta_true": [1.0, -2.0],
        "sigma1": 1.0,
        "sigma2": 1.0,
        "sigma_x": 2.5,
        "mix_prob": 0.5,
        "observations": observations,
        "labels": labels,
        "expected_modes": [[1.0, -2.0], [-1.0, 2.0]],
        "grid": grid,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--n-observations", type=int, default=80)
    parser.add_argument("--grid-size", type=int, default=41)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    protocol = build_protocol(seed=args.seed, n_observations=args.n_observations, grid_size=args.grid_size)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(protocol, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
