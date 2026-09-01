import argparse, json, math

def compute_ess_schedule(target_probs, behavior_probs, eps=1e-12):
    if len(target_probs) != len(behavior_probs) or not target_probs:
        raise ValueError('target_probs and behavior_probs must be non-empty and equal length')
    ratios = [max(float(t), eps) / max(float(b), eps) for t, b in zip(target_probs, behavior_probs)]
    sum_r = sum(ratios)
    sum_r2 = sum(r*r for r in ratios)
    ess = 0.0 if sum_r2 == 0 else (sum_r * sum_r) / (len(ratios) * sum_r2)
    ess = max(0.0, min(1.0, ess))
    return {'importance_ratios': ratios, 'ess': ess, 'clip_threshold': ess, 'kl_coefficient': 1.0 - ess}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--target', default='[0.6,0.4]')
    p.add_argument('--behavior', default='[0.5,0.5]')
    p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    if a.self_test:
        out = compute_ess_schedule([0.5,0.5], [0.5,0.5])
        assert abs(out['ess'] - 1.0) < 1e-12
        out2 = compute_ess_schedule([0.9,0.1], [0.5,0.5])
        assert 0.0 <= out2['ess'] <= 1.0 and abs(out2['clip_threshold'] + out2['kl_coefficient'] - 1.0) < 1e-12
    print(json.dumps(compute_ess_schedule(json.loads(a.target), json.loads(a.behavior)), indent=2))
if __name__ == '__main__': main()
