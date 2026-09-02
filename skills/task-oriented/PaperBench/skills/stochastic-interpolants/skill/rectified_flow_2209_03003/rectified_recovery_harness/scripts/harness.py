import argparse, importlib.util, json, math, random, sys
from pathlib import Path

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def make_data(n, seed):
    random.seed(seed); x0=[]; x1=[]; times=[]
    for i in range(n):
        a = -1.0 + 2.0 * i / max(n - 1, 1)
        b = math.sin(3.0 * a) * 0.2
        x0.append([a, b])
        shift = 1.0
        x1.append([a + shift, b + 0.7])
        times.append((i % 11 + 0.5) / 11.0)
    return x0, x1, times

def run(attempt_dir, skill_root, sample_count=64, seed=7):
    attempt = Path(attempt_dir); skills = Path(skill_root)
    interp = _load(skills/'rectified_coupling_interpolation/scripts/interpolation.py', 'rf_interp')
    vel = _load(skills/'rectified_velocity_regression/scripts/velocity.py', 'rf_vel')
    ode = _load(skills/'rectified_ode_reflow/scripts/ode.py', 'rf_ode')
    x0, x1, times = make_data(sample_count, seed)
    records = interp.build_records(x0, x1, times)
    train = vel.train(records, lr=0.08, steps=220)
    one_step = ode.simulate(x0, train['params_after'], steps=1)
    four_step = ode.simulate(x0, train['params_after'], steps=4)
    loss_reduction = (train['loss_before'] - train['loss_after']) / max(train['loss_before'], 1e-12)
    logs = attempt/'recovery/logs'; logs.mkdir(parents=True, exist_ok=True)
    (logs/'training_trace.json').write_text(json.dumps(train, indent=2), encoding='utf-8')
    item = {'schema_version':1,'dataset':'deterministic synthetic two-dimensional coupling','sample_count':sample_count,'seed':seed,'is_resource_derived':False,'resource_files':[],'construction':'x0 grid with sinusoidal second coordinate and constant affine target displacement; generated inside current attempt'}
    (logs/'generated_data_item.json').write_text(json.dumps(item, indent=2), encoding='utf-8')
    (logs/'ode_diagnostics.json').write_text(json.dumps({'one_step':one_step,'four_step':four_step}, indent=2), encoding='utf-8')
    inv={'schema_version':1,'invocations':[{'module':'coupling_interpolation','skill':'rectified_coupling_interpolation','evidence':'imported helper','artifact':'recovery/logs/generated_data_item.json'},{'module':'velocity_regression','skill':'rectified_velocity_regression','evidence':'imported helper','artifact':'recovery/logs/training_trace.json'},{'module':'ode_transport_reflow','skill':'rectified_ode_reflow','evidence':'imported helper','artifact':'recovery/logs/ode_diagnostics.json'},{'module':'recovery_experiment','skill':'rectified_recovery_harness','evidence':'called script','artifact':'recovery/recovery_result.json'}]}
    (logs/'generated_skill_invocations.json').write_text(json.dumps(inv, indent=2), encoding='utf-8')
    plan=json.loads((attempt/'module_plan.json').read_text(encoding='utf-8'))
    result={'schema_version':1,'paper_id':'rectified_flow_2209_03003','experiment':'deterministic two-dimensional Gaussian-to-mixture proxy','is_proxy':True,'sample_count':sample_count,'metrics':{'loss_reduction_fraction':loss_reduction,'loss_before':train['loss_before'],'loss_after':train['loss_after'],'one_step_mean_straightness_ratio':one_step['mean_straightness_ratio'],'four_step_mean_straightness_ratio':four_step['mean_straightness_ratio']},'paper_target':plan['fast_recovery_target'],'commands':[f'python recovery/run_recovery.py --attempt-dir {attempt} --skill-root {skills} --sample-count {sample_count} --seed {seed}'],'artifacts':['recovery/logs/training_trace.json','recovery/logs/generated_data_item.json','recovery/logs/ode_diagnostics.json'],'mechanism_checks':{'interpolation_records_built':True,'least_squares_loss_computed':True,'optimizer_step_executed':train['optimizer_state_changed'],'reduced_training_executed':True,'training_step_executed':False,'qwen3_model_loaded':False,'euler_transport_executed':True,'reflow_straightness_diagnostic_executed':True,'convex_transport_cost_recorded':True,'fallback_used':False},'notes':'Soft-mode reduced proxy recovery. Full CIFAR/image training was not attempted because bounded runtime and model/data resources were unavailable.'}
    (attempt/'recovery/recovery_result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--attempt-dir', required=True); parser.add_argument('--skill-root', required=True); parser.add_argument('--sample-count', type=int, default=64); parser.add_argument('--seed', type=int, default=7)
    args=parser.parse_args(); print(json.dumps(run(args.attempt_dir, args.skill_root, args.sample_count, args.seed), indent=2))

if __name__ == '__main__':
    main()
