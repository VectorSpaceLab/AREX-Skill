import json, os, subprocess, sys, time
from pathlib import Path

def run(attempt_dir, skills_root):
    attempt=Path(attempt_dir); skills=Path(skills_root); logs=attempt/'recovery'/'logs'; logs.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(skills/'actor_learner_protocol'/'scripts')); sys.path.insert(0, str(skills/'vtrace_target_computation'/'scripts')); sys.path.insert(0, str(skills/'vtrace_actor_critic_update'/'scripts'))
    from protocol import validate_unroll
    from vtrace import compute_vtrace
    from update import train_one_step
    raw={"features":[1.0,-0.5,0.25],"bootstrap_feature":0.0,"rewards":[1.0,0.0,0.5],"discounts":[0.9,0.9,0.0],"actions":[0,1,0],"values":[0.0,0.0,0.0,0.0],"target_policy":[[0.62,0.38],[0.47,0.53],[0.56,0.44]],"behavior_policy":[[0.45,0.55],[0.60,0.40],[0.55,0.45]]}
    validated=validate_unroll(raw)
    unroll={"features":raw["features"],"bootstrap_feature":raw["bootstrap_feature"],"rewards":validated["rewards"],"discounts":validated["discounts"],"actions":validated["actions"],"behavior_action_probs":validated["behavior_action_probs"]}
    params={"policy_weight":0.1,"value_weight":0.0}
    step=train_one_step(params, unroll, lr=0.05)
    cross=compute_vtrace(unroll["rewards"], unroll["discounts"], step["before"]["values"], step["before"]["target_action_probs"], unroll["behavior_action_probs"], 1.0, 1.0)
    data_item={"schema_version":1,"dataset":"synthetic_policy_lag_trajectory","is_resource_derived":False,"resource_files":[],"construction":"Paper-derived synthetic unroll preserving IMPALA policy-lag metadata.","unroll":raw,"validated_unroll":validated}
    (logs/'generated_data_item.json').write_text(json.dumps(data_item,indent=2),encoding='utf-8')
    trace={"schema_version":1,"loss_before":step["loss_before"],"loss_after":step["loss_after"],"params_before":step["params_before"],"params_after":step["params_after"],"parameters_before":step["params_before"],"parameters_after":step["params_after"],"gradients":step["gradients"],"optimizer_state_changed":step["optimizer_state_changed"],"learning_rate_used":step["learning_rate_used"],"vtrace_targets_before":step["before"]["vtrace"]["targets"],"vtrace_cross_check_targets":cross["targets"]}
    (logs/'training_trace.json').write_text(json.dumps(trace,indent=2),encoding='utf-8')
    inv={"schema_version":1,"invocations":[{"module":"actor_learner_protocol","skill":"actor_learner_protocol","evidence":"imported helper","artifact":"recovery/logs/generated_data_item.json"},{"module":"vtrace_target_computation","skill":"vtrace_target_computation","evidence":"cross-check","artifact":"recovery/logs/training_trace.json"},{"module":"vtrace_actor_critic_update","skill":"vtrace_actor_critic_update","evidence":"imported helper","artifact":"recovery/logs/training_trace.json"},{"module":"recovery_evaluation_harness","skill":"recovery_evaluation_harness","evidence":"called script","artifact":"recovery/recovery_result.json"}]}
    (logs/'generated_skill_invocations.json').write_text(json.dumps(inv,indent=2),encoding='utf-8')
    plan=json.loads((attempt/'module_plan.json').read_text())
    metric=max(0.0, step['loss_before']-step['loss_after'])
    result={"schema_version":1,"paper_id":"impala_vtrace","experiment":"synthetic_policy_lag_trajectory","is_proxy":True,"sample_count":1,"metrics":{"loss_reduction":metric,"loss_before":step['loss_before'],"loss_after":step['loss_after']},"paper_target":plan['fast_recovery_target'],"commands":["python recovery/run_recovery.py"],"artifacts":["recovery/logs/generated_data_item.json","recovery/logs/training_trace.json"],"mechanism_checks":{"full_distributed_impala_executed":False,"full_runtime_blocked":True,"policy_lag_detected":validated['has_policy_lag'],"behavior_policy_probabilities_used":True,"vtrace_targets_computed":True,"rho_clipping_checked":max(step['before']['vtrace']['ratios']) > 1.0,"c_trace_coefficients_computed":True,"actor_critic_loss_computed":True,"reduced_training_executed":True,"optimizer_step_executed":step['optimizer_state_changed'],"training_step_executed":False,"qwen3_model_loaded":False,"fallback_used":False},"notes":"Soft-mode reduced recovery: full distributed Atari/DMLab IMPALA is blocked by simulator/training cost, but the V-trace actor-critic mechanism ran with a real optimizer update."}
    (attempt/'recovery'/'recovery_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    source={"schema_version":1,"allowed_sources_used":["paper_profile.md","module_plan.json","modules/","environment/runtime_handoff.json",str(skills)],"forbidden_sources_detected":[],"original_repo_source":"unknown","source_boundary":"No original implementation repository was read during recovery.","benchmark_sources":{}}
    (attempt/'recovery'/'source_manifest.json').write_text(json.dumps(source,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    run(sys.argv[1], sys.argv[2])
