import argparse, json, math

def kl_beta_target(behavior_dist, target_dist, eps=1e-12):
    if len(behavior_dist) != len(target_dist) or not behavior_dist:
        raise ValueError('distributions must be non-empty and equal length')
    total = 0.0
    for b, t in zip(behavior_dist, target_dist):
        b = max(float(b), eps); t = max(float(t), eps)
        total += b * math.log(b / t)
    return total

def p3o_components(on_adv, on_score, off_adv, off_score, ratios, clip_threshold, kl_coefficient, behavior_dist, target_dist):
    if len(on_adv) != len(on_score) or len(off_adv) != len(off_score) or len(off_adv) != len(ratios):
        raise ValueError('component vector lengths do not match')
    on = sum(float(a)*float(s) for a, s in zip(on_adv, on_score)) / max(1, len(on_adv))
    clipped = [min(float(r), float(clip_threshold)) for r in ratios]
    off = sum(c*float(a)*float(s) for c, a, s in zip(clipped, off_adv, off_score)) / max(1, len(off_adv))
    kl = kl_beta_target(behavior_dist, target_dist)
    objective = on + off - float(kl_coefficient) * kl
    return {'on_policy': on, 'off_policy': off, 'kl_penalty': kl, 'objective': objective, 'clipped_ratios': clipped}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    out = p3o_components([1.0], [0.2], [1.0], [0.3], [2.0], 0.5, 0.2, [0.5,0.5], [0.6,0.4])
    if a.self_test:
        assert out['clipped_ratios'] == [0.5]
        assert out['kl_penalty'] >= 0.0
        assert abs(out['objective'] - (out['on_policy'] + out['off_policy'] - 0.2*out['kl_penalty'])) < 1e-12
    print(json.dumps(out, indent=2))
if __name__ == '__main__': main()
