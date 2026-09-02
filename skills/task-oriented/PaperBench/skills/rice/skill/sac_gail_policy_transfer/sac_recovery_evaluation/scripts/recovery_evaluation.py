#!/usr/bin/env python3
import argparse, json
REQUIRED=['entropy_term_used','replay_batch_used','twin_q_min_used','value_update_executed','q_update_executed','policy_update_executed','polyak_target_update_executed','optimizer_step_executed','reduced_training_executed']

def score_recovery(mechanism_checks, trace=None, invocations=None, forbidden_sources_detected=None):
    trace=trace or {}
    invocations=invocations or []
    forbidden_sources_detected=forbidden_sources_detected or []
    checks={key: bool(mechanism_checks.get(key)) for key in REQUIRED}
    checks['loss_recorded'] = 'loss_before' in trace and 'loss_after' in trace
    checks['params_changed'] = trace.get('params_before') != trace.get('params_after')
    checks['skills_invoked'] = len(invocations) >= 4
    checks['source_boundary_ok'] = not forbidden_sources_detected
    failed=[key for key,value in checks.items() if not value]
    return {'ok': not failed, 'mechanism_pass_rate': (len(checks)-len(failed))/len(checks), 'failed_checks': failed, 'checks': checks}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    data=json.load(open(args.input))
    result=score_recovery(data.get('mechanism_checks',{}), data.get('trace',{}), data.get('invocations',[]), data.get('forbidden_sources_detected',[]))
    json.dump(result, open(args.output,'w'), indent=2)
if __name__=='__main__': main()
