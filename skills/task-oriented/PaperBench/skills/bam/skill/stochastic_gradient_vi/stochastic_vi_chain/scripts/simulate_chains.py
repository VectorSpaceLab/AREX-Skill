#!/usr/bin/env python3
import argparse
import json
import math
import random
from pathlib import Path


def squared_distance(values, optimum):
    return sum((value - target) ** 2 for value, target in zip(values, optimum))


def simulate_chains(chains=4, iterations=400, dimensions=8, learning_rate=0.08, noise_scale=0.22, seed=7, optimum=None):
    if chains <= 0 or iterations <= 0 or dimensions <= 0:
        raise ValueError('chains, iterations, and dimensions must be positive')
    if learning_rate <= 0:
        raise ValueError('learning_rate must be positive')
    if noise_scale < 0:
        raise ValueError('noise_scale must be non-negative')
    rng = random.Random(seed)
    if optimum is None:
        optimum = [0.15 * math.sin(i + 1) for i in range(dimensions)]
    if len(optimum) != dimensions:
        raise ValueError('optimum length must match dimensions')

    initial_parameters = []
    all_iterates = []
    all_gradients = []
    for chain_index in range(chains):
        params = [target + rng.uniform(-2.5, 2.5) + 0.2 * chain_index for target in optimum]
        initial_parameters.append(list(params))
        chain_iterates = []
        chain_gradients = []
        for _ in range(iterations):
            gradient = []
            for value, target in zip(params, optimum):
                deterministic_gradient = target - value
                noisy_gradient = deterministic_gradient + rng.gauss(0.0, noise_scale)
                gradient.append(noisy_gradient)
            params = [value + learning_rate * grad for value, grad in zip(params, gradient)]
            chain_iterates.append(list(params))
            chain_gradients.append(gradient)
        all_iterates.append(chain_iterates)
        all_gradients.append(chain_gradients)

    first_distance = sum(squared_distance(params, optimum) for params in initial_parameters) / chains
    final_distance = sum(squared_distance(trace[-1], optimum) for trace in all_iterates) / chains
    return {
        'schema_version': 1,
        'chains': chains,
        'iterations': iterations,
        'dimensions': dimensions,
        'learning_rate': learning_rate,
        'noise_scale': noise_scale,
        'seed': seed,
        'optimum': optimum,
        'initial_parameters': initial_parameters,
        'iterates': all_iterates,
        'gradients': all_gradients,
        'mean_initial_squared_distance': first_distance,
        'mean_final_squared_distance': final_distance,
        'optimizer_step_executed': True,
        'full_model_training_executed': False,
        'reduced_training_executed': True,
    }


def main():
    parser = argparse.ArgumentParser(description='Simulate noisy stochastic VI optimizer chains.')
    parser.add_argument('--chains', type=int, default=4)
    parser.add_argument('--iterations', type=int, default=400)
    parser.add_argument('--dimensions', type=int, default=8)
    parser.add_argument('--learning-rate', type=float, default=0.08)
    parser.add_argument('--noise-scale', type=float, default=0.22)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = simulate_chains(args.chains, args.iterations, args.dimensions, args.learning_rate, args.noise_scale, args.seed)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({
        'output': args.output,
        'chains': result['chains'],
        'iterations': result['iterations'],
        'dimensions': result['dimensions'],
        'mean_final_squared_distance': result['mean_final_squared_distance'],
    }, indent=2))


if __name__ == '__main__':
    main()
