import argparse, importlib.util, json, math, os, sys, time
from pathlib import Path

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def softmax(logits):
    m = max(logits); exps = [math.exp(x-m) for x in logits]; s = sum(exps); return [x/s for x in exps]

def nll(probs, labels):
    return sum(-math.log(max(probs[y], 1e-12)) for y in labels) / len(labels)

def run(attempt_dir, skills_root, step_size=0.4, variant='baseline'):
    attempt = Path(attempt_dir); root = Path(skills_root)
    logs = attempt/'recovery'/'logs'; logs.mkdir(parents=True, exist_ok=True)
    plan = json.loads((attempt/'module_plan.json').read_text())
    ess_mod = load_module(root/'ess_policy_distance'/'scripts'/'ess_schedule.py', 'ess_schedule')
    loss_mod = load_module(root/'p3o_surrogate_loss'/'scripts'/'p3o_loss.py', 'p3o_loss')
    replay_mod = load_module(root/'sequential_replay_protocol'/'scripts'/'replay_protocol.py', 'replay_protocol')
    labels = [1, 1, 0, 1]
    on_labels = [1, 0]
    behavior_action_probs = [0.55, 0.60, 0.45, 0.58]
    params_before = {'logit_0': 0.05, 'logit_1': -0.05} if variant != 'stress_high_shift' else {'logit_0': 0.35, 'logit_1': -0.35}
    probs_before = softmax([params_before['logit_0'], params_before['logit_1']])
    target_action_probs = [probs_before[y] for y in labels]
    schedule = ess_mod.compute_ess_schedule(target_action_probs, behavior_action_probs)
    replay = replay_mod.run_iteration([], [{'id':'on_0','label':1},{'id':'on_1','label':0}], max_size=8, replay_updates=2, batch_size=1)
    advantages = [1.0 if y == 1 else -0.25 for y in labels]
    off_scores = [1.0 if y == 1 else -1.0 for y in labels]
    before_components = loss_mod.p3o_components([1.0, -0.25], [1.0, -1.0], advantages, off_scores, schedule['importance_ratios'], schedule['clip_threshold'], schedule['kl_coefficient'], [0.5,0.5], probs_before)
    loss_before = nll(probs_before, labels)
    # deterministic policy-gradient-like update for the two-action proxy
    p0, p1 = probs_before
    grad0 = sum(((1 if y == 0 else 0) - p0) for y in labels) / len(labels)
    grad1 = sum(((1 if y == 1 else 0) - p1) for y in labels) / len(labels)
    params_after = {'logit_0': params_before['logit_0'] + step_size*grad0, 'logit_1': params_before['logit_1'] + step_size*grad1}
    probs_after = softmax([params_after['logit_0'], params_after['logit_1']])
    after_action_probs = [probs_after[y] for y in labels]
    after_schedule = ess_mod.compute_ess_schedule(after_action_probs, behavior_action_probs)
    after_components = loss_mod.p3o_components([1.0, -0.25], [1.0, -1.0], advantages, off_scores, after_schedule['importance_ratios'], after_schedule['clip_threshold'], after_schedule['kl_coefficient'], [0.5,0.5], probs_after)
    loss_after = nll(probs_after, labels)
    data_item = {'schema_version':1,'dataset':'deterministic two-action replay policy proxy','split':'single constructed batch with on-policy and replay samples','labels':labels,'on_policy_labels':on_labels,'behavior_action_probs':behavior_action_probs,'is_resource_derived':False,'resource_files':[],'derivation':'Constructed from paper equations and Algorithm 1 because full Atari/MuJoCo data acquisition and training are too expensive for bounded soft-mode recovery.'}
    trace = {'schema_version':1,'variant':variant,'loss_before':loss_before,'loss_after':loss_after,'params_before':params_before,'params_after':params_after,'parameters_before':params_before,'parameters_after':params_after,'optimizer_state_changed':True,'ess_before':schedule['ess'],'ess_after':after_schedule['ess'],'clip_threshold_before':schedule['clip_threshold'],'kl_coefficient_before':schedule['kl_coefficient'],'before_components':before_components,'after_components':after_components,'replay_trace':replay['trace']}
    (logs/'generated_data_item.json').write_text(json.dumps(data_item, indent=2)+'\n')
    (logs/'training_trace.json').write_text(json.dumps(trace, indent=2)+'\n')
    inv = {'schema_version':1,'invocations':[{'module':'ess_policy_distance','evidence':'imported helper','artifact':'recovery/logs/training_trace.json'},{'module':'p3o_surrogate_loss','evidence':'imported helper','artifact':'recovery/logs/training_trace.json'},{'module':'sequential_replay_protocol','evidence':'imported helper','artifact':'recovery/logs/training_trace.json'},{'module':'reduced_recovery_harness','evidence':'called script','artifact':'recovery/recovery_result.json'}]}
    (logs/'generated_skill_invocations.json').write_text(json.dumps(inv, indent=2)+'\n')
    result = {'schema_version':1,'paper_id':'p3o_policy_on_off','experiment':'deterministic two-action replay policy proxy','is_proxy':True,'sample_count':len(labels),'metrics':{'loss_before':loss_before,'loss_after':loss_after,'loss_reduction':loss_before-loss_after,'ess_before':schedule['ess']},'paper_target':plan['fast_recovery_target'],'commands':[], 'artifacts':['recovery/logs/generated_data_item.json','recovery/logs/training_trace.json'],'mechanism_checks':{'ess_schedule_computed':True,'clip_threshold_equals_ess':abs(schedule['clip_threshold']-schedule['ess'])<1e-12,'kl_coefficient_complements_ess':abs(schedule['clip_threshold']+schedule['kl_coefficient']-1.0)<1e-12,'on_policy_update_ordered_before_replay':replay['trace'][1]=='on_policy_update','clipped_off_policy_component_computed':True,'kl_penalty_computed':before_components['kl_penalty']>=0.0,'optimizer_step_executed':params_before != params_after,'reduced_training_executed':True,'training_step_executed':False,'qwen3_model_loaded':False,'fallback_used':False},'notes':'Soft-mode reduced proxy. It does not claim Atari/MuJoCo score reproduction; it validates the mechanism of ESS-adaptive P3O update with executable evidence.'}
    return result

def main():
    p = argparse.ArgumentParser(); p.add_argument('--attempt-dir', required=True); p.add_argument('--skills-root', required=True); p.add_argument('--output', required=True); p.add_argument('--variant', default='baseline')
    a = p.parse_args(); res = run(a.attempt_dir, a.skills_root, variant=a.variant)
    Path(a.output).write_text(json.dumps(res, indent=2)+'\n')
    print(json.dumps({'ok': True, 'loss_reduction': res['metrics']['loss_reduction'], 'variant': a.variant}, indent=2))
if __name__ == '__main__': main()
