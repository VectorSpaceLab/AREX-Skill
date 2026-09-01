#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def check_gap(target, aggregate_norm, epsilon, baseline_metric, retained_metric, mechanism_checks=None, recovered_target=None):
    mechanism_checks=dict(mechanism_checks or {})
    reasons=[]
    if recovered_target is not None:
        for key in ('dataset','split','metric','paper_value'):
            if target.get(key)!=recovered_target.get(key): reasons.append(f'target mismatch: {key}')
    if not math.isfinite(aggregate_norm) or not math.isfinite(epsilon): reasons.append('non-finite bound inputs')
    influence_ok=aggregate_norm <= epsilon + 1e-12
    if not influence_ok: reasons.append('aggregate influence exceeds epsilon')
    gap=abs(float(baseline_metric)-float(retained_metric))
    required=['influence_vectors_computed','aggregate_optimizer_executed','metric_gap_computed']
    for key in required:
        if not mechanism_checks.get(key): reasons.append(f'missing mechanism check: {key}')
    mechanism_checks.update({'influence_bound_satisfied':influence_ok,'metric_gap_computed':True})
    ok=(not reasons)
    return {'schema_version':1,'ok':ok,'reasons':reasons,'aggregate_norm':aggregate_norm,'epsilon':epsilon,'observed_metric_gap':gap,'target_metric':target.get('metric'),'mechanism_checks':mechanism_checks}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--output'); p.add_argument('--demo', action='store_true')
    a=p.parse_args(); data={'target':{'dataset':'synthetic_binary_classification_proxy','split':'deterministic_8_train_4_eval','metric':'retained_accuracy_gap','paper_value':0.013},'aggregate_norm':0.1,'epsilon':0.2,'baseline_metric':1.0,'retained_metric':1.0,'mechanism_checks':{'influence_vectors_computed':True,'aggregate_optimizer_executed':True,'metric_gap_computed':True}} if a.demo else json.loads(Path(a.input).read_text())
    out=check_gap(**data); text=json.dumps(out, indent=2)
    if a.output: Path(a.output).write_text(text+'\n')
    else: print(text)
if __name__=='__main__': main()
