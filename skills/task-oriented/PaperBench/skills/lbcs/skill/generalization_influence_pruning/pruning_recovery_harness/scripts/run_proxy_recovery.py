#!/usr/bin/env python3
import argparse, importlib.util, json, math, sys
from pathlib import Path

def load_module(path, name):
    spec=importlib.util.spec_from_file_location(name, path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def sigmoid(x): return 1/(1+math.exp(-x))
def loss(features, labels, params):
    vals=[]
    for x,y in zip(features, labels):
        p=min(max(sigmoid(sum(params[i]*x[i] for i in range(len(params)))),1e-9),1-1e-9)
        vals.append(-(y*math.log(p)+(1-y)*math.log(1-p)))
    return sum(vals)/len(vals)
def accuracy(features, labels, params):
    return sum((1 if sigmoid(sum(params[i]*x[i] for i in range(len(params))))>=0.5 else 0)==y for x,y in zip(features, labels))/len(labels)
def train_step(features, labels, params, lr):
    grad=[0.0]*len(params)
    for x,y in zip(features, labels):
        p=sigmoid(sum(params[i]*x[i] for i in range(len(params))))
        for i in range(len(params)): grad[i]+=(p-y)*x[i]/len(labels)
    return [params[i]-lr*grad[i] for i in range(len(params))]

def main():
    p=argparse.ArgumentParser(); p.add_argument('--attempt-dir', required=True); p.add_argument('--skills-root', required=True); p.add_argument('--epsilon', type=float, default=0.075)
    a=p.parse_args(); attempt=Path(a.attempt_dir); rec=attempt/'recovery'; logs=rec/'logs'; logs.mkdir(parents=True, exist_ok=True)
    plan=json.loads((attempt/'module_plan.json').read_text()); target=plan['fast_recovery_target']
    root=Path(a.skills_root)
    inf=load_module(root/'influence_vector_estimation'/'scripts'/'influence_estimator.py','inf')
    prune=load_module(root/'aggregate_influence_pruning'/'scripts'/'prune_by_influence.py','prune')
    gap=load_module(root/'generalization_gap_bound'/'scripts'/'check_gap_bound.py','gap')
    train_x=[[-2,-1],[-1,-1],[-1,0],[0,-1],[1,0],[1,1],[2,1],[2,2]]; train_y=[0,0,0,0,1,1,1,1]
    eval_x=[[-1.5,-0.5],[-0.5,-1],[1.5,0.5],[2,1.5]]; eval_y=[0,0,1,1]
    params=[0.25,0.1]
    influence=inf.estimate_influences(features=train_x, labels=train_y, params=params, damping=0.2)
    selection=prune.select_subset(influence['influences'], epsilon=a.epsilon)
    retained_x=[x for x,m in zip(train_x, selection['selected_mask']) if not m]
    retained_y=[y for y,m in zip(train_y, selection['selected_mask']) if not m]
    before_loss=loss(retained_x, retained_y, params); before_acc=accuracy(eval_x, eval_y, params)
    params_after=train_step(retained_x, retained_y, params, lr=0.5)
    after_loss=loss(retained_x, retained_y, params_after); retained_acc=accuracy(eval_x, eval_y, params_after)
    full_after=train_step(train_x, train_y, params, lr=0.5); baseline_acc=accuracy(eval_x, eval_y, full_after)
    checks={'influence_vectors_computed':True,'aggregate_optimizer_executed':True,'metric_gap_computed':True,'proxy_dataset_constructed':True,'optimizer_step_executed':params_after!=params,'reduced_training_executed':True,'full_cifar_training_executed':False,'original_repo_used':False}
    bound=gap.check_gap(target, selection['aggregate_norm'], a.epsilon, baseline_acc, retained_acc, checks, target)
    data_item={'schema_version':1,'dataset':'synthetic_binary_classification_proxy','train_samples':train_x,'train_labels':train_y,'eval_samples':eval_x,'eval_labels':eval_y,'construction':'deterministic linearly separable binary classification proxy; no original repo or external dataset used'}
    trace={'schema_version':1,'params_before':params,'params_after':params_after,'parameters_before':params,'parameters_after':params_after,'loss_before':before_loss,'loss_after':after_loss,'optimizer':'manual_logistic_gradient_descent','learning_rate':0.5,'retained_sample_count':len(retained_y)}
    inv={'schema_version':1,'invocations':[{'module':'influence_vector_estimation','skill':'influence_vector_estimation','evidence':'imported helper','kind':'imported helper','artifact':'recovery/logs/influence_vectors.json'},{'module':'aggregate_influence_pruning','skill':'aggregate_influence_pruning','evidence':'imported helper','kind':'imported helper','artifact':'recovery/logs/pruning_selection.json'},{'module':'generalization_gap_bound','skill':'generalization_gap_bound','evidence':'imported helper','kind':'imported helper','artifact':'recovery/logs/bound_check.json'},{'module':'pruning_recovery_harness','skill':'pruning_recovery_harness','evidence':'called script','kind':'called script','artifact':'recovery/recovery_result.json'}]}
    (logs/'generated_data_item.json').write_text(json.dumps(data_item, indent=2)+'\n')
    (logs/'training_trace.json').write_text(json.dumps(trace, indent=2)+'\n')
    (logs/'influence_vectors.json').write_text(json.dumps(influence, indent=2)+'\n')
    (logs/'pruning_selection.json').write_text(json.dumps(selection, indent=2)+'\n')
    (logs/'bound_check.json').write_text(json.dumps(bound, indent=2)+'\n')
    (logs/'generated_skill_invocations.json').write_text(json.dumps(inv, indent=2)+'\n')
    result={'schema_version':1,'paper_id':'generalization_influence_pruning','experiment':'synthetic_binary_classification_proxy','is_proxy':True,'sample_count':len(train_y),'metrics':{'baseline_eval_accuracy':baseline_acc,'retained_eval_accuracy':retained_acc,'retained_accuracy_gap':abs(baseline_acc-retained_acc),'aggregate_influence_norm':selection['aggregate_norm'],'pruned_fraction':selection['selected_count']/len(train_y),'loss_before':before_loss,'loss_after':after_loss},'paper_target':target,'commands':['python recovery/run_recovery.py --attempt-dir <attempt_dir> --skills-root <generated_skills_root>'],'artifacts':['recovery/logs/generated_data_item.json','recovery/logs/training_trace.json','recovery/logs/influence_vectors.json','recovery/logs/pruning_selection.json','recovery/logs/bound_check.json'],'mechanism_checks':bound['mechanism_checks'],'notes':'Soft-mode reduced proxy: full CIFAR training is blocked by bounded runtime and absent prepared dataset/model stack; proxy preserves influence-vector aggregation, constrained subset selection, and optimizer-step evidence.'}
    (rec/'recovery_result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
if __name__=='__main__': main()
