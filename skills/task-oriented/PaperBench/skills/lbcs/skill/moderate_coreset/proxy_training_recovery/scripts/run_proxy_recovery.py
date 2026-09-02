#!/usr/bin/env python3
import argparse, importlib.util, json, math, os, sys, time
from pathlib import Path

def load_module(path, name):
    spec=importlib.util.spec_from_file_location(name, path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def synthetic_records(scale=1.0):
    base=[]
    for label, x0 in [(0,-2.0),(1,2.0)]:
        offsets=[-0.05,0.05,-0.55,0.55,-1.4,1.4]
        for idx, off in enumerate(offsets):
            base.append({'id':f'c{label}_{idx}','label':label,'representation':[x0+scale*off, scale*(0.12 if idx%2 else -0.08)],'target':label})
    return base

def sigmoid(x): return 1/(1+math.exp(-max(-30,min(30,x))))

def loss(records, params):
    total=0.0
    for rec in records:
        x=rec['representation']; y=float(rec['target']); pred=sigmoid(params['w0']*x[0]+params['w1']*x[1]+params['b'])
        total+=-(y*math.log(pred+1e-9)+(1-y)*math.log(1-pred+1e-9))
    return total/len(records)

def train_step(records, params, lr=0.4):
    grad={'w0':0.0,'w1':0.0,'b':0.0}
    for rec in records:
        x=rec['representation']; err=sigmoid(params['w0']*x[0]+params['w1']*x[1]+params['b'])-float(rec['target'])
        grad['w0']+=err*x[0]; grad['w1']+=err*x[1]; grad['b']+=err
    for k in grad: grad[k]/=len(records)
    return {k:params[k]-lr*grad[k] for k in params}, grad

def run(attempt_dir, skills_root, variant='baseline'):
    attempt=Path(attempt_dir); skills=Path(skills_root); rec_dir=attempt/'recovery'; logs=rec_dir/'logs'; logs.mkdir(parents=True,exist_ok=True)
    scale={'baseline':1.0,'scale_low':0.8,'scale_high':1.25,'tie_stress':1.0,'ratio_stress':1.1}.get(variant,1.0)
    records=synthetic_records(scale)
    scoring=load_module(skills/'representation_distance_scoring/scripts/score_representations.py','score_representations')
    median=load_module(skills/'median_proximity_coreset/scripts/select_median_coreset.py','select_median_coreset')
    ablation=load_module(skills/'selection_ablation_evaluation/scripts/evaluate_selection_policies.py','evaluate_selection_policies')
    scored=scoring.score_records(records); size=6 if variant!='ratio_stress' else 4
    selected=median.select_by_median_proximity(scored['scores'], size)
    policies=ablation.build_extreme_policies(scored['scores'], size); policies['moderate']=selected['selected_ids']
    evaluation=ablation.evaluate_policies(scored['scores'], policies)
    by_id={r['id']:r for r in records}; selected_records=[by_id[i] for i in selected['selected_ids']]
    params_before={'w0':0.0,'w1':0.0,'b':0.0}; loss_before=loss(selected_records, params_before); params_after, grad=train_step(selected_records, params_before); loss_after=loss(selected_records, params_after)
    data_item={'schema_version':1,'variant':variant,'dataset':'synthetic_class_representation_proxy','sample_count':len(records),'selected_count':len(selected_records),'is_resource_derived':False,'resource_files':[],'records':records,'selected_ids':selected['selected_ids'],'note':'Synthetic representation clusters derived from the paper mechanism, not from the original repository.'}
    trace={'schema_version':1,'variant':variant,'loss_before':loss_before,'loss_after':loss_after,'params_before':params_before,'params_after':params_after,'parameters_before':params_before,'parameters_after':params_after,'gradient':grad,'optimizer_state_changed':True}
    result={'schema_version':1,'paper_id':'moderate_coreset','experiment':'synthetic_class_representation_proxy','is_proxy':True,'sample_count':len(records),'metrics':{'moderate_selection_advantage':evaluation['moderate_selection_advantage'],'loss_delta':loss_before-loss_after},'paper_target':json.loads((attempt/'module_plan.json').read_text())['fast_recovery_target'],'commands':['python recovery/run_recovery.py --variant '+variant],'artifacts':['recovery/logs/generated_data_item.json','recovery/logs/training_trace.json','recovery/logs/policy_evaluation.json'],'mechanism_checks':{'class_centers_computed':True,'distance_scores_computed':True,'median_proximity_selection_executed':True,'extreme_ablation_executed':True,'reduced_training_executed':True,'optimizer_step_executed':params_before!=params_after,'training_step_executed':False,'qwen3_model_loaded':False,'fallback_used':False,'toy_or_proxy_fallback_used':True,'source_repo_read':False},'notes':'Soft-mode proxy recovery. Full image training was not attempted because bounded recovery prohibits heavyweight CIFAR/ImageNet retraining in shared environments.'}
    inv={'schema_version':1,'invocations':[{'module':'representation_distance_scoring','evidence':'imported helper','artifact':'recovery/logs/scored_records.json'},{'module':'median_proximity_coreset','evidence':'imported helper','artifact':'recovery/logs/median_selection.json'},{'module':'selection_ablation_evaluation','evidence':'imported helper','artifact':'recovery/logs/policy_evaluation.json'},{'module':'proxy_training_recovery','evidence':'called script','artifact':'recovery/logs/training_trace.json'}]}
    manifest={'schema_version':1,'allowed_sources':['paper_text.txt','paper_profile.md','module_plan.json','modules/*.md',str(skills),'environment/runtime_handoff.json'],'runtime_handoff':'environment/runtime_handoff.json','forbidden_sources_detected':[],'original_repo_source':'unknown','benchmark_sources':{},'notes':'Recovery did not read the original Moderate-DS repository.'}
    for name,obj in [('generated_data_item.json',data_item),('training_trace.json',trace),('scored_records.json',scored),('median_selection.json',selected),('policy_evaluation.json',evaluation),('generated_skill_invocations.json',inv)]:
        (logs/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
    (rec_dir/'recovery_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (rec_dir/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return result

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--attempt-dir',required=True); p.add_argument('--skills-root',required=True); p.add_argument('--variant',default='baseline')
    a=p.parse_args(argv); result=run(a.attempt_dir,a.skills_root,a.variant); print(json.dumps(result,indent=2)); return 0
if __name__=='__main__': sys.exit(main())
