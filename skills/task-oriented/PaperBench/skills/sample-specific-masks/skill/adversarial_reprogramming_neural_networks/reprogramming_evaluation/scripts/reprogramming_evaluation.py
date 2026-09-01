from __future__ import annotations

def evaluate_reprogramming_evidence(result, trace, source_paths=None):
    errors=[]; metrics=result.get('metrics',{})
    if not any(isinstance(v,(int,float)) for v in metrics.values()): errors.append('missing numeric metric')
    checks=result.get('mechanism_checks',{})
    for key in ['universal_program_reused','frozen_model_unchanged','output_remapping_used','optimizer_step_executed']:
        if checks.get(key) is not True: errors.append(f'missing mechanism check {key}')
    if checks.get('reduced_training_executed') is True:
        if 'loss_before' not in trace or 'loss_after' not in trace: errors.append('missing loss trace')
        if trace.get('params_before') == trace.get('params_after'): errors.append('program parameters did not change')
    for p in source_paths or []:
        if 'original_repo' in str(p): errors.append('forbidden original repo path in source manifest')
    return {'ok': not errors, 'errors': errors, 'metrics': metrics, 'mechanism_checks': checks}
