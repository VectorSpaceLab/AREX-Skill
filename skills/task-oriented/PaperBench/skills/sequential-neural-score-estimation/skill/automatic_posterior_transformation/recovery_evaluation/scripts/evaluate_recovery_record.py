#!/usr/bin/env python3
import argparse, json
REQUIRED=['proposal_correction_applied','atomic_loss_computed','sequential_proposal_updated','generated_skills_exercised','reduced_training_executed','optimizer_step_executed']

def invocation_coverage(invocation_log, required_modules):
    seen = {item.get('module') or item.get('skill') for item in invocation_log.get('invocations', [])}
    return {'covered': sorted(set(required_modules) & seen), 'missing': sorted(set(required_modules) - seen), 'ok': set(required_modules).issubset(seen)}

def source_boundary_ok(source_manifest):
    return source_manifest.get('original_repo_used') is False and 'repo' not in ' '.join(source_manifest.get('allowed_sources_used', [])).lower()

def evaluate(record, validation):
    checks={}
    checks['gate_ok']=validation.get('ok') is True
    metric=record.get('paper_target',{}).get('metric')
    checks['numeric_metric']=isinstance(record.get('metrics',{}).get(metric), (int,float))
    mech=record.get('mechanism_checks',{})
    for key in REQUIRED: checks[key]=mech.get(key) is True
    status='accept' if all(checks.values()) else 'refine'
    return {'status':status,'checks':checks,'missing':[k for k,v in checks.items() if not v]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--record'); ap.add_argument('--validation'); ap.add_argument('--self-test', action='store_true'); ns=ap.parse_args()
    if ns.self_test:
        rec={'metrics':{'posterior_mean_abs_error':0.1},'paper_target':{'metric':'posterior_mean_abs_error'},'mechanism_checks':{k:True for k in REQUIRED}}
        out=evaluate(rec, {'ok':True}); assert out['status']=='accept'; print(json.dumps(out,indent=2)); return
    print(json.dumps(evaluate(json.load(open(ns.record)), json.load(open(ns.validation))), indent=2))
if __name__ == '__main__': main()
