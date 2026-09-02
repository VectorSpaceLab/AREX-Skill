#!/usr/bin/env python3
import argparse, json

REQUIRED = [
    'posterior_computed', 'weighted_posterior_applied', 'rho_filter_applied',
    'guided_token_selected', 'hybrid_loss_computed', 'optimizer_step_executed',
    'multiclass_true_false_pairs_built', 'source_boundary_respected'
]

def summarize(result):
    checks = result.get('mechanism_checks', {})
    passed = [k for k in REQUIRED if checks.get(k) is True]
    return {'required_checks': REQUIRED, 'passed_checks': passed, 'mechanism_pass_rate': len(passed)/len(REQUIRED), 'ok': len(passed)==len(REQUIRED)}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--output', required=True)
    args = ap.parse_args(); out = summarize(json.load(open(args.result)))
    json.dump(out, open(args.output,'w'), indent=2, sort_keys=True)
