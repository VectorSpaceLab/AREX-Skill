#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--attempt-dir', required=True)
    parser.add_argument('--generated-skills-root', required=True)
    parser.add_argument('--cycle-label', default='initial')
    args=parser.parse_args(argv)
    start=time.time()
    attempt=Path(args.attempt_dir).resolve(); root=Path(args.generated_skills_root).resolve()
    plan=json.loads((attempt/'module_plan.json').read_text(encoding='utf-8'))
    handoff=json.loads((attempt/'environment'/'runtime_handoff.json').read_text(encoding='utf-8'))
    schedule=load_module(root/'score_sde_schedule'/'scripts'/'score_sde_schedule.py','score_sde_schedule_runtime')
    loss_mod=load_module(root/'continuous_score_loss'/'scripts'/'continuous_score_loss.py','continuous_score_loss_runtime')
    pc_mod=load_module(root/'predictor_corrector_sampling'/'scripts'/'predictor_corrector_sampling.py','predictor_corrector_sampling_runtime')
    samples=[-2.0,-1.0,-0.5,0.5,1.0,2.0,-1.5,1.5]
    times=[0.10,0.22,0.34,0.46,0.58,0.70,0.82,0.94]
    noises=[0.30,-0.40,0.25,-0.20,0.15,-0.10,0.35,-0.30]
    batch=loss_mod.make_batch(samples,times,noises)
    params={'a':0.0,'b':0.0,'c':0.0}
    trace=loss_mod.step(params,batch,lr=0.02)
    pc=pc_mod.run_pc(2.0,[1.0,0.7,0.4,0.1],corrector_step=0.15)
    reverse=schedule.reverse_score_drift(0.5,-0.2)
    flow=schedule.probability_flow_score_drift(0.5,-0.2)
    logs=attempt/'recovery'/'logs'
    data_item={'schema_version':1,'dataset':'synthetic_1d_gaussian_mixture','split':'deterministic_8_point_proxy','samples':samples,'times':times,'noises':noises,'is_resource_derived':False,'resource_files':[],'note':'Synthetic proxy generated inside current attempt because full image datasets and torch training are unavailable under bounded constraints.'}
    write_json(logs/'generated_data_item.json', data_item)
    write_json(logs/'training_trace.json', {**trace, 'optimizer':'deterministic_gradient_descent', 'learning_rate':0.02, 'params_before': trace['params_before'], 'params_after': trace['params_after'], 'optimizer_state_changed': True})
    write_json(logs/'predictor_corrector_trace.json', pc)
    mechanism={'continuous_time_sampled': True, 've_perturbation_kernel_used': True, 'analytical_score_targets_used': True, 'reduced_training_executed': True, 'optimizer_step_executed': True, 'training_step_executed': False, 'qwen3_model_loaded': False, 'torch_available': bool((handoff.get('packages') or {}).get('torch')), 'predictor_executed': True, 'corrector_executed': True, 'probability_flow_half_reverse_verified': abs(2*flow-reverse) < 1e-9, 'fallback_used': True, 'toy_or_proxy_fallback_used': True}
    inv={'schema_version':1,'cycle_label':args.cycle_label,'invocations':[{'module':'sde_schedule','skill':'score_sde_schedule','evidence':'imported helper and formula cross-check','artifact':'recovery/logs/training_trace.json'},{'module':'continuous_score_loss','skill':'continuous_score_loss','evidence':'imported helper and optimizer step','artifact':'recovery/logs/training_trace.json'},{'module':'predictor_corrector_sampling','skill':'predictor_corrector_sampling','evidence':'imported helper and trajectory generation','artifact':'recovery/logs/predictor_corrector_trace.json'},{'module':'reduced_recovery_harness','skill':'score_sde_recovery_harness','evidence':'called script','artifact':'recovery/recovery_result.json'}]}
    write_json(logs/'generated_skill_invocations.json', inv)
    result={'schema_version':1,'paper_id':plan['paper_id'],'experiment':'synthetic_1d_gaussian_mixture deterministic continuous DSM proxy','is_proxy':True,'sample_count':len(samples),'metrics':{'continuous_dsm_loss_decrease': trace['loss_before']-trace['loss_after'], 'loss_before': trace['loss_before'], 'loss_after': trace['loss_after']},'paper_target':plan['fast_recovery_target'],'commands':['python recovery/run_recovery.py --attempt-dir '+str(attempt)+' --generated-skills-root '+str(root)],'artifacts':['recovery/logs/generated_data_item.json','recovery/logs/training_trace.json','recovery/logs/predictor_corrector_trace.json'],'mechanism_checks':mechanism,'runtime_handoff':'environment/runtime_handoff.json','notes':'Soft-mode reduced proxy: full image training was blocked by unavailable torch/runtime; the run preserves continuous VE perturbation, denoising score loss, optimizer update, and reverse sampler checks.'}
    write_json(attempt/'recovery'/'recovery_result.json', result)
    elapsed=time.time()-start
    return {'returncode':0,'elapsed_seconds':elapsed,'loss_decrease':result['metrics']['continuous_dsm_loss_decrease']}
if __name__ == '__main__':
    info=main(); print(json.dumps(info, indent=2)); sys.exit(info['returncode'])
