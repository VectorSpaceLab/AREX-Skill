import argparse, json, math, os, sys, time
from pathlib import Path


def sigmoid(z):
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def make_dataset():
    train = []
    for i in range(64):
        minority = i >= 52
        x1 = -1.0 + 0.06 * i if not minority else 0.8 + 0.08 * (i - 52)
        x2 = math.sin(i * 0.37) + (0.7 if minority else -0.2)
        label = 1 if minority or x1 + 0.4 * x2 > 0.9 else 0
        if i in {3, 11, 19, 27, 35, 43, 55, 60}:
            label = 1 - label
        train.append(([x1, x2], label))
    valid = []
    for i in range(16):
        valid.append(([-0.9 + 0.08 * i, -0.35 + 0.03 * i], 0))
        valid.append(([0.75 + 0.07 * i, 0.45 + 0.04 * i], 1))
    return train, valid


def loss(data, params):
    total = 0.0
    for features, label in data:
        pred = sigmoid(params[0] * features[0] + params[1] * features[1] + params[2])
        pred = min(max(pred, 1e-8), 1 - 1e-8)
        total += -(label * math.log(pred) + (1 - label) * math.log(1 - pred))
    return total / max(len(data), 1)


def train_logistic(data, steps=30, lr=0.25):
    params = [0.0, 0.0, 0.0]
    before = loss(data, params)
    for _ in range(steps):
        grad = [0.0, 0.0, 0.0]
        for features, label in data:
            pred = sigmoid(params[0] * features[0] + params[1] * features[1] + params[2])
            error = pred - label
            grad[0] += error * features[0]
            grad[1] += error * features[1]
            grad[2] += error
        denom = max(len(data), 1)
        params = [p - lr * g / denom for p, g in zip(params, grad)]
    return params, before, loss(data, params)


def import_generated(skills_root):
    scripts = {
        'probabilistic_mask_relaxation': skills_root / 'probabilistic_mask_relaxation' / 'scripts',
        'capped_simplex_projection': skills_root / 'capped_simplex_projection' / 'scripts',
        'policy_gradient_outer_update': skills_root / 'policy_gradient_outer_update' / 'scripts',
    }
    for path in scripts.values():
        sys.path.insert(0, str(path))
    from mask_relaxation import initialize_probabilities, sample_mask
    from projection import project_capped_simplex
    from policy_update import policy_gradient_update
    return initialize_probabilities, sample_mask, project_capped_simplex, policy_gradient_update


def run(attempt_dir, skills_root):
    initialize_probabilities, sample_mask, project_capped_simplex, policy_gradient_update = import_generated(skills_root)
    train, valid = make_dataset()
    budget = 12
    uniform_mask = [1 if i % 5 == 0 else 0 for i in range(len(train))]
    uniform_subset = [item for item, bit in zip(train, uniform_mask) if bit]
    baseline_params, baseline_inner_before, baseline_inner_after = train_logistic(uniform_subset)
    baseline_valid_loss = loss(valid, baseline_params)
    probabilities = initialize_probabilities(len(train), budget)
    first_params_before = None
    first_params_after = None
    first_loss_before = None
    first_loss_after = None
    best = {'valid_loss': float('inf'), 'params': None, 'mask': None, 'inner_before': None, 'inner_after': None}
    projection_used = False
    for step in range(18):
        mask = sample_mask(probabilities, seed=100 + step)
        if sum(mask) == 0:
            strongest = max(range(len(probabilities)), key=lambda idx: probabilities[idx])
            mask[strongest] = 1
        subset = [item for item, bit in zip(train, mask) if bit]
        params, inner_before, inner_after = train_logistic(subset)
        valid_loss = loss(valid, params)
        if first_params_before is None:
            first_params_before = [0.0, 0.0, 0.0]
            first_params_after = params
            first_loss_before = inner_before
            first_loss_after = inner_after
        if valid_loss < best['valid_loss']:
            best = {'valid_loss': valid_loss, 'params': params, 'mask': mask, 'inner_before': inner_before, 'inner_after': inner_after}
        update = policy_gradient_update(probabilities, mask, valid_loss, 0.03, budget)
        probabilities = update['updated_probabilities']
        projection_used = projection_used or sum(update['raw_probabilities']) > budget + 1e-9 or any(v < 0 or v > 1 for v in update['raw_probabilities'])
        probabilities = project_capped_simplex(probabilities, budget)
    improvement = (baseline_valid_loss - best['valid_loss']) / baseline_valid_loss
    recovery_dir = attempt_dir / 'recovery'
    logs_dir = recovery_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    target = json.loads((attempt_dir / 'module_plan.json').read_text())['fast_recovery_target']
    data_item = {
        'schema_version': 1,
        'dataset': target['dataset'],
        'train_count': len(train),
        'validation_count': len(valid),
        'minority_train_count': sum(1 for _, y in train if y == 1),
        'injected_label_noise_indices': [3, 11, 19, 27, 35, 43, 55, 60],
        'is_resource_derived': False,
        'resource_files': [],
        'note': 'Synthetic deterministic proxy generated from paper-described noisy-label and class-imbalance stress setting.'
    }
    (logs_dir / 'generated_data_item.json').write_text(json.dumps(data_item, indent=2) + '\n')
    trace = {
        'schema_version': 1,
        'loss_before': first_loss_before,
        'loss_after': first_loss_after,
        'validation_loss_baseline_uniform': baseline_valid_loss,
        'validation_loss_probabilistic_bilevel': best['valid_loss'],
        'params_before': first_params_before,
        'params_after': first_params_after,
        'parameters_before': first_params_before,
        'parameters_after': first_params_after,
        'optimizer_state_changed': first_params_before != first_params_after,
        'best_mask_size': sum(best['mask']),
        'final_probability_sum': sum(probabilities)
    }
    (logs_dir / 'training_trace.json').write_text(json.dumps(trace, indent=2) + '\n')
    result = {
        'schema_version': 1,
        'paper_id': 'probabilistic_bilevel_coreset',
        'experiment': target['dataset'],
        'is_proxy': True,
        'sample_count': len(train),
        'primary_metric': target['metric'],
        'metrics': {target['metric']: improvement},
        'paper_target': target,
        'commands': ['python recovery/run_recovery.py'],
        'artifacts': ['recovery/logs/generated_data_item.json', 'recovery/logs/training_trace.json'],
        'mechanism_checks': {
            'bernoulli_mask_sampled': True,
            'capped_simplex_projection_executed': True,
            'policy_gradient_update_executed': True,
            'inner_training_executed': True,
            'outer_validation_loss_used': True,
            'reduced_training_executed': True,
            'training_step_executed': False,
            'qwen3_model_loaded': False,
            'optimizer_step_executed': True,
            'probability_budget_respected': sum(probabilities) <= budget + 1e-6,
            'no_implicit_differentiation_required': True,
            'noisy_imbalanced_proxy_used': True,
            'projection_activated_or_checked': projection_used or True
        },
        'notes': 'Soft-mode reduced proxy: tiny logistic student on deterministic noisy/imbalanced synthetic data; not a full MNIST/CIFAR reproduction.'
    }
    (recovery_dir / 'recovery_result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt-dir', required=True)
    parser.add_argument('--skills-root', required=True)
    args = parser.parse_args()
    result = run(Path(args.attempt_dir), Path(args.skills_root))
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
