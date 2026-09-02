import argparse, json, math

def expected_norm(n):
    return math.sqrt(n) * (1.0 - 1.0/(4*n) + 1.0/(21*n*n))

def default_parameters(n, lambda_=None):
    if n < 1:
        raise ValueError('dimension must be positive')
    lam = int(lambda_ if lambda_ is not None else 4 + math.floor(3 * math.log(n)))
    if lam < 2:
        raise ValueError('lambda must be at least 2')
    mu = lam // 2
    raw = [math.log(mu + 0.5) - math.log(i + 1) for i in range(mu)]
    total = sum(raw)
    weights = [w / total for w in raw]
    mueff = 1.0 / sum(w*w for w in weights)
    cm = 1.0
    cs = (mueff + 2.0) / (n + mueff + 5.0)
    ds = 1.0 + 2.0 * max(0.0, math.sqrt((mueff - 1.0)/(n + 1.0)) - 1.0) + cs
    cc = (4.0 + mueff / n) / (n + 4.0 + 2.0 * mueff / n)
    c1 = 2.0 / ((n + 1.3)**2 + mueff)
    cmu = min(1.0 - c1, 2.0 * (mueff - 2.0 + 1.0/mueff) / ((n + 2.0)**2 + 2.0 * mueff / 2.0))
    return {'dimension': n, 'lambda': lam, 'mu': mu, 'weights': weights, 'mueff': mueff, 'cm': cm, 'cs': cs, 'ds': ds, 'cc': cc, 'c1': c1, 'cmu': max(0.0, cmu), 'expected_norm': expected_norm(n)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dimension', type=int, required=True)
    ap.add_argument('--lambda', dest='lambda_', type=int, default=None)
    args = ap.parse_args()
    print(json.dumps(default_parameters(args.dimension, args.lambda_), indent=2))
if __name__ == '__main__':
    main()
