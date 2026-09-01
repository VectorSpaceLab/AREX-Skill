#!/usr/bin/env python3
import argparse, json, math

def _check_time(t):
    if not 0.0 <= t <= 1.0:
        raise ValueError('time must be in [0, 1]')

def ve_sigma(t, sigma_min=0.01, sigma_max=50.0):
    _check_time(float(t))
    if sigma_min <= 0 or sigma_max <= sigma_min:
        raise ValueError('require 0 < sigma_min < sigma_max')
    return sigma_min * (sigma_max / sigma_min) ** float(t)

def ve_diffusion(t, sigma_min=0.01, sigma_max=50.0):
    sigma = ve_sigma(t, sigma_min, sigma_max)
    return sigma * math.sqrt(2.0 * math.log(sigma_max / sigma_min))

def perturb_ve(x0, t, noise, sigma_min=0.01, sigma_max=50.0):
    sigma = ve_sigma(t, sigma_min, sigma_max)
    xt = x0 + sigma * noise
    target_score = -noise / sigma
    return {'x0': x0, 't': t, 'noise': noise, 'sigma': sigma, 'xt': xt, 'target_score': target_score}

def reverse_score_drift(t, score, sigma_min=0.01, sigma_max=50.0):
    g = ve_diffusion(t, sigma_min, sigma_max)
    return -(g * g) * score

def probability_flow_score_drift(t, score, sigma_min=0.01, sigma_max=50.0):
    return 0.5 * reverse_score_drift(t, score, sigma_min, sigma_max)

def self_test():
    assert abs(ve_sigma(0.0) - 0.01) < 1e-12
    assert abs(ve_sigma(1.0) - 50.0) < 1e-9
    score = -0.3
    assert abs(probability_flow_score_drift(0.4, score) * 2.0 - reverse_score_drift(0.4, score)) < 1e-9
    item = perturb_ve(2.0, 0.5, 0.25)
    assert item['target_score'] < 0
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--t', type=float, default=0.5)
    parser.add_argument('--x0', type=float, default=0.0)
    parser.add_argument('--noise', type=float, default=1.0)
    args = parser.parse_args()
    if args.self_test:
        self_test(); print(json.dumps({'ok': True})); return
    print(json.dumps(perturb_ve(args.x0, args.t, args.noise), indent=2))
if __name__ == '__main__': main()
