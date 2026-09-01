#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
REQUIRED_CHECKS=['ot_path_samples_built','cfm_target_vector_computed','cfm_loss_computed','optimizer_step_executed','params_changed','ode_sampler_checked']
def evaluate_proxy(result,threshold=.25):
    failures=[]
    if not result.get('is_proxy'): failures.append('recovery must be explicitly marked as proxy')
    dec=result.get('metrics',{}).get('cfm_loss_relative_decrease')
    if not isinstance(dec,(int,float)): failures.append('missing numeric cfm_loss_relative_decrease')
    elif dec<threshold: failures.append(f'relative loss decrease {dec:.6f} is below threshold {threshold:.6f}')
    checks=result.get('mechanism_checks',{})
    for key in REQUIRED_CHECKS:
        if checks.get(key) is not True: failures.append(f'missing or false mechanism check: {key}')
    exercised={i.get('module_id') for i in result.get('generated_skill_invocations',[]) if i.get('evidence_type') in {'called script','imported helper','cross-check'}}
    for req in ['conditional_path_builder','cfm_training_objective','ode_sampler_checker','proxy_recovery_evaluator']:
        if req not in exercised: failures.append(f'generated skill not exercised: {req}')
    return {'ok':not failures,'failures':failures,'threshold':threshold,'observed_relative_loss_decrease':dec}
def main():
    p=argparse.ArgumentParser(); p.add_argument('result_json'); p.add_argument('--threshold',type=float,default=.25); p.add_argument('--output',required=True); a=p.parse_args(); ev=evaluate_proxy(json.loads(Path(a.result_json).read_text()),a.threshold); Path(a.output).write_text(json.dumps(ev,indent=2)); print(json.dumps(ev,indent=2)); return 0 if ev['ok'] else 2
if __name__=='__main__': raise SystemExit(main())
