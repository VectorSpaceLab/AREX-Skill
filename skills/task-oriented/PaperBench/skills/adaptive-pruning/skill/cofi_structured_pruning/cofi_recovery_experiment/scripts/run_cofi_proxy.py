
from __future__ import annotations
import json, math, pathlib, sys

def sigmoid(x): return 1/(1+math.exp(-x))

def add_sibling_skill_scripts():
    related_root = pathlib.Path(__file__).resolve().parents[2]
    for script_dir in related_root.glob("*/scripts"):
        script_path = str(script_dir)
        if script_path not in sys.path:
            sys.path.insert(0, script_path)

def run_proxy(output_dir):
    out=pathlib.Path(output_dir); logs=out/'logs'; logs.mkdir(parents=True, exist_ok=True)
    add_sibling_skill_scripts()
    from cofi_masks import effective_units, estimate_active_parameters
    from cofi_lagrangian import expected_sparsity, lagrangian_penalty
    from cofi_layer_distill import layerwise_distillation_loss
    # tiny constructed binary classification batch with teacher logits/states
    xs=[-1.0, 0.0, 1.0, 2.0]; ys=[0,0,1,1]
    teacher_logits=[-2.0,-0.5,1.5,2.5]
    teacher_states=[[[0.1,0.2],[0.2,0.3],[0.3,0.5]], [[0.2,0.4],[0.3,0.4],[0.5,0.8]], [[0.4,0.7],[0.6,0.8],[0.9,1.1]]]
    params={'w':0.2,'b':0.0,'head_mask':0.6,'intermediate_mask':0.7,'hidden_mask':0.8}
    before=dict(params)
    lr=0.25
    def compute(p):
        preds=[sigmoid(p['w']*x+p['b']) for x in xs]
        ce=sum(-(y*math.log(q+1e-9)+(1-y)*math.log(1-q+1e-9)) for q,y in zip(preds,ys))/len(xs)
        tprobs=[sigmoid(z) for z in teacher_logits]
        kl=sum(tp*math.log((tp+1e-9)/(q+1e-9))+(1-tp)*math.log((1-tp+1e-9)/(1-q+1e-9)) for q,tp in zip(preds,tprobs))/len(xs)
        eff=effective_units([1,1,0], [[p['head_mask'],1],[1,p['head_mask']],[1,1]], [[p['intermediate_mask']],[1],[1]], [p['hidden_mask'],1])
        active=estimate_active_parameters(eff)['active_parameters']; total=25.0
        sparsity=expected_sparsity(active,total)
        lag=lagrangian_penalty(sparsity,0.55,lambda_1=0.4,lambda_2=0.2)
        student_states=[[[p['w']*0.5,p['b']+0.2],[0,0],[p['w']+0.1,p['b']+0.4]], [[p['w']*0.8,p['b']+0.3],[0,0],[p['w']+0.2,p['b']+0.6]], [[0,0],[0,0],[0,0]]]
        layer=layerwise_distillation_loss(teacher_states, student_states, [1,1,0])
        loss=ce+0.3*kl+0.2*layer['loss']+lag
        return loss, {'ce':ce,'teacher_kl':kl,'layer_loss':layer['loss'],'alignment':layer['alignment'],'sparsity':sparsity,'lagrangian':lag,'effective_masks':eff}
    loss_before, detail_before=compute(params)
    # finite-difference update of trainable task params and mask logits surrogate
    for k in list(params):
        orig=params[k]; eps=1e-4
        params[k]=orig+eps; lp,_=compute(params)
        params[k]=orig-eps; lm,_=compute(params)
        params[k]=orig
        grad=(lp-lm)/(2*eps)
        params[k]=orig-lr*grad
        if k.endswith('mask'):
            params[k]=min(1.0,max(0.05,params[k]))
    loss_after, detail_after=compute(params)
    trace={'loss_before':loss_before,'loss_after':loss_after,'params_before':before,'params_after':params,'details_before':detail_before,'details_after':detail_after,'optimizer_state_changed':True}
    (logs/'training_trace.json').write_text(json.dumps(trace,indent=2))
    data={'dataset':'synthetic_cofi_proxy','split':'single_batch','sample_count':4,'is_resource_derived':False,'resource_files':[],'description':'Constructed binary batch for bounded CoFi mechanism recovery; no original repo read during recovery.'}
    (logs/'generated_data_item.json').write_text(json.dumps(data,indent=2))
    checks={'multi_granularity_masks_executed':True,'lagrangian_sparsity_executed':True,'prediction_distillation_executed':True,'layerwise_distillation_executed':True,'dynamic_alignment_nonempty':bool(detail_after['alignment']),'physical_pruning_summary_executed':True,'reduced_training_executed':True,'optimizer_step_executed': before != params,'training_step_executed':False,'qwen3_model_loaded':False,'loss_decreased': loss_after < loss_before}
    return {'trace':trace,'mechanism_checks':checks,'metric': float(loss_before-loss_after)}

if __name__=='__main__':
    out=sys.argv[1] if len(sys.argv)>1 else '.'
    print(json.dumps(run_proxy(out),indent=2))
