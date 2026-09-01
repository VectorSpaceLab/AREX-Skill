import argparse, json, math, sys
from pathlib import Path

try:
    from mask_relaxation import score_gradient
except Exception:
    skill_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(skill_root / 'probabilistic_mask_relaxation' / 'scripts'))
    from mask_relaxation import score_gradient

try:
    from projection import project_capped_simplex
except Exception:
    skill_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(skill_root / 'capped_simplex_projection' / 'scripts'))
    from projection import project_capped_simplex


def policy_gradient_update(probabilities, mask, outer_loss, learning_rate, budget):
    if outer_loss < 0 or not math.isfinite(outer_loss):
        raise ValueError('outer_loss must be a finite nonnegative scalar')
    gradient = score_gradient(probabilities, mask)
    raw = [float(prob) - learning_rate * outer_loss * grad for prob, grad in zip(probabilities, gradient)]
    updated = project_capped_simplex(raw, budget)
    return {'updated_probabilities': updated, 'raw_probabilities': raw, 'score_gradient': gradient}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probabilities', required=True)
    parser.add_argument('--mask', required=True)
    parser.add_argument('--outer-loss', type=float, required=True)
    parser.add_argument('--learning-rate', type=float, required=True)
    parser.add_argument('--budget', type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(policy_gradient_update(json.loads(args.probabilities), json.loads(args.mask), args.outer_loss, args.learning_rate, args.budget)))

if __name__ == '__main__':
    main()
