import argparse, json, math, sys
from pathlib import Path


def build_records():
    records = []
    for i in range(40):
        label = 0 if i < 20 else 1
        score_pos = i / 39
        target_prob = 0.52 + 0.42 * score_pos
        if label == 0:
            probs = [target_prob, 1 - target_prob]
        else:
            probs = [1 - target_prob, target_prob]
        if i in {0, 1, 2, 3}:
            probs = [0.35, 0.65] if label == 0 else [0.65, 0.35]
        records.append({'index': i, 'epoch': 0, 'label': label, 'probabilities': probs})
        records.append({'index': i, 'epoch': 1, 'label': label, 'probabilities': probs})
    return records


def represented_fraction(selected, scores, strata):
    lo, hi = min(scores), max(scores)
    width = (hi - lo) / strata if hi > lo else 1
    bins = set()
    for idx in selected:
        bins.add(min(strata - 1, int((scores[idx] - lo) / width)) if hi > lo else 0)
    return len(bins) / strata, sorted(bins)


def optimizer_step(selected, labels):
    weight, bias, lr = 0.0, 0.0, 0.4
    def loss_for(w, b):
        total = 0.0
        for i in selected:
            x = (i - 19.5) / 20.0
            y = labels[i]
            pred = 1 / (1 + math.exp(-(w * x + b)))
            total += -(y * math.log(pred + 1e-9) + (1-y) * math.log(1-pred + 1e-9))
        return total / len(selected)
    before = loss_for(weight, bias)
    grad_w = grad_b = 0.0
    for i in selected:
        x = (i - 19.5) / 20.0
        y = labels[i]
        pred = 1 / (1 + math.exp(-(weight * x + bias)))
        grad_w += (pred - y) * x
        grad_b += pred - y
    grad_w /= len(selected)
    grad_b /= len(selected)
    new_weight = weight - lr * grad_w
    new_bias = bias - lr * grad_b
    after = loss_for(new_weight, new_bias)
    return {
        'loss_before': before,
        'loss_after': after,
        'params_before': {'weight': weight, 'bias': bias},
        'params_after': {'weight': new_weight, 'bias': new_bias},
        'optimizer_state_changed': True,
        'selected_indices': selected,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt-dir', required=True)
    parser.add_argument('--skills-root', required=True)
    parser.add_argument('--output', default='')
    args = parser.parse_args()
    attempt = Path(args.attempt_dir).resolve()
    skills = Path(args.skills_root).resolve()
    sys.path.insert(0, str(skills/'training_dynamics_scoring'/'scripts'))
    sys.path.insert(0, str(skills/'coverage_stratified_selection'/'scripts'))
    from score_training_dynamics import compute_scores
    from select_coreset import monotonic_selection, select_coverage_coreset
    recovery = attempt/'recovery'
    logs = recovery/'logs'
    logs.mkdir(parents=True, exist_ok=True)
    target = json.loads((attempt/'module_plan.json').read_text())['fast_recovery_target']
    records = build_records()
    score_table = compute_scores(records, num_classes=2, max_el2n_epoch=2)
    (logs/'score_table.json').write_text(json.dumps(score_table, indent=2), encoding='utf-8')
    ccs = select_coverage_coreset(score_table, 'accumulated_margin', 0.1, 0.1, 8, 7)
    mono = monotonic_selection(score_table, 'accumulated_margin', 0.1, descending=True)
    ccs_fraction, ccs_bins = represented_fraction(ccs['selected_indices'], score_table['accumulated_margin'], 8)
    mono_fraction, mono_bins = represented_fraction(mono, score_table['accumulated_margin'], 8)
    gain = ccs_fraction - mono_fraction
    trace = optimizer_step(ccs['selected_indices'], score_table['targets'])
    (logs/'training_trace.json').write_text(json.dumps(trace, indent=2), encoding='utf-8')
    data_item = {
        'schema_version': 1,
        'dataset': target['dataset'],
        'sample_count': 40,
        'is_resource_derived': False,
        'resource_files': [],
        'note': 'Deterministic synthetic proxy because full CIFAR/ImageNet data and long GPU training are blocked for bounded recovery.',
        'score_bins': 8,
        'records_path': 'recovery/logs/score_table.json'
    }
    (logs/'generated_data_item.json').write_text(json.dumps(data_item, indent=2), encoding='utf-8')
    mechanism_checks = {
        'proxy_declared': True,
        'full_cifar_training_blocked': True,
        'qwen3_model_loaded': False,
        'training_step_executed': False,
        'reduced_training_executed': True,
        'optimizer_step_executed': trace['params_before'] != trace['params_after'],
        'training_dynamics_scores_computed': True,
        'mislabel_filter_executed': len(ccs['removed_indices']) > 0,
        'stratified_sampling_executed': len(ccs['represented_bins']) > 1,
        'coverage_gain_positive': gain > 0,
        'score_bins_ccs': ccs_bins,
        'score_bins_monotonic': mono_bins,
        'loss_decreased': trace['loss_after'] < trace['loss_before']
    }
    result = {
        'schema_version': 1,
        'paper_id': 'coverage_centric_coreset',
        'experiment': target['dataset'],
        'is_proxy': True,
        'sample_count': 40,
        'metrics': {'coverage_gain_over_monotonic': gain, 'ccs_bin_fraction': ccs_fraction, 'monotonic_bin_fraction': mono_fraction, 'loss_delta': trace['loss_before'] - trace['loss_after']},
        'paper_target': {'dataset': target['dataset'], 'split': target['split'], 'metric': target['metric'], 'value': target['paper_value'], 'proxy': target['proxy']},
        'commands': [],
        'artifacts': ['recovery/logs/generated_data_item.json', 'recovery/logs/training_trace.json', 'recovery/logs/score_table.json'],
        'mechanism_checks': mechanism_checks,
        'notes': 'Soft-mode reduced proxy validates CCS score coverage and optimizer execution, not full CIFAR10 accuracy.'
    }
    out = Path(args.output) if args.output else recovery/'recovery_result.json'
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'output': str(out), 'coverage_gain_over_monotonic': gain, 'loss_delta': result['metrics']['loss_delta']}, indent=2))

if __name__ == '__main__':
    main()
