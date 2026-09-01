import argparse, json, random
from pathlib import Path


def _draw_matrix(mean, variance, count, seed):
    rng = random.Random(seed)
    sd = variance ** 0.5
    return [[rng.gauss(m, sd) for m in mean] for _ in range(count)]


def sample_posteriors(task_item, num_samples=256, seed=0, mode='matched'):
    if num_samples < 4:
        raise ValueError('num_samples must be at least 4')
    posterior = task_item['posterior']
    mean = [float(x) for x in posterior['mean']]
    variance = float(posterior['variance'])
    ref = _draw_matrix(mean, variance, num_samples, seed)
    approx_mean = list(mean)
    approx_variance = variance
    if mode == 'shifted':
        approx_mean = [x + 0.75 for x in mean]
    elif mode == 'wide':
        approx_variance = variance * 2.0
    elif mode != 'matched':
        raise ValueError('unknown approximation mode')
    approx = _draw_matrix(approx_mean, approx_variance, num_samples, seed + 1009)
    return {'schema_version': 1, 'task_name': task_item['task_name'], 'num_samples': num_samples, 'seed': seed, 'mode': mode, 'reference_samples': ref, 'approximate_samples': approx, 'approximation': {'mean': approx_mean, 'variance': approx_variance}}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--num-samples', type=int, default=256)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--mode', default='matched')
    args = parser.parse_args(argv)
    task = json.loads(Path(args.task).read_text(encoding='utf-8'))
    samples = sample_posteriors(task, args.num_samples, args.seed, args.mode)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(samples, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'output': str(out), 'num_samples': args.num_samples}))

if __name__ == '__main__':
    main()
