import argparse, json, math, random
from pathlib import Path


def build_gaussian_linear_task(dim=2, prior_scale=1.0, simulator_scale=0.5, seed=0, observation=None):
    if dim <= 0:
        raise ValueError('dim must be positive')
    if prior_scale <= 0 or simulator_scale <= 0:
        raise ValueError('scales must be positive')
    rng = random.Random(seed)
    if observation is None:
        observation = [rng.gauss(0.0, math.sqrt(prior_scale + simulator_scale)) for _ in range(dim)]
    if len(observation) != dim:
        raise ValueError('observation length must match dim')
    prior_precision = 1.0 / prior_scale
    simulator_precision = 1.0 / simulator_scale
    posterior_variance = 1.0 / (prior_precision + simulator_precision)
    gain = posterior_variance * simulator_precision
    posterior_mean = [gain * float(x) for x in observation]
    return {
        'schema_version': 1,
        'task_name': 'gaussian_linear_proxy',
        'dim_parameters': dim,
        'dim_data': dim,
        'prior': {'mean': [0.0] * dim, 'variance': prior_scale},
        'simulator': {'noise_variance': simulator_scale},
        'observation': [float(x) for x in observation],
        'posterior': {'mean': posterior_mean, 'variance': posterior_variance},
        'num_observations': 1,
        'simulation_budget': 256,
        'is_resource_derived': False,
        'resource_files': [],
        'mechanism': 'conjugate Gaussian prior plus Gaussian simulator noise',
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--dim', type=int, default=2)
    parser.add_argument('--prior-scale', type=float, default=1.0)
    parser.add_argument('--simulator-scale', type=float, default=0.5)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    item = build_gaussian_linear_task(args.dim, args.prior_scale, args.simulator_scale, args.seed)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(item, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'output': str(out), 'task_name': item['task_name']}))

if __name__ == '__main__':
    main()
