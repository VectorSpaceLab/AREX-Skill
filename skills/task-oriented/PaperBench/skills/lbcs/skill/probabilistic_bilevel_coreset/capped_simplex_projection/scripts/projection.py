import argparse, json, math


def project_capped_simplex(values, budget, iterations=80):
    if budget < 0:
        raise ValueError('budget must be nonnegative')
    vector = [float(value) for value in values]
    if any(not math.isfinite(value) for value in vector):
        raise ValueError('values must be finite')
    n = len(vector)
    if n == 0:
        return []
    if budget <= 0:
        return [0.0 for _ in vector]
    clipped = [min(max(value, 0.0), 1.0) for value in vector]
    if budget >= n or sum(clipped) <= budget + 1e-12:
        return clipped
    low = min(vector) - 1.0
    high = max(vector)
    for _ in range(iterations):
        tau = (low + high) / 2.0
        projected = [min(max(value - tau, 0.0), 1.0) for value in vector]
        if sum(projected) > budget:
            low = tau
        else:
            high = tau
    tau = high
    return [min(max(value - tau, 0.0), 1.0) for value in vector]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--values', required=True, help='JSON list of numbers')
    parser.add_argument('--budget', type=float, required=True)
    args = parser.parse_args()
    print(json.dumps({'projected': project_capped_simplex(json.loads(args.values), args.budget)}))

if __name__ == '__main__':
    main()
