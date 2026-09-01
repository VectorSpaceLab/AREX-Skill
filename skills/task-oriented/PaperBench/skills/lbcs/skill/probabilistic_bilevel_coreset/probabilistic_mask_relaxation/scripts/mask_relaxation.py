import argparse, json, math, random


def initialize_probabilities(n, budget):
    if n <= 0:
        raise ValueError('n must be positive')
    if budget < 0:
        raise ValueError('budget must be nonnegative')
    value = min(float(budget) / float(n), 1.0)
    return [value for _ in range(n)]


def sample_mask(probabilities, seed=None):
    rng = random.Random(seed)
    mask = []
    for probability in probabilities:
        if probability < 0.0 or probability > 1.0 or not math.isfinite(probability):
            raise ValueError('probabilities must be finite values in [0, 1]')
        mask.append(1 if rng.random() < probability else 0)
    return mask


def score_gradient(probabilities, mask, eps=1e-6):
    if len(probabilities) != len(mask):
        raise ValueError('probabilities and mask must have equal length')
    gradient = []
    for probability, bit in zip(probabilities, mask):
        if bit not in (0, 1):
            raise ValueError('mask values must be binary')
        clipped = min(max(float(probability), eps), 1.0 - eps)
        gradient.append((float(bit) - clipped) / (clipped * (1.0 - clipped)))
    return gradient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, required=True)
    parser.add_argument('--budget', type=float, required=True)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    probabilities = initialize_probabilities(args.n, args.budget)
    mask = sample_mask(probabilities, args.seed)
    print(json.dumps({'probabilities': probabilities, 'mask': mask, 'score_gradient': score_gradient(probabilities, mask)}))

if __name__ == '__main__':
    main()
