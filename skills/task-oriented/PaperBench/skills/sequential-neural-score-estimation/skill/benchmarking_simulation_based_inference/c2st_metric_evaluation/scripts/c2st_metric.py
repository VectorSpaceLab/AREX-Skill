import argparse, json, math
from pathlib import Path


def _validate(samples):
    if not samples or not samples[0]:
        raise ValueError('sample matrix must be non-empty')
    dim = len(samples[0])
    for row in samples:
        if len(row) != dim:
            raise ValueError('inconsistent sample dimension')
    return dim


def _mean(xs):
    return [sum(row[j] for row in xs) / len(xs) for j in range(len(xs[0]))]


def _std(xs, means):
    out=[]
    for j,m in enumerate(means):
        var=sum((row[j]-m)**2 for row in xs)/max(1,len(xs)-1)
        out.append(math.sqrt(var) if var > 1e-12 else 1.0)
    return out


def c2st_accuracy(reference, approximate, threshold=0.62):
    dim = _validate(reference)
    if _validate(approximate) != dim:
        raise ValueError('sample dimensions differ')
    means = _mean(reference); stds = _std(reference, means)
    zr = [[(x[j]-means[j])/stds[j] for j in range(dim)] for x in reference]
    za = [[(x[j]-means[j])/stds[j] for j in range(dim)] for x in approximate]
    mr = _mean(zr); ma = _mean(za)
    direction = [ma[j]-mr[j] for j in range(dim)]
    norm = math.sqrt(sum(v*v for v in direction))
    if norm < 1e-12:
        acc = 0.5
    else:
        midpoint = [(ma[j]+mr[j])/2 for j in range(dim)]
        def score(row): return sum((row[j]-midpoint[j])*direction[j] for j in range(dim))
        ref_correct = sum(1 for row in zr if score(row) < 0) / len(zr)
        app_correct = sum(1 for row in za if score(row) >= 0) / len(za)
        acc = 0.5 * (ref_correct + app_correct)
    return {'schema_version': 1, 'metric': 'c2st_accuracy', 'c2st_accuracy': float(acc), 'target_value': 0.5, 'threshold': threshold, 'accepted': acc <= threshold, 'mean_distance_z': float(norm)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--threshold', type=float, default=0.62)
    args = parser.parse_args(argv)
    data = json.loads(Path(args.samples).read_text(encoding='utf-8'))
    metric = c2st_accuracy(data['reference_samples'], data['approximate_samples'], args.threshold)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metric, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'output': str(out), 'c2st_accuracy': metric['c2st_accuracy']}))

if __name__ == '__main__':
    main()
